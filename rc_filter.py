# -*- coding: utf-8 -*-
"""
任务五 - ① RC 低通滤波电路（PySpice 仿真）
参数：R = 1 kOhm, C = 1 uF
理论值：tau = RC = 1 ms，fc = 1/(2*pi*RC) ≈ 159.15 Hz
仿真内容：
  1) 方波输入的瞬态响应（测时间常数 tau）
  2) AC 频率扫描（幅频/相频波特图，测 -3dB 截止频率 fc）
"""
import os
import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images")
os.makedirs(OUT_DIR, exist_ok=True)

# ---------------- 参数 ----------------
R = 1.0e3      # 1 kOhm
C = 1.0e-6     # 1 uF
tau_theory = R * C                  # 1 ms
fc_theory = 1.0 / (2 * np.pi * R * C)  # ~159.15 Hz

# ---------------- 电路 ----------------
circuit = Circuit("RC Low-pass Filter")
circuit.PulseVoltageSource(
    "vin", "vin", "0",
    initial_value=0 @ u_V, pulsed_value=1 @ u_V,
    pulse_width=5 @ u_ms, period=10 @ u_ms,       # 100 Hz 方波
    rise_time=1 @ u_ns, fall_time=1 @ u_ns,
)
circuit.R(1, "vin", "out", R @ u_Ohm)
circuit.C(1, "out", "0", C @ u_F)

# ---------------- 瞬态仿真：方波响应 ----------------
simulator = circuit.simulator(temperature=25, nominal_temperature=25)
transient = simulator.transient(step_time=10 @ u_us, end_time=25 @ u_ms)
t = np.array(transient.time) * 1e3          # ms
vin = np.array(transient["vin"])
vout = np.array(transient["out"])

# 实测时间常数：取第一个上升沿，输出上升到 0 -> 63.2% 所需时间
mask = (t >= 0.0) & (t <= 3.0)              # 第一个上升沿（t=0 起）
t_edge = t[mask]
v_edge = vout[mask]
v_final = vout[(t >= 4.0) & (t <= 5.0)].max()   # 稳态值（充电完成段）
idx = np.argmax(v_edge >= 0.632 * v_final)
tau_sim = (t_edge[idx] - t_edge[0]) * 1e-3  # 换算回秒

# ---------------- AC 仿真：波特图 ----------------
ac_circuit = Circuit("RC Low-pass Filter AC")
ac_circuit.SinusoidalVoltageSource(
    "vin", "vin", "0", amplitude=1 @ u_V, frequency=1 @ u_kHz, ac_magnitude=1 @ u_V
)
ac_circuit.R(1, "vin", "out", R @ u_Ohm)
ac_circuit.C(1, "out", "0", C @ u_F)
ac = ac_circuit.simulator(temperature=25, nominal_temperature=25).ac(
    start_frequency=1 @ u_Hz, stop_frequency=1 @ u_MHz,
    number_of_points=200, variation="dec",
)
freq = np.array(ac.frequency)
gain = np.abs(np.array(ac["out"]))          # |H| (1V 输入)
phase = np.degrees(np.angle(np.array(ac["out"])))

# 实测 -3dB 截止频率（对 |H| 曲线插值）
target = 1.0 / np.sqrt(2.0)
idx_above = np.where(gain >= target)[0]
idx_below = np.where(gain < target)[0]
cross = np.argmax(gain < target)            # 第一个跌到 -3dB 以下的点
f1, g1 = freq[cross - 1], gain[cross - 1]
f2, g2 = freq[cross], gain[cross]
fc_sim = np.exp(np.log(f1) + (np.log(target) - np.log(g1)) *
                (np.log(f2) - np.log(f1)) / (np.log(g2) - np.log(g1)))

# ---------------- 绘图 ----------------
fig, ax = plt.subplots(figsize=(9, 5))
ax.plot(t, vin, "g--", lw=1.2, label="输入 v_in（方波 1V/100Hz）")
ax.plot(t, vout, "b-", lw=1.8, label="输出 v_out（RC 充放电）")
ax.axhline(0.632, color="r", ls=":", lw=1)
ax.annotate("63.2%% → tau ≈ %.3f ms" % (tau_sim * 1e3),
            xy=(tau_sim * 1e3, 0.632), xytext=(5, 0.72),
            arrowprops=dict(arrowstyle="->", color="r"), color="r", fontsize=11)
ax.set_xlabel("时间 t (ms)")
ax.set_ylabel("电压 (V)")
ax.set_title("RC 低通滤波电路：方波输入/输出瞬态波形")
ax.grid(alpha=0.3)
ax.legend(loc="lower right")
fig.tight_layout()
fig.savefig(os.path.join(OUT_DIR, "rc_transient.png"), dpi=150)

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 7), sharex=True)
ax1.semilogx(freq, 20 * np.log10(gain), "b-", lw=1.8)
ax1.axvline(fc_theory, color="r", ls="--", lw=1,
            label="理论 fc = %.1f Hz" % fc_theory)
ax1.axhline(-3.0103, color="g", ls=":", lw=1, label="-3dB 线")
ax1.set_ylabel("幅频 |H| (dB)")
ax1.set_title("RC 低通滤波电路：波特图（仿真 AC 扫描）")
ax1.grid(alpha=0.3, which="both")
ax1.legend()
ax2.semilogx(freq, phase, "b-", lw=1.8)
ax2.axvline(fc_theory, color="r", ls="--", lw=1)
ax2.set_ylabel("相频 ∠H (°)")
ax2.set_xlabel("频率 f (Hz)")
ax2.grid(alpha=0.3, which="both")
fig.tight_layout()
fig.savefig(os.path.join(OUT_DIR, "rc_bode.png"), dpi=150)

# ---------------- 输出结果 ----------------
print("=" * 60)
print("RC 低通滤波电路  R=1kOhm  C=1uF")
print("-" * 60)
print("时间常数 tau   理论 = %.4f ms | 仿真 = %.4f ms | 误差 = %.2f%%"
      % (tau_theory * 1e3, tau_sim * 1e3,
         (tau_sim - tau_theory) / tau_theory * 100))
print("截止频率 fc    理论 = %.2f Hz | 仿真 = %.2f Hz | 误差 = %.2f%%"
      % (fc_theory, fc_sim, (fc_sim - fc_theory) / fc_theory * 100))
print("fc 处增益(仿真) = %.3f (理论 1/sqrt(2)=0.707)" % gain[cross])
print("图像已保存: rc_transient.png, rc_bode.png")
print("=" * 60)
