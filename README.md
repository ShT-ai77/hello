


# 任务五 · 进阶挑战 —— PySpice 电路仿真

> 选做任务 1：使用 PySpice 完成三个电路（① RC 滤波电路、② 戴维南定理验证、③ NMOS 共源极放大电路）。
>
> 每个电路均包含：**自己画的电路图**（schemdraw 绘制）、**理论值手算**（公式 + 计算过程）、**PySpice 仿真数据**、**「理论值 vs 仿真值」对比表**。

---

## 文件清单

| 文件 | 说明 |
|---|---|
| `rc_filter.py` | ① RC 低通滤波电路仿真（瞬态 + AC 扫描） |
| `thevenin.py` | ② 戴维南定理验证仿真（4 次仿真） |
| `mos_amplifier.py` | ③ NMOS 共源极放大电路仿真（OP + 瞬态） |
| `draw_circuits.py` | 用 schemdraw 绘制全部电路图 |
| `images/` | 电路图与仿真波形图 |

运行方式：

```bash
pip install PySpice matplotlib schemdraw
pyspice-post-installation --install-ngspice-dll   # 安装 ngspice 引擎
python rc_filter.py
python thevenin.py
python mos_amplifier.py
```

---

## ① RC 低通滤波电路

### 电路图

![RC 电路](images/circuit_rc.png)

元件取值：**R = 1 kΩ，C = 1 µF**；输入 1V 方波（100Hz）做瞬态仿真，AC 扫描 1Hz~1MHz 测波特图。

### 理论值手算

- 时间常数：

$$\tau = RC = 1\times10^3 \times 1\times10^{-6} = 1\ \text{ms}$$

- 截止频率（-3dB）：

$$f_c = \frac{1}{2\pi RC} = \frac{1}{2\pi \times 10^3 \times 10^{-6}} \approx 159.15\ \text{Hz}$$

- 截止频率处增益 $|H(f_c)| = 1/\sqrt{2} \approx 0.707$（即 -3dB）。

### 仿真数据

- 瞬态：方波激励下输出呈指数充放电曲线，输出上升到稳态 63.2% 用时 ≈ 0.997 ms；
- AC 扫描：增益在 159.15 Hz 处降为 0.705（≈ -3.05 dB），此后按 -20 dB/dec 滚降。

![RC 瞬态波形](images/rc_transient.png)

![RC 波特图](images/rc_bode.png)

### 对比表

| 量 | 理论值（手算） | 仿真值（PySpice） | 误差 |
|---|---|---|---|
| 时间常数 τ | 1.000 ms | 0.997 ms | -0.32% |
| 截止频率 fc | 159.15 Hz | 159.15 Hz | ≈ 0% |
| fc 处增益 | 0.707 | 0.705 | -0.28% |

**结论**：τ 与 fc 的手算与仿真高度吻合，验证了一阶 RC 低通的 $\tau = RC$、$f_c = 1/(2\pi RC)$。

---

## ② 戴维南定理验证

### 电路图（含源二端网络，标注端口 a-b）

![戴维南原网络](images/circuit_thevenin.png)

元件取值：**V1 = 10V，R1 = 1 kΩ（串联），R2 = 2.2 kΩ（端口上并联）**，负载 **RL = 1 kΩ**。

### 理论值手算

- 开路电压（R1、R2 分压）：

$$V_{th} = V_1\cdot\frac{R_2}{R_1+R_2} = 10\times\frac{2.2}{1+2.2} = 6.875\ \text{V}$$

- 等效电阻（电压源置零，R1∥R2）：

$$R_{th} = R_1 \| R_2 = \frac{1\times2.2}{1+2.2} = 687.5\ \Omega$$

- 短路电流：

$$I_{sc} = \frac{V_{th}}{R_{th}} = \frac{6.875}{687.5} = 10\ \text{mA}$$

- 接负载 RL = 1 kΩ 后：

$$V_L = V_{th}\cdot\frac{R_L}{R_{th}+R_L} = 6.875\times\frac{1}{1.6875} \approx 4.074\ \text{V},\quad I_L \approx 4.074\ \text{mA}$$

### 仿真数据

仿真 1（端口开路）：V_oc = 6.8750 V；仿真 2（端口短路，0V 电流表）：I_sc = 10.000 mA。
仿真 3（原网络接 RL）与仿真 4（戴维南等效电路 V_th 串 R_th 接同一 RL）：

![戴维南等效电路](images/circuit_thevenin_eq.png)

### 对比表

| 量 | 理论值（手算） | 仿真值（PySpice） | 误差 |
|---|---|---|---|
| 开路电压 V_oc（= V_th） | 6.8750 V | 6.8750 V | 0.00% |
| 短路电流 I_sc | 10.000 mA | 10.000 mA | 0.00% |
| 等效电阻 R_th = V_oc/I_sc | 687.5 Ω | 687.5 Ω | 0.00% |

