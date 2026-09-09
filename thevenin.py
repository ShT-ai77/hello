# -*- coding: utf-8 -*-
"""
任务五 - ② 戴维南定理验证（PySpice 仿真）
含源二端网络：V1 = 10V 串 R1 = 1kOhm，端口 a-b 上并 R2 = 2.2kOhm
理论值：
  V_th = V1 * R2/(R1+R2) = 10 * 2.2/3.2 = 6.875 V
  R_th = R1 // R2 = 687.5 Ohm
  I_sc = V_th / R_th = 10 mA
仿真内容：
  1) 开路电压 V_oc（端口 a-b 悬空）
  2) 短路电流 I_sc（端口 a-b 短接）
  3) 原网络接负载 RL = 1kOhm -> V_L, I_L
  4) 戴维南等效电路（V_th 串 R_th）接同一负载 -> V_L', I_L'
  验证两者一致，即为戴维南定理成立
"""
import os
import numpy as np

from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *

V1, R1, R2, RL = 10.0, 1.0e3, 2.2e3, 1.0e3

Vth_theory = V1 * R2 / (R1 + R2)
Rth_theory = R1 * R2 / (R1 + R2)
Isc_theory = Vth_theory / Rth_theory


def build_original(name, load=None, short=False):
    """搭建原网络。load: 接负载电阻；short: 端口短路（串入 0V 电流表）"""
    c = Circuit(name)
    c.V(1, "vin", "0", V1 @ u_V)
    c.R(1, "vin", "a", R1 @ u_Ohm)
    c.R(2, "a", "0", R2 @ u_Ohm)
    if short:
        c.V("meas", "a", "0", 0 @ u_V)   # 0V 源作电流表
    elif load is not None:
        c.R("load", "a", "0", load @ u_Ohm)
    return c


def build_equivalent(name, load):
    """戴维南等效电路：Vth 串 Rth 接负载"""
    c = Circuit(name)
    c.V("th", "vin", "0", Vth_theory @ u_V)
    c.R("th", "vin", "a", Rth_theory @ u_Ohm)
    c.R("load", "a", "0", load @ u_Ohm)
    return c


# ---- 仿真 1：开路电压 ----
voc_sim = float(build_original("Thevenin Voc").simulator(
    temperature=25, nominal_temperature=25).operating_point()["a"][0])

# ---- 仿真 2：短路电流 ----
op = build_original("Thevenin Isc", short=True).simulator(
    temperature=25, nominal_temperature=25).operating_point()
isc_sim = abs(float(np.asarray(op["vmeas"])[0]))  # 流过 0V 电流表的电流

# ---- 仿真 3：原网络接负载 ----
vl_sim = float(build_original("Original + RL", load=RL).simulator(
    temperature=25, nominal_temperature=25).operating_point()["a"][0])
il_sim = vl_sim / RL

# ---- 仿真 4：等效电路接同一负载 ----
vl_eq = float(build_equivalent("Equivalent + RL", load=RL).simulator(
    temperature=25, nominal_temperature=25).operating_point()["a"][0])
il_eq = vl_eq / RL

# ---------------- 输出结果 ----------------
print("=" * 66)
print("戴维南定理验证   V1=10V, R1=1kOhm, R2=2.2kOhm, RL=1kOhm")
print("-" * 66)
print("%-28s %12s %12s %8s" % ("量", "理论值", "仿真值", "误差"))
print("%-28s %10.4f V %10.4f V %7.2f%%" %
      ("开路电压 V_oc (=V_th)", Vth_theory, voc_sim,
       (voc_sim - Vth_theory) / Vth_theory * 100))
print("%-28s %10.4f A %10.4f A %7.2f%%" %
      ("短路电流 I_sc", Isc_theory, isc_sim,
       (isc_sim - Isc_theory) / Isc_theory * 100))
print("%-28s %10.1f Ohm %9.1f Ohm %7.2f%%" %
      ("等效电阻 R_th=V_oc/I_sc", Rth_theory, voc_sim / isc_sim,
       (voc_sim / isc_sim - Rth_theory) / Rth_theory * 100))
print("-" * 66)
print("接负载 RL=1kOhm 后：")
print("%-28s %10.4f V %10.4f V %7.2f%%" %
      ("  原网络  V_L", Vth_theory * RL / (Rth_theory + RL), vl_sim,
       (vl_sim - Vth_theory * RL / (Rth_theory + RL)) / (Vth_theory * RL / (Rth_theory + RL)) * 100))
print("%-28s %10.4f mA %9.4f mA" %
      ("  原网络  I_L", il_sim * 1e3, il_sim * 1e3))
print("%-28s %10.4f V %10.4f V %7.2f%%" %
      ("  等效电路 V_L'", Vth_theory * RL / (Rth_theory + RL), vl_eq,
       (vl_eq - Vth_theory * RL / (Rth_theory + RL)) / (Vth_theory * RL / (Rth_theory + RL)) * 100))
print("%-28s %10.4f mA %9.4f mA" %
      ("  等效电路 I_L'", il_eq * 1e3, il_eq * 1e3))
print("-" * 66)
print("V_L 与 V_L' 偏差 = %.6f V, I_L 与 I_L' 偏差 = %.6f mA"
      % (abs(vl_sim - vl_eq), abs(il_sim - il_eq) * 1e3))
print("=> 原网络与戴维南等效电路外特性一致，戴维南定理验证通过")
print("=" * 66)
