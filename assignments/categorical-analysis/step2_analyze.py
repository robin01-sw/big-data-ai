# -*- coding: utf-8 -*-
"""
第 2 步：列联表 + 卡方检验 + 关联强度
------------------------------------
输入：outputs/cleaned_data.csv（第 1 步产出）
输出：outputs/ 下的列联表 csv、检验结果 txt、热力图 png

分析思路：
    两个类别变量（父亲职业 × 母亲职业）之间有没有关联，标准做法是
      ① 做交叉列联表，看条件分布（父亲的类别固定时，母亲类别的分布是否变化）
      ② 卡方独立性检验：H0 = 两者独立（无关联）
      ③ 关联强度：Cramér's V（0 = 完全无关，1 = 完全相关）
      ④ 样本量小、单元格期望频数偏低时，卡方近似不可靠，用置换检验复核
"""

import os
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "outputs")
DATA = os.path.join(OUT, "cleaned_data.csv")

# 中文字体（Windows 自带雅黑 / 黑体）
for f in ("Microsoft YaHei", "SimHei", "SimSun"):
    if any(f.lower() in x.name.lower() for x in font_manager.fontManager.ttflist):
        plt.rcParams["font.sans-serif"] = [f]
        break
plt.rcParams["axes.unicode_minus"] = False

log_lines = []


def log(msg=""):
    print(msg)
    log_lines.append(str(msg))


df = pd.read_csv(DATA, encoding="utf-8-sig")
N = len(df)
log(f"样本量 N = {N}")

F_CATS = ["公共部门（党政机关·事业单位）", "国有企业", "民营企业", "个体经营", "家庭主妇", "无业·未填"]
SHORT = {
    "公共部门（党政机关·事业单位）": "公共部门",
    "国有企业": "国企",
    "民营企业": "民营",
    "个体经营": "个体",
    "家庭主妇": "家庭主妇",
    "无业·未填": "无业/未填",
}


def analyze(row_col, col_col, tag, cats_order=None, title=""):
    """对一对类别变量做完整分析，返回结果字典"""
    ct = pd.crosstab(df[row_col], df[col_col])
    if cats_order:
        ct = ct.reindex(index=cats_order, columns=cats_order, fill_value=0)

    log(f"\n{'='*66}")
    log(f"{title or tag}：{row_col} × {col_col}")
    log(f"{'='*66}")
    log("【观察频数列联表】")
    log(ct.to_string())
    ct.to_csv(os.path.join(OUT, f"列联表_{tag}_频数.csv"), encoding="utf-8-sig")

    row_pct = (ct.div(ct.sum(axis=1), axis=0) * 100).round(1)
    log("\n【行百分比（每一行合计 100%，用于看条件分布）】")
    log(row_pct.to_string())
    row_pct.to_csv(os.path.join(OUT, f"列联表_{tag}_行百分比.csv"), encoding="utf-8-sig")

    chi2, p, dof, expected = stats.chi2_contingency(ct.values, correction=False)
    n = ct.values.sum()
    r, c = ct.shape
    cramer_v = np.sqrt(chi2 / (n * (min(r, c) - 1)))
    small = (expected < 5).sum()
    small_ratio = small / expected.size

    log("\n【卡方独立性检验】")
    log(f"  χ² = {chi2:.3f}，自由度 df = {dof}，p = {p:.4f}")
    log(f"  Cramér's V = {cramer_v:.3f}")
    log(f"  期望频数 < 5 的单元格：{small}/{expected.size}（占 {small_ratio:.0%}）")
    if p < 0.05:
        log("  → p < 0.05，拒绝 H0：两变量存在显著关联")
    else:
        log("  → p ≥ 0.05，不能拒绝 H0：未发现显著关联（可视作相互独立）")

    # 置换检验：把母亲职业随机打乱，看随机情况下的 χ² 分布
    rng = np.random.default_rng(20261112)
    other = df[col_col].values.copy()
    obs = chi2
    B = 5000
    cnt = 0
    for _ in range(B):
        perm = rng.permutation(other)
        t = pd.crosstab(df[row_col], perm).values
        # 保证形状一致
        c2 = stats.chi2_contingency(t, correction=False)[0] if t.shape[1] > 1 else 0.0
        if c2 >= obs:
            cnt += 1
    p_perm = (cnt + 1) / (B + 1)
    log(f"\n【置换检验（{B} 次随机重排，不依赖期望频数假设）】")
    log(f"  p(置换) = {p_perm:.4f}")

    return {"tag": tag, "n": n, "chi2": chi2, "dof": dof, "p": p, "V": cramer_v,
            "p_perm": p_perm, "small": small, "cells": expected.size, "ct": ct}


res6 = analyze("父亲职业", "母亲职业", "详细6x6", F_CATS,
               title="一、六类职业细分")
res3 = analyze("父亲职业_粗", "母亲职业_粗", "粗分3x3", None,
               title="二、合并为三类的稳健检验")

