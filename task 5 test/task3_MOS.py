# -*- coding: utf-8 -*-
# =====================================================================
# 考核任务③：NMOS 共源级放大电路（PySpice 仿真）—— 参数按题卡固定，不做修改
# ---------------------------------------------------------------------
# 固定参数：VDD=5V, Rg1=60kΩ, Rg2=40kΩ, Rd=2kΩ, Cb1 视为足够大(取100µF)
#          NMOS：K=0.8mA/V², V_th=1V, λ=0.02/V；输入 Vi=10mV/1kHz 正弦波
# 电路连接：VDD -> Rd -> 漏极 d（输出 vO）；VDD -> Rg1 -> 栅极 g；栅极 g -> Rg2 -> 地；
#          输入 Vi -> Cb1 -> 栅极 g（隔直耦合）；源极 s 接地，衬底 B 接源极（共源组态）
# 手算静态工作点（直流通路：Cb1 断开、电容开路）：
#   分压公式：V_G = VDD × Rg2/(Rg1+Rg2) = 5 × 40k/100k = 2 V（栅极无电流，分压不带载）
#   V_GS = V_G - V_S = 2 - 0 = 2 V（源极接地）
#   饱和区电流公式：I_D = K(V_GS - V_th)² = 0.8m × (2-1)² = 0.8 mA
#   输出回路 KVL：V_DS = VDD - I_D·Rd = 5 - 0.8m×2k = 3.4 V
#   饱和区判断：V_DS(3.4V) > V_GS - V_th(1V) ✔ 工作在饱和区（放大区）
# 手算小信号（微变等效电路）：
#   跨导公式：gm = 2K(V_GS - V_th) = 2 × 0.8m × 1 = 1.6 mS
#   增益公式（忽略 λ）：Av = -gm·Rd = -1.6m × 2k = -3.2（负号=反相放大）
#   （若计 λ：ro = 1/(λ·I_D) = 62.5kΩ，Av = -gm·(Rd∥ro) ≈ -3.10，与仿真更接近）
# 运行输出：task3_transient.png（输入/输出波形）、task3_bode.png（幅频特性）+ 控制台数据摘要
# =====================================================================

import numpy as np                             # 导入 numpy：数值计算库
import matplotlib.pyplot as plt                # 导入 matplotlib：绘图库
from PySpice.Spice.Netlist import Circuit      # 导入 Circuit 类：搭建 SPICE 网表
from PySpice.Unit import *                     # 导入单位系统：直接用 kΩ、mV 等物理单位

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']  # 设置中文字体防止乱码
plt.rcParams['axes.unicode_minus'] = False                       # 修复负号显示问题

# ---------------- 1. 电路参数（题卡固定，绝对不改） ----------------
VDD = 5.0                                      # 电源电压 VDD = 5 V（题卡固定）
RG1 = 60e3                                     # 上分压电阻 Rg1 = 60 kΩ（题卡固定）
RG2 = 40e3                                     # 下分压电阻 Rg2 = 40 kΩ（题卡固定）
RD = 2e3                                       # 漏极电阻 Rd = 2 kΩ（题卡固定）
CB1 = 100e-6                                   # 耦合电容 Cb1 = 100 µF（题卡"足够大"，取大值近似短路）
K = 0.8e-3                                     # MOS 工艺参数 K = 0.8 mA/V²（题卡固定，饱和区 I_D=K(V_GS-V_th)²）
VTH = 1.0                                      # 开启电压 V_th = 1 V（题卡固定）
LAMBDA = 0.02                                  # 沟道长度调制系数 λ = 0.02 /V（题卡固定，影响输出电阻 ro）
VI_AMP = 0.01                                  # 输入正弦幅度 Vi = 10 mV（小信号，题卡固定）
VI_FREQ = 1e3                                  # 输入正弦频率 f = 1 kHz（题卡固定）

