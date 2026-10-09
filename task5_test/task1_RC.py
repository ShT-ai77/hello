# -*- coding: utf-8 -*-
# =====================================================================
# 考核任务①：RC 低通滤波电路（PySpice 仿真）
# ---------------------------------------------------------------------
# 电路连接：方波信号源 Vi -> 电阻 R(1kΩ) -> 输出节点 out -> 电容 C(100nF) -> 地
# 手算理论值：
#   时间常数公式：τ = R × C = 1kΩ × 100nF = 0.1 ms
#   截止频率公式：fc = 1 / (2πRC) = 1/(2π×1e3×100e-9) ≈ 1591.5 Hz
#   传递函数：H(jω) = 1/(1 + jωRC)，幅频 |H| = 1/√(1+(f/fc)²)，相频 φ = -arctan(f/fc)
# 运行输出：task1_transient.png（方波瞬态波形）、task1_bode.png（波特图）、控制台数据摘要
# =====================================================================

import numpy as np                          # 数值计算库，用于数组运算、对数与插值
import matplotlib.pyplot as plt                # 导入 matplotlib：绘图库，用于画波形图和波特图
from PySpice.Spice.Netlist import Circuit      # 导入 Circuit 类：用 Python 搭建 SPICE 网表（即"连电路"）
from PySpice.Unit import *                     # 导入单位系统：可直接写 kΩ、µF、ms 等带物理单位的数值

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']  # 设置中文字体，防止图中中文标签乱码
plt.rcParams['axes.unicode_minus'] = False                       # 修复中文坐标系下负号显示为方块的问题

# 【开关】是否生成/保存波形图：False=只打印数据摘要（运行后不留图）；True=生成 png 并弹窗查看
SAVE_FIG = False

# ---------------- 1. 电路参数（任务书规定①②电路参数自定） ----------------
R = 1e3                                        # 电阻 R = 1 kΩ（单位：Ω），与电容串联起分压/限流作用
C = 100e-9                                     # 电容 C = 100 nF（单位：F），储能元件决定充放电快慢
tau_theory = R * C                             # 时间常数公式：τ = R×C = 1e3 × 100e-9 = 1e-4 s = 0.1 ms
fc_theory = 1 / (2 * np.pi * R * C)            # 截止频率公式：fc = 1/(2πRC) ≈ 1591.5 Hz（增益下降 3dB 处）

# ---------------- 2. 搭建 RC 电路网表 ----------------
circuit = Circuit('RC 低通滤波电路')            # 创建网表对象，相当于给电路命名
# 输入源：PULSE(初值 终值 延迟 上升时间 下降时间 脉宽 周期) = 0→1V、1kHz 方波；
# 末尾的 "AC 1" 表示：交流小信号分析时输入幅度置 1，这样交流输出幅度就等于增益本身
circuit.V('in', 'vin', circuit.gnd, 'PULSE(0 1 0 1n 1n 0.5m 1m) AC 1')   # 节点名用 vin（不用 in，因 in 是 Python 关键字）
circuit.R(1, 'vin', 'out', R @ u_Ohm)           # 电阻 R1 接在输入节点 vin 与输出节点 out 之间，满足欧姆定律 V=IR
circuit.C(1, 'out', circuit.gnd, C @ u_F)      # 电容 C1 接在输出节点 out 与地之间，满足电容伏安关系 i=C·dv/dt

simulator = circuit.simulator(temperature=25, nominal_temperature=25)  # 创建仿真器（底层调用 ngspice 求解基尔霍夫方程组）

# ---------------- 3. 瞬态分析：看方波充放电波形，测时间常数 τ ----------------
analysis = simulator.transient(step_time=1 @ u_us, end_time=3 @ u_ms)   # 瞬态分析：步长 1µs，共仿真 3ms（3 个方波周期）
time = np.array(analysis.time)                 # 提取时间轴数组（单位：秒）
v_in = np.array(analysis['vin'])                # 提取输入电压波形 v_in(t)（方波），节点名 vin
v_out = np.array(analysis['out'])              # 提取输出电压波形 v_out(t)（电容上的电压，按指数规律充放电）