# ---------------------------------------------------------------- 描述性补充
log("\n" + "=" * 66)
log("三、与'母亲是否家庭主妇'相关的描述统计")
log("=" * 66)
mom_house = df["母亲职业"] == "家庭主妇"
log(f"母亲为家庭主妇的家庭：{mom_house.sum()} / {N}（{mom_house.mean():.1%}）")
log("\n其中父亲的职业分布：")
log(df.loc[mom_house, "父亲职业"].value_counts().to_string())
log("\n其余家庭中父亲的职业分布：")
log(df.loc[~mom_house, "父亲职业"].value_counts().to_string())

# 父亲是否体制内 & 母亲是否家庭主妇 的 2×2 表
sub = df.copy()
sub["父亲体制内"] = np.where(sub["父亲职业_粗"] == "体制内（公共部门+国企）", "体制内", "体制外")
ct2 = pd.crosstab(sub["父亲体制内"], np.where(mom_house, "家庭主妇", "有工作"))
log("\n【父亲是否体制内 × 母亲是否家庭主妇】")
log(ct2.to_string())
try:
    chi2b, pb, dofb, expb = stats.chi2_contingency(ct2.values, correction=True)
    log(f"χ²(连续性校正) = {chi2b:.3f}，df = {dofb}，p = {pb:.4f}")
except Exception as e:
    pb = np.nan
    log(f"（2×2 检验无法计算：{e}）")

# ---------------------------------------------------------------- 可视化
fig, axes = plt.subplots(1, 2, figsize=(14.5, 5.6))
labels = [SHORT[c] for c in res6["ct"].index]
cols = [SHORT[c] for c in res6["ct"].columns]

for ax, mat, title, fmt, cmap in (
    (axes[0], res6["ct"].values, "（a）观察频数", "d", "Blues"),
    (axes[1], (res6["ct"].div(res6["ct"].sum(axis=1), axis=0) * 100).values,
     "（b）行百分比 / %", ".0f", "Oranges"),
):
    im = ax.imshow(mat, cmap=cmap, aspect="auto")
    ax.set_xticks(range(len(cols)))
    ax.set_xticklabels(cols, rotation=30, ha="right")
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels)
    ax.set_xlabel("母亲职业类别")
    ax.set_ylabel("父亲职业类别")
    ax.set_title(title, fontsize=11)
    vmax = mat.max()
    for i in range(mat.shape[0]):
        for j in range(mat.shape[1]):
            v = mat[i, j]
            ax.text(j, i, format(v, fmt), ha="center", va="center", fontsize=9,
                    color="white" if v > vmax * 0.6 else "#333")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.03)

fig.suptitle(f"父母职业的列联表（N={N}）", fontsize=13)
fig.tight_layout()
png = os.path.join(OUT, "列联表热力图.png")
fig.savefig(png, dpi=170)
log(f"\n[输出] 热力图 → {os.path.relpath(png, HERE)}")

# 边际分布条形图
fig2, axes2 = plt.subplots(1, 2, figsize=(14.5, 4.6), sharey=True)
for ax, col, name, color in ((axes2[0], "父亲职业", "父亲", "#2c6fa8"),
                             (axes2[1], "母亲职业", "母亲", "#c0392b")):
    vc = df[col].value_counts().reindex(F_CATS).fillna(0).astype(int)
    y = np.arange(len(F_CATS))
    ax.barh(y, vc.values, color=color, alpha=.85)
    ax.set_yticks(y)
    ax.set_yticklabels([SHORT[c] for c in F_CATS])
    ax.invert_yaxis()
    ax.set_xlim(0, vc.max() * 1.18)
    ax.set_xlabel("人数")
    ax.set_title(f"{name}亲职业分布（N={N}）")
    for i, v in enumerate(vc.values):
        ax.text(v + .3, i, str(v), va="center", fontsize=9)
fig2.subplots_adjust(left=0.09, right=0.97, top=0.88, bottom=0.15, wspace=0.15)
png2 = os.path.join(OUT, "边际分布.png")
fig2.savefig(png2, dpi=170)
log(f"[输出] 边际分布图 → {os.path.relpath(png2, HERE)}")

# ---------------------------------------------------------------- 汇总
summary = pd.DataFrame([
    {"表": "六类细分 6×6", "χ²": round(res6["chi2"], 3), "df": res6["dof"],
     "p(卡方)": round(res6["p"], 4), "p(置换)": round(res6["p_perm"], 4),
     "Cramér's V": round(res6["V"], 3),
     "期望频数<5的格子": f"{res6['small']}/{res6['cells']}"},
    {"表": "合并三类 3×3", "χ²": round(res3["chi2"], 3), "df": res3["dof"],
     "p(卡方)": round(res3["p"], 4), "p(置换)": round(res3["p_perm"], 4),
     "Cramér's V": round(res3["V"], 3),
     "期望频数<5的格子": f"{res3['small']}/{res3['cells']}"},
])
log("\n" + "=" * 66)
log("四、结果汇总")
log("=" * 66)
log(summary.to_string(index=False))
summary.to_csv(os.path.join(OUT, "检验结果汇总.csv"), index=False, encoding="utf-8-sig")

with open(os.path.join(OUT, "step2_report.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(log_lines))
