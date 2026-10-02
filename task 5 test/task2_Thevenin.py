# -*- coding: utf-8 -*-
# =====================================================================
# 考核任务②：戴维南定理验证（PySpice 仿真）
# ---------------------------------------------------------------------
# 含源二端网络（端口标注 a-b）：电压源 V1(12V) -> R1(4kΩ) -> 端口节点 p，
#                              R2(6kΩ) 并联在端口 p 与地之间
# 手算理论值：
#   开路电压（分压公式）：V_oc = V1 × R2/(R1+R2) = 12 × 6k/(4k+6k) = 7.2 V
#   短路电流：I_sc = V1/R1 = 12/4k = 3 mA（端口短路时 R2 被短路、无电流流过）
#   等效电阻（除源后）：R_th = R1∥R2 = R1·R2/(R1+R2) = 2.4 kΩ = V_oc/I_sc
#   接负载 RL=4.8kΩ 后（分压公式）：V_RL = V_oc × RL/(R_th+RL) = 4.8 V
# 验证思路：V_oc、I_sc 两次仿真 + 原网络接负载 vs 戴维南等效电路接负载，对比电压电流
# 运行输出：task2_thevenin_compare.png（手算 vs 仿真对比柱状图）+ 控制台数据摘要
# =====================================================================

import numpy as np                             # 导入 numpy：用于数值计算（柱状图数据整理）
import matplotlib.pyplot as plt                # 导入 matplotlib：绘图库，用于画对比柱状图
from PySpice.Spice.Netlist import Circuit      # 导入 Circuit 类：搭建 SPICE 网表
from PySpice.Unit import *                     # 导入单位系统：直接用 kΩ、V 等物理单位写参数

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']  # 设置中文字体防止乱码
plt.rcParams['axes.unicode_minus'] = False                       # 修复负号显示问题

# ---------------- 1. 电路参数（任务书规定①②电路参数自定） ----------------
V1 = 12.0                                      # 独立电压源 V1 = 12 V（网络内部的源）
R1 = 4e3                                       # 电阻 R1 = 4 kΩ（源内串联回路电阻，单位：Ω）
R2 = 6e3                                       # 电阻 R2 = 6 kΩ（端口并联电阻）
RL = 4.8e3                                     # 负载电阻 RL = 4.8 kΩ（验证用）

# 手算理论值（供对比）
voc_th = V1 * R2 / (R1 + R2)                   # 分压公式：V_oc = V1·R2/(R1+R2) = 7.2 V
isc_th = V1 / R1                               # 短路电流公式：I_sc = V1/R1 = 3 mA（R2 被短路不分流）
rth_th = R1 * R2 / (R1 + R2)                   # 并联等效电阻公式：R_th = R1R2/(R1+R2) = 2.4 kΩ
vrl_th = voc_th * RL / (rth_th + RL)           # 戴维南等效后接负载分压公式：V_RL = V_oc·RL/(R_th+RL) = 4.8 V
irl_th = vrl_th / RL                           # 欧姆定律：I_RL = V_RL/RL = 1 mA

# ---------------- 2. 仿真一：测开路电压 V_oc（端口 a-b 空载） ----------------
c1 = Circuit('原网络-开路')                     # 网表一：原网络，不接负载
c1.V('1', 'a', c1.gnd, V1 @ u_V)               # 电压源 V1 从节点 a（电源正）对地 12V
c1.R(1, 'a', 'p', R1 @ u_Ohm)                  # R1 从电源正端串到端口节点 p
c1.R(2, 'p', c1.gnd, R2 @ u_Ohm)               # R2 并联在端口 p 与地之间（构成二端网络）
op1 = c1.simulator(temperature=25, nominal_temperature=25).operating_point()  # 直流工作点分析（基尔霍夫定律求解）
voc_sim = float(op1['p'][0])                   # 端口开路时 p 点电压即 V_oc（无电流流出端口）

# ---------------- 3. 仿真二：测短路电流 I_sc（端口 a-b 短路） ----------------
c2 = Circuit('原网络-端口短路')                 # 网表二：原网络，端口用 0V 电压源当"电流表"短接
c2.V('1', 'a', c2.gnd, V1 @ u_V)               # 同上：12V 电源
c2.R(1, 'a', 'p', R1 @ u_Ohm)                  # R1 串联
c2.R(2, 'p', c2.gnd, R2 @ u_Ohm)               # R2 并联
c2.V('sc', 'p', c2.gnd, 0 @ u_V)               # 0V 电压源 Vsc 把端口 p 短接到地：0V 源不影响电路，只读取流过它的电流
op2 = c2.simulator(temperature=25, nominal_temperature=25).operating_point()  # 直流工作点分析
isc_sim = abs(float(op2.branches['vsc'][0]))   # 从 Vsc 支路读短路电流（取绝对值，方向取决于源的正方向定义）

rth_sim = voc_sim / isc_sim                    # 等效电阻公式：R_th = V_oc/I_sc（戴维南等效电阻的实验测定法）

# ---------------- 4. 仿真三：原网络接负载 RL，测负载电压电流 ----------------
c3 = Circuit('原网络-接负载')                   # 网表三：原网络端口接真实负载
c3.V('1', 'a', c3.gnd, V1 @ u_V)               # 12V 电源
c3.R(1, 'a', 'p', R1 @ u_Ohm)                  # R1 串联
c3.R(2, 'p', c3.gnd, R2 @ u_Ohm)               # R2 并联
c3.R('L', 'p', c3.gnd, RL @ u_Ohm)             # 负载 RL 接在端口 p 与地之间
op3 = c3.simulator(temperature=25, nominal_temperature=25).operating_point()  # 直流工作点分析
vrl_sim_orig = float(op3['p'][0])              # 负载两端电压（p 点对地电压）
irl_sim_orig = vrl_sim_orig / RL               # 欧姆定律：I_RL = V_RL/RL