idx63 = int(np.argmax(v_out >= 0.632))         # 找输出第一次充到终值 63.2% 的时刻：一阶电路定义 t=τ 时 v=0.632×V_final
tau_sim = time[idx63]                          # 仿真测得的时间常数 τ_sim（输入在 t=0 上跳，故该时刻数值即 τ）

# 画瞬态波形图并保存
plt.figure(figsize=(9, 5))                     # 新建画布，尺寸 9×5 英寸
plt.plot(time * 1e3, v_in, 'b--', lw=1.5, label='输入 v_in（方波 1kHz）')     # 画输入方波（蓝色虚线），时间换算成 ms
plt.plot(time * 1e3, v_out, 'r-', lw=2, label='输出 v_out（电容电压）')       # 画输出波形（红色实线），即电容充放电曲线
plt.axhline(0.632, color='gray', ls=':', lw=1)                               # 画 63.2% 终值参考线（τ 的定义位置）
plt.axvline(tau_sim * 1e3, color='green', ls=':', lw=1,                      # 画出仿真测得的 τ 竖线
            label='τ_sim ≈ %.3f ms（理论 %.3f ms）' % (tau_sim * 1e3, tau_theory * 1e3))
plt.xlabel('时间 t (ms)')                      # x 轴标签：时间
plt.ylabel('电压 (V)')                         # y 轴标签：电压
plt.title('任务① RC 低通滤波：方波瞬态响应（τ=RC=0.1ms）')                   # 图标题
plt.legend(loc='lower right')                  # 显示图例
plt.grid(alpha=0.3)                            # 加半透明网格便于读数
plt.tight_layout()                             # 自动调整边距
if SAVE_FIG: plt.savefig('task1_transient.png', dpi=150)    # 【开关控制】SAVE_FIG=True 时才保存瞬态波形图为 png 文件

# ---------------- 4. 交流小信号分析：扫频画波特图，测截止频率 fc ----------------
# 【重要】交流小信号分析的物理约定：
#   —— 此处直流电源接地：交流分析中 SPICE 自动把直流源（无直流输入源）置零，电路在直流工作点附近线性化；
#   —— 此处电容视为短路：容抗公式 X_C = 1/(2πfC)，频率足够高时 X_C→0，电容近似短路（低通通带内阻抗很小）
ac = simulator.ac(variation='dec', number_of_points=200,                  # 交流扫频：每十倍频 200 个点
                  start_frequency=10 @ u_Hz, stop_frequency=1 @ u_MHz)    # 扫频范围 10Hz ~ 1MHz（对数扫频）
freq = np.array(ac.frequency)                  # 频率数组（单位：Hz）
v_ac = np.array(ac['out'])                     # 输出节点复数电压相量（输入 AC=1，故 |v_ac| 即增益 |H(jf)|）
gain_db = 20 * np.log10(np.abs(v_ac))          # 增益公式：Av(dB) = 20·log10(|v_out/v_in|) = 20·log10|H(jf)|
phase_deg = np.angle(v_ac, deg=True)           # 相频特性 φ(f)，一阶低通理论值 φ = -arctan(f/fc)，高频趋近 -90°

# 用插值法求仿真截止频率：增益首次跌到 -3.0103dB（即 |H| = 1/√2 ≈ 0.707）处
target = -3.0103                               # -3dB 对应的精确分贝值：20·log10(1/√2)
k = int(np.argmax(gain_db < target))           # 找到第一个低于 -3dB 的数组下标
f1, f2 = freq[k - 1], freq[k]                  # 截止频率必夹在相邻两点 f1、f2 之间
g1, g2 = gain_db[k - 1], gain_db[k]            # 对应两点的增益值
fc_sim = np.exp(np.log(f1) + (target - g1) * (np.log(f2) - np.log(f1)) / (g2 - g1))  # 在 ln(f)—dB 空间线性插值求 fc_sim