**等效替换后接负载验证表（RL = 1 kΩ）**

| 量 | 原网络（仿真） | 等效电路（仿真） | 理论值 | 偏差 |
|---|---|---|---|---|
| 负载电压 V_L | 4.0741 V | 4.0741 V | 4.0741 V | 0.000000 V |
| 负载电流 I_L | 4.0741 mA | 4.0741 mA | 4.0741 mA | 0.000000 mA |

**结论**：原网络与「V_th 串 R_th」等效电路在接同一负载时端口电压、电流完全一致，戴维南定理验证通过。

---

## ③ NMOS 共源极放大电路（题面固定参数）

### 电路图（按题图绘制）

![NMOS 共源放大电路](images/circuit_nmos.png)

给定参数：**VDD = 5V，Rg1 = 60 kΩ，Rg2 = 40 kΩ，Rd = 2 kΩ，Cb1 足够大**；
NMOS：**K = 0.8 mA/V²，V_th = 1V，λ = 0.02 /V**；输入 **vi = 10mV @ 1kHz 正弦波**。

> SPICE 说明：SPICE level-1 模型 $I_D = \frac{KP}{2}\frac{W}{L}(V_{GS}-V_{th})^2(1+\lambda V_{DS})$，
> 取 W/L = 1、KP = 0.8 mA/V² 即对应题面 K = 0.8 mA/V²。

### 手算静态工作点

栅极电位（Rg1、Rg2 分压，栅极电流为 0）：

$$V_{GS} = V_{DD}\cdot\frac{R_{g2}}{R_{g1}+R_{g2}} = 5\times\frac{40}{60+40} = 2\ \text{V}$$

不计 λ 时：

$$I_D = \frac{K}{2}(V_{GS}-V_{th})^2 = \frac{0.8}{2}\times(2-1)^2 = 0.4\ \text{mA}$$

$$V_{DS} = V_{DD} - I_D R_d = 5 - 0.4\times2 = 4.2\ \text{V}$$

计入 λ = 0.02/V 自洽求解（$I_D = \frac{K}{2}(V_{GS}-V_{th})^2(1+\lambda V_{DS})$，$V_{DS}=V_{DD}-I_D R_d$）：

$$I_D = \frac{a(1+\lambda V_{DD})}{1+a\lambda R_d} = 0.4331\ \text{mA},\qquad V_{DS} = 4.134\ \text{V},\quad a=\tfrac{K}{2}(V_{GS}-V_{th})^2$$

**饱和区判断**：$V_{DS} = 4.13\ \text{V} > V_{GS} - V_{th} = 1\ \text{V}$ → **工作在饱和区 ✓**

### 手算小信号

跨导：

$$g_m = K(V_{GS}-V_{th})(1+\lambda V_{DS}) = 0.8\text{m}\times1\times1.0827 \approx 0.866\ \text{mS}$$

输出电阻（沟道长度调制）：

$$r_o = \frac{1}{\lambda I_D} \approx 115.5\ \text{kΩ}$$

电压增益：

$$A_v = -g_m\,(R_d \| r_o) = -0.866\text{m}\times1.966\text{k} \approx -1.70$$

### 仿真验证（PySpice）

**直流 OP 对比表**

| 量 | 理论值（手算，含 λ） | 仿真值（OP） | 误差 |
|---|---|---|---|
| V_GS | 2.0000 V | 2.0000 V | 0.00% |
| I_D | 0.4331 mA | 0.4331 mA | 0.00% |
| V_DS | 4.1339 V | 4.1339 V | -0.00% |
| 饱和区判断 | V_DS > 1V，饱和 ✓ | V_DS = 4.134 V > 1V，饱和 ✓ | — |

**小信号增益对比表**（vi = 10mV @ 1kHz 瞬态仿真）

| 量 | 理论值（手算） | 仿真值（实测） | 相对偏差 |
|---|---|---|---|
| 输入幅度 v_i | 10 mV | 10.000 mV | — |
| 输出幅度 v_o | 17.03 mV | 17.050 mV | — |
| 增益 A_v | -1.7028 | -1.7050 | 0.13% |

**输入/输出波形图（反相放大）**：

![MOS 波形](images/mos_waveform.png)

**结论**：OP 工作点与手算完全一致；输出与输入反相、幅度放大约 1.70 倍，与 $A_v=-g_m(R_d\|r_o)$ 手算值吻合，验证了共源极反相放大特性。

---

## 总结

| 电路 | 关键指标 | 理论 vs 仿真 |
|---|---|---|
| ① RC 低通 | τ、fc | 误差 < 0.35% |
| ② 戴维南 | V_oc、I_sc、R_th、带载 V/I | 误差 0%，等效替换外特性完全一致 |
| ③ NMOS 共源 | V_GS、I_D、V_DS、gm、A_v | OP 误差 ≈ 0%，增益偏差 0.13%，反相 ✓ |