# 手算理论值（供对比，忽略 λ 的手算口径）
vgs_th = VDD * RG2 / (RG1 + RG2)               # 分压公式：V_GS = VDD·Rg2/(Rg1+Rg2) = 2 V
id_th = K * (vgs_th - VTH) ** 2                # 饱和区电流公式：I_D = K(V_GS-V_th)² = 0.8 mA
vds_th = VDD - id_th * RD                      # 输出回路 KVL：V_DS = VDD - I_D·Rd = 3.4 V
gm_th = 2 * K * (vgs_th - VTH)                 # 跨导公式：gm = 2K(V_GS-V_th) = 1.6 mS
av_th = -gm_th * RD                            # 增益公式：Av = -gm·Rd = -3.2（忽略 λ 的手算值）

# ---------------- 2. 搭建共源放大电路网表 ----------------
circuit = Circuit('NMOS 共源放大电路')          # 创建网表对象
# MOS 模型卡：SPICE level-1 模型中 I_D = (KP/2)·(W/L)·(V_GS-V_to)²·(1+λ·V_DS)，
# 故取 KP = 2K = 1.6mA/V² 且 W/L=1（SPICE 默认 W=L=100µm），即可等效题卡的 K=0.8mA/V²
circuit.model('NMOS_K', 'nmos', level=1, vto=VTH, kp=2 * K, **{'lambda': LAMBDA})  # vto=开启电压, kp=2K, lambda=沟道长度调制
circuit.V('dd', 'vdd', circuit.gnd, VDD @ u_V)                       # 电源 VDD：5V 接在 vdd 节点与地之间
circuit.R('g1', 'vdd', 'gate', RG1 @ u_Ohm)                          # Rg1：从 VDD 到栅极（上分压电阻）
circuit.R('g2', 'gate', circuit.gnd, RG2 @ u_Ohm)                    # Rg2：从栅极到地（下分压电阻）
circuit.R('d', 'vdd', 'drain', RD @ u_Ohm)                           # Rd：从 VDD 到漏极（把电流变化转为电压变化）
circuit.C('b1', 'vin', 'gate', CB1 @ u_F)                             # 耦合电容 Cb1：输入经它隔直后耦合到栅极（"通交流、阻直流"），节点名用 vin
# 输入源：SIN(直流偏置 幅度 频率) = 10mV/1kHz 正弦；末尾 "AC 1" 表示交流小信号分析时输入置 1，输出即增益
circuit.V('in', 'vin', circuit.gnd, 'SIN(0 10m 1k) AC 1')             # 节点名用 vin（in 是 Python 关键字，PySpice 会警告）
circuit.M('1', 'drain', 'gate', circuit.gnd, circuit.gnd, model='NMOS_K')  # NMOS：漏极/栅极/源极/衬底；源极接地、衬底接源极（共源组态）

simulator = circuit.simulator(temperature=25, nominal_temperature=25)  # 创建仿真器（ngspice 求解）

# ---------------- 3. 直流工作点分析（OP）：验证手算静态工作点 ----------------
op = simulator.operating_point()               # 直流工作点分析：电容开路、电感短路，即"直流通路"
v_gs_sim = float(op['gate'][0])                # V_GS = 栅极电位（源极接地，V_S=0；栅极无电流故等于分压值）
v_ds_sim = float(op['drain'][0])               # V_DS = 漏极电位（源极接地）
i_d_sim = (VDD - v_ds_sim) / RD                # 漏极节点 KCL：I_D = (VDD - V_DS)/Rd（Rd 上压降除以电阻）
vov_sim = v_gs_sim - VTH                       # 过驱动电压公式：V_OV = V_GS - V_th
sat_ok = v_ds_sim > vov_sim                    # 饱和区判断条件：V_DS > V_GS - V_th（漏端沟道夹断）
ro_sim = 1 / (LAMBDA * i_d_sim)                # 输出电阻公式：ro = 1/(λ·I_D)（计及沟道长度调制效应）