idx1k = int(np.argmin(np.abs(freq - 1e3)))     # 找最接近 1kHz 的扫频点（方波基波频率处的增益）
gain_1k = float(np.abs(v_ac[idx1k]))           # 1kHz 处增益理论值 1/√(1+(1000/1591.5)²) ≈ 0.847

# 画波特图（幅频 + 相频两个子图）并保存
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 7), sharex=True)           # 建 2 行 1 列共享 x 轴的子图
ax1.semilogx(freq, gain_db, 'b-', lw=2)        # 上子图：横轴对数频率，画幅频特性曲线
ax1.axvline(fc_theory, color='red', ls='--', lw=1, label='理论 fc=%.1f Hz' % fc_theory)      # 标理论截止频率竖线
ax1.axhline(-3.0103, color='gray', ls=':', lw=1, label='-3dB 线')            # 标 -3dB 水平参考线
ax1.set_ylabel('增益 |H| (dB)')                # 上子图 y 轴标签
ax1.set_title('任务① RC 低通波特图：fc = 1/(2πRC) ≈ %.1f Hz（仿真 %.1f Hz）' % (fc_theory, fc_sim))  # 标题含手算与仿真对比
ax1.legend(loc='lower left')                   # 图例
ax1.grid(alpha=0.3, which='both')              # 主次网格都显示（对数轴需要）
ax2.semilogx(freq, phase_deg, 'g-', lw=2)      # 下子图：相频特性曲线
ax2.axvline(fc_theory, color='red', ls='--', lw=1)                          # 相频图上也标出 fc
ax2.set_xlabel('频率 f (Hz)')                  # 下子图 x 轴标签
ax2.set_ylabel('相位 φ (°)')                   # 下子图 y 轴标签
ax2.grid(alpha=0.3, which='both')              # 网格
plt.tight_layout()                             # 调整布局
if SAVE_FIG: plt.savefig('task1_bode.png', dpi=150)         # 【开关控制】SAVE_FIG=True 时才保存波特图为 png 文件

# ---------------- 5. 打印数据摘要：手算 vs 仿真 对比表 ----------------
print('=' * 62)                                # 分隔线
print('任务① RC 低通滤波 —— 手算 vs 仿真 数据摘要')                          # 表标题
print('=' * 62)                                # 分隔线
print('参数          手算理论值        仿真值          相对误差')             # 表头
print('-' * 62)                                # 分隔线
print('τ  时间常数   %-12.4f ms   %-12.4f ms   %.2f%%' %                   # 时间常数对比行
      (tau_theory * 1e3, tau_sim * 1e3, abs(tau_sim - tau_theory) / tau_theory * 100))
print('fc 截止频率   %-12.1f Hz    %-12.1f Hz    %.2f%%' %                 # 截止频率对比行
      (fc_theory, fc_sim, abs(fc_sim - fc_theory) / fc_theory * 100))
print('增益@1kHz    %-12.4f      %-12.4f      %.2f%%' %                    # 1kHz 处增益对比行：1/√(1+(f/fc)²)
      (1 / np.sqrt(1 + (1e3 / fc_theory) ** 2), gain_1k,
       abs(gain_1k - 1 / np.sqrt(1 + (1e3 / fc_theory) ** 2)) / (1 / np.sqrt(1 + (1e3 / fc_theory) ** 2)) * 100))
print('-' * 62)                                # 分隔线
print('结论：输出幅度在 fc 以上按 -20dB/十倍频 滚降，符合一阶低通传递函数 H(jω)=1/(1+jωRC)')  # 结论

if SAVE_FIG: plt.show()                                     # 【开关控制】SAVE_FIG=True 时才弹出图窗
