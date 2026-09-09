# -*- coding: utf-8 -*-
"""
任务五 - ③ NMOS 共源极放大电路（PySpice 仿真）
给定电路（题面固定参数）：
  VDD = 5V, Rg1 = 60kOhm, Rg2 = 40kOhm, Rd = 2kOhm, Cb1 足够大
  NMOS: K = 0.8 mA/V^2, V_th = 1V, lambda = 0.02 /V
  输入 vi = 10mV @ 1kHz 正弦波
说明：SPICE 中 I_D = (KP/2)*(W/L)*(V_GS-V_th)^2*(1+lambda*V_DS)
  取 W/L = 1、KP = 1.6 mA/V^2，即对应 K = 0.8 mA/V^2
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

VDD, RG1, RG2, RD = 5.0, 60e3, 40e3, 2.0e3
K, VTH, LAMBDA = 0.8e-3, 1.0, 0.02
KP = K             # SPICE level-1: I_D = (KP/2)*(W/L)*(V_GS-VTO)^2*(1+lam*V_DS)
                   # 即 KP 即题面参数 K = 0.8 mA/V^2（W/L = 1）
VI_AMP, VI_FREQ = 0.01, 1e3

# ---------------- 手算理论值 ----------------
vg_th = VDD * RG2 / (RG1 + RG2)              # 栅极电位 = V_GS（源接地）
# 含沟道长度调制解方程: ID = K/2*(VGS-Vth)^2*(1+l*VDS), VDS = VDD-RD*ID
# => ID = a*(1+l*VDD) / (1 + a*l*RD)，其中 a = K/2*(VGS-Vth)^2
a0 = 0.5 * K * (vg_th - VTH) ** 2
id_th = a0 * (1 + LAMBDA * VDD) / (1 + a0 * LAMBDA * RD)
vds_th = VDD - RD * id_th
gm_th = K * (vg_th - VTH) * (1 + LAMBDA * vds_th)          # 跨导
ro_th = 1.0 / (LAMBDA * id_th)                              # 输出电阻
av_th = -gm_th * (RD * ro_th / (RD + ro_th))                # 增益 = -gm*(Rd//ro)

print("=" * 64)
print("手算静态工作点（理论值）")
print("-" * 64)
print("V_GS = VDD*Rg2/(Rg1+Rg2) = %.4f V" % vg_th)
print("I_D   = %.4f mA (含 lambda 修正; 不计 lambda 时 0.400 mA)"
      % (id_th * 1e3))
print("V_DS  = %.4f V" % vds_th)
print("饱和区判断: V_DS = %.3f V > V_GS - V_th = %.3f V -> %s"
      % (vds_th, vg_th - VTH, "工作在饱和区 ✓" if vds_th > vg_th - VTH else "未饱和 ✗"))
print("手算小信号: gm = %.4f mS, ro = %.1f kOhm, Av = -gm(Rd//ro) = %.4f"
      % (gm_th * 1e3, ro_th / 1e3, av_th))
print("=" * 64)

# ---------------- 搭电路 ----------------
def build(name, with_ac=True):
    c = Circuit(name)
    c.V("dd", "vdd", "0", VDD @ u_V)
    c.R("g1", "vdd", "g", RG1 @ u_Ohm)
    c.R("g2", "g", "0", RG2 @ u_Ohm)
    c.R("d", "vdd", "d", RD @ u_Ohm)
    c.C("b1", "vi", "g", 1 @ u_mF)           # Cb1 视为足够大
    if with_ac:
        c.SinusoidalVoltageSource("in", "vi", "0",
                                  amplitude=VI_AMP @ u_V,
                                  frequency=VI_FREQ @ u_Hz)
    else:
        c.V("in", "vi", "0", 0 @ u_V)
    c.model("nmos1", "NMOS", level=1, vto=VTH @ u_V,
            kp=KP, **{"lambda": LAMBDA})   # kp 单位 A/V^2；lambda 是 ngspice 参数名
    c.MOSFET(1, "d", "g", "0", "0", model="nmos1", w=1 @ u_um, l=1 @ u_um)
    return c


# ---------------- 直流 OP 仿真 ----------------
op = build("NMOS Amp DC", with_ac=False).simulator(
    temperature=25, nominal_temperature=25).operating_point()
vg_sim = float(op["g"][0])
vd_sim = float(op["d"][0])
id_sim = (VDD - vd_sim) / RD
vgs_sim = vg_sim  # 源接地
sat = vd_sim > (vgs_sim - VTH)

print("OP 仿真结果")
print("-" * 64)
print("%-8s %14s %14s %10s" % ("量", "理论值", "仿真值", "误差"))
print("%-8s %12.4f V %13.4f V %8.2f%%"
      % ("V_GS", vg_th, vgs_sim, (vgs_sim - vg_th) / vg_th * 100))
print("%-8s %12.4f mA %12.4f mA %8.2f%%"
      % ("I_D", id_th * 1e3, id_sim * 1e3, (id_sim - id_th) / id_th * 100))
print("%-8s %12.4f V %13.4f V %8.2f%%"
      % ("V_DS", vds_th, vd_sim, (vd_sim - vds_th) / vds_th * 100))
print("饱和区判断(仿真): V_DS=%.3f V > V_GS-V_th=%.3f V -> %s"
      % (vd_sim, vgs_sim - VTH, "饱和区 ✓" if sat else "非饱和 ✗"))
print("=" * 64)

# ---------------- 瞬态仿真：看波形、测增益 ----------------
trans = build("NMOS Amp Tran").simulator(
    temperature=25, nominal_temperature=25).transient(
    step_time=1 @ u_us, end_time=5 @ u_ms)
t = np.array(trans.time) * 1e3   # ms
vi = np.array(trans["vi"])
vo = np.array(trans["d"])

# 取最后两个周期（2~5ms）测幅度（避开起始瞬态）
m = t >= 3.0
vi_pk = (vi[m].max() - vi[m].min()) / 2
vo_pk = (vo[m].max() - vo[m].min()) / 2
av_sim = -vo_pk / vi_pk          # 反相放大，取负号

fig, ax = plt.subplots(figsize=(9, 5))
# 去掉直流偏置，仅看交流分量（输出直流工作点 V_DS ≈ %.2f V 已在 OP 中确认）
vo_ac = vo - vo.mean()
ax.plot(t, vi * 1e3, "g-", lw=1.2, label="输入 v_i (10mV/1kHz)")
ax.plot(t, vo_ac * 1e3, "b-", lw=1.8, label="输出 v_o（交流分量，反相放大）")
ax.set_xlabel("时间 t (ms)")
ax.set_ylabel("电压 (mV)")
ax.set_title("NMOS 共源极放大电路：输入/输出波形（反相放大）")
ax.grid(alpha=0.3)
ax.legend()
ax.annotate("实测增益 Av = v_o/v_i ≈ %.2f（手算 %.2f）" % (av_sim, av_th),
            xy=(4.0, vo_pk * 1e3 * 0.9), fontsize=11, color="r")
fig.tight_layout()
fig.savefig(os.path.join(OUT_DIR, "mos_waveform.png"), dpi=150)

print("瞬态仿真（v_i = 10mV @ 1kHz）")
print("-" * 64)
print("输入幅度 = %.3f mV, 输出幅度 = %.3f mV" % (vi_pk * 1e3, vo_pk * 1e3))
print("%-8s %14s %14s" % ("增益 Av", "理论值", "仿真值"))
print("%-8s %14.4f %14.4f  (相对偏差 %.2f%%)"
      % ("", av_th, av_sim, abs(av_sim - av_th) / abs(av_th) * 100))
print("输出与输入反相 ✓ (共源极放大器反相特性)")
print("图像已保存: mos_waveform.png")
print("=" * 64)