# ---------------- 4. 瞬态分析：看输入/输出波形（反相放大），测实际增益 ----------------
tran = simulator.transient(step_time=1 @ u_us, end_time=5 @ u_ms)   # 瞬态分析：步长 1µs，共 5ms（5 个信号周期）
t = np.array(tran.time)                        # 时间轴数组
v_in_t = np.array(tran['vin'])                  # 输入电压波形 v_i(t)（10mV 正弦），节点名 vin
v_out_t = np.array(tran['drain'])              # 输出电压波形 v_o(t)（漏极电位）

steady = t >= 3e-3                             # 取 3ms 之后（已到稳态，避开起振阶段）
vin_s, vout_s = v_in_t[steady], v_out_t[steady]           # 稳态段的输入与输出波形
ts = t[steady]                                 # 稳态段对应的时间轴
amp_in = (vin_s.max() - vin_s.min()) / 2       # 峰峰值折半 = 输入幅度（≈10mV）
amp_out = (vout_s.max() - vout_s.min()) / 2    # 峰峰值折半 = 输出幅度（≈30mV）
i_pk = int(np.argmax(vin_s))                   # 找输入正峰时刻
inverted = vout_s[i_pk] < vout_s.mean()        # 输入为正峰时输出低于均值 → 输出反相（共源放大特性）
av_tran = -(amp_out / amp_in) if inverted else (amp_out / amp_in)  # 增益公式：Av = v_o/v_i（反相取负号）
# 由仿真增益反推跨导：|Av| = gm·(Rd∥ro)，并联公式 Rd∥ro = Rd·ro/(Rd+ro)
gm_sim = abs(av_tran) / (RD * ro_sim / (RD + ro_sim))      # 跨导反推公式：gm = |Av|/(Rd∥ro)

# 画瞬态波形图（上下两个子图，突出反相关系）并保存
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 6.5), sharex=True)  # 2 行 1 列共享 x 轴
ax1.plot(t * 1e3, v_in_t * 1e3, 'b-', lw=1.8)  # 输入波形（纵轴换算成 mV）
ax1.set_ylabel('v_i (mV)')                     # y 轴标签
ax1.set_title('任务③ 共源放大：输入 10mV/1kHz（上）与输出（下）—— 输出反相且放大')  # 标题
ax1.grid(alpha=0.3)                            # 网格
ax2.plot(t * 1e3, v_out_t, 'r-', lw=1.8)       # 输出波形（画完整 5ms，稳态后幅度用于测增益）
ax2.axhline(v_ds_sim, color='gray', ls='--', lw=1, label='静态 V_DS=%.3f V' % v_ds_sim)  # 标静态工作点电平
ax2.set_xlabel('时间 t (ms)')                  # x 轴标签
ax2.set_ylabel('v_o (V)')                      # y 轴标签
ax2.legend()                                   # 图例
ax2.grid(alpha=0.3)                            # 网格
plt.tight_layout()                             # 调整布局
plt.savefig('task3_transient.png', dpi=150)    # 保存瞬态波形 png

# ---------------- 5. 交流小信号分析：测 1kHz 增益并画幅频特性 ----------------
# 【重要】交流小信号分析的物理约定：
#   —— 此处直流电源接地：交流分析中 SPICE 自动把 VDD 直流源置零（交流接地），电路在静态工作点附近线性化；
#   —— 此处电容视为短路：Cb1 足够大，容抗 X_C=1/(2πfC) 在 1kHz 时≈0.3Ω，近似短路（耦合电容"通交流"）
# 微变等效模型：栅极=电压控制电流源 gm·v_gs（栅极输入阻抗无穷大），漏极经 ro 与 Rd 并联到交流地
ac = simulator.ac(variation='dec', number_of_points=20,             # 交流扫频：每十倍频 20 点
                  start_frequency=10 @ u_Hz, stop_frequency=100 @ u_MHz)  # 范围 10Hz~100MHz