# ---------------- 5. 仿真四：戴维南等效电路（V_oc 串 R_th）接同一负载 ----------------
c4 = Circuit('戴维南等效-接负载')               # 网表四：用等效源替代原网络
c4.V('th', 't', c4.gnd, voc_sim @ u_V)         # 等效电压源 V_th = 仿真测得的 V_oc ≈ 7.2V
c4.R('th', 't', 'p', rth_sim @ u_Ohm)          # 等效内阻 R_th = V_oc/I_sc ≈ 2.4kΩ 串联
c4.R('L', 'p', c4.gnd, RL @ u_Ohm)             # 同一个负载 RL
op4 = c4.simulator(temperature=25, nominal_temperature=25).operating_point()  # 直流工作点分析
vrl_sim_thev = float(op4['p'][0])              # 等效电路下负载电压（应与原网络完全一致）
irl_sim_thev = vrl_sim_thev / RL               # 等效电路下负载电流

# ---------------- 6. 画"手算 vs 仿真"对比柱状图并保存 ----------------
labels = ['V_oc (V)', 'I_sc (mA)', 'R_th (kΩ)', 'V_RL-原网络 (V)', 'V_RL-等效电路 (V)']  # 五个对比项标签
hand_vals = [voc_th, isc_th * 1e3, rth_th / 1e3, vrl_th, vrl_th]                        # 手算值（统一量纲后）
sim_vals = [voc_sim, isc_sim * 1e3, rth_sim / 1e3, vrl_sim_orig, vrl_sim_thev]          # 仿真值（统一量纲后）
x = np.arange(len(labels))                     # 柱状图横坐标位置数组
w = 0.35                                       # 每根柱子的宽度
plt.figure(figsize=(10, 5.5))                  # 新建画布
b1 = plt.bar(x - w / 2, hand_vals, w, color='#4C72B0', label='手算理论值')               # 左柱：手算值
b2 = plt.bar(x + w / 2, sim_vals, w, color='#DD8452', label='PySpice 仿真值')           # 右柱：仿真值
for bars in (b1, b2):                          # 遍历两组柱子
    for b in bars:                             # 遍历每根柱子
        plt.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.08,          # 在柱顶上方标注数值
                 '%.3f' % b.get_height(), ha='center', fontsize=9)
plt.xticks(x, labels, fontsize=9)              # 横轴刻度标签
plt.ylabel('数值')                             # y 轴标签
plt.title('任务② 戴维南定理验证：手算 vs 仿真（R_th=R1∥R2，V_oc/I_sc 两种算法一致）')  # 标题
plt.legend()                                   # 图例
plt.grid(axis='y', alpha=0.3)                  # y 向网格便于读数
plt.tight_layout()                             # 调整布局
plt.savefig('task2_thevenin_compare.png', dpi=150)  # 保存对比图 png

# ---------------- 7. 打印数据摘要：手算 vs 仿真 对比表 ----------------
print('=' * 66)                                # 分隔线
print('任务② 戴维南定理验证 —— 手算 vs 仿真 数据摘要')                     # 表标题
print('=' * 66)                                # 分隔线
print('项目               手算理论值      仿真值         相对误差')           # 表头
print('-' * 66)                                # 分隔线
print('V_oc 开路电压     %-12.4f V    %-12.4f V    %.3f%%' %              # 开路电压对比（分压公式）
      (voc_th, voc_sim, abs(voc_sim - voc_th) / voc_th * 100))
print('I_sc 短路电流     %-12.4f mA   %-12.4f mA   %.3f%%' %              # 短路电流对比（I_sc=V1/R1）
      (isc_th * 1e3, isc_sim * 1e3, abs(isc_sim - isc_th) / isc_th * 100))
print('R_th 等效电阻     %-12.4f kΩ   %-12.4f kΩ   %.3f%%' %              # 等效电阻对比（R_th=R1∥R2 与 V_oc/I_sc 双算法）
      (rth_th / 1e3, rth_sim / 1e3, abs(rth_sim - rth_th) / rth_th * 100))
print('V_RL 原网络接负载 %-12.4f V    %-12.4f V    %.3f%%' %              # 原网络负载电压对比
      (vrl_th, vrl_sim_orig, abs(vrl_sim_orig - vrl_th) / vrl_th * 100))
print('V_RL 等效电路接负载 %-10.4f V    %-12.4f V    %.3f%%' %            # 等效电路负载电压对比（应≈0 误差）
      (vrl_th, vrl_sim_thev, abs(vrl_sim_thev - vrl_th) / vrl_th * 100))
print('-' * 66)                                # 分隔线
print('负载电流：原网络 %.4f mA，等效电路 %.4f mA（二者一致 → 戴维南等效对外电路完全成立）' %
      (irl_sim_orig * 1e3, irl_sim_thev * 1e3))                                 # 电流验证结论
print('结论：R_th 可用 R1∥R2（除源）与 V_oc/I_sc（实验法）两种方法求得，结果一致')     # 结论

plt.show()                                     # 弹出图窗（已先保存 png）