freq = np.array(ac.frequency)                  # 频率数组
gain_ac = np.abs(np.array(ac['drain']))        # 输出幅度（输入 AC=1，故该值即电压增益 |Av|）
idx1k = int(np.argmin(np.abs(freq - VI_FREQ))) # 找最接近 1kHz 的扫频点
av_ac = float(gain_ac[idx1k])                  # 1kHz 处仿真增益（计及 λ 的微变等效模型值）

plt.figure(figsize=(9, 5))                     # 新建画布
plt.semilogx(freq, 20 * np.log10(gain_ac), 'b-', lw=2)                     # 幅频特性（dB）
plt.axhline(20 * np.log10(av_ac), color='gray', ls=':', lw=1,             # 标出 1kHz 处增益水平线
            label='1kHz 增益 ≈ %.2f（%.1f dB）' % (av_ac, 20 * np.log10(av_ac)))
plt.xlabel('频率 f (Hz)')                      # x 轴标签
plt.ylabel('增益 |Av| (dB)')                   # y 轴标签
plt.title('任务③ 共源放大幅频特性：中频 Av = -gm·(Rd∥ro) ≈ %.2f（反相）' % av_ac)   # 标题
plt.legend()                                   # 图例
plt.grid(alpha=0.3, which='both')              # 主次网格
plt.tight_layout()                             # 调整布局
plt.savefig('task3_bode.png', dpi=150)         # 保存幅频特性 png

# ---------------- 6. 打印数据摘要：手算 vs 仿真 对比表 ----------------
print('=' * 66)                                # 分隔线
print('任务③ NMOS 共源放大 —— 手算 vs 仿真 数据摘要（题卡固定参数）')       # 表标题
print('=' * 66)                                # 分隔线
print('静态工作点')                            # 小节标题
print('  V_GS：手算 %.4f V，仿真 %.4f V（栅极无电流，分压公式 V_G=VDD·Rg2/(Rg1+Rg2)）' % (vgs_th, v_gs_sim))  # V_GS 对比
print('  I_D ：手算 %.4f mA，仿真 %.4f mA（仿真偏大因含沟道长度调制 I_D=K(V_OV)²(1+λV_DS)）' % (id_th * 1e3, i_d_sim * 1e3))  # I_D 对比
print('  V_DS：手算 %.4f V，仿真 %.4f V（输出回路 KVL：V_DS=VDD-I_D·Rd）' % (vds_th, v_ds_sim))  # V_DS 对比
print('  饱和区判断：V_DS=%.3f V %s V_GS-V_th=%.3f V → %s' %
      (v_ds_sim, '>' if sat_ok else '<=', vov_sim, '工作在饱和区 ✔' if sat_ok else '未饱和 ✘'))  # 饱和判断
print('-' * 66)                                # 分隔线
print('小信号参数')                            # 小节标题
print('  gm ：手算 %.4f mS，仿真 %.4f mS（跨导公式 gm=2K(V_GS-V_th)；仿真值由 |Av|/(Rd∥ro) 反推）' %
      (gm_th * 1e3, gm_sim * 1e3))              # 跨导对比
print('  ro ：计 λ 理论 %.2f kΩ（ro=1/(λ·I_D)，忽略 λ 时 ro→∞）' % (ro_sim / 1e3))  # 输出电阻
print('  Av ：手算(忽略λ) %.3f，手算(计λ) %.3f，瞬态仿真 %.3f，交流仿真 %.3f' %
      (av_th, -gm_th * (RD * ro_sim / (RD + ro_sim)), av_tran, -av_ac))           # 增益四方对比
print('-' * 66)                                # 分隔线
print('波形：输出幅度 %.2f mV / 输入 %.2f mV，输出与输入反相（共源放大"反相器"特性）' %
      (amp_out * 1e3, amp_in * 1e3))            # 波形测量结论

plt.show()                                     # 弹出图窗（已先保存 png）
