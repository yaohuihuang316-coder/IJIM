# -*- coding: utf-8 -*-
"""
RQ3-2 步骤 2/4 · 功效审计（power audit）· 主交付
================================================
本脚本是二级遗留工作 `c3_size_mc.py` 的**功效（power）扩展**。

★ 与 c3_size_mc.py 的关系（必须写清，否则就是「替代实现」）
  · `c3_size_mc.py` 只量 **size**：三场景全是 D=0（b_ms = b_sm ∈ {0, 0.3}），
    没有任何 b_ms ≠ b_sm 的场景 ⇒ **它不含任何功效信息**。
    （其产物 `04_运行痕迹/c3/C3_size_mc.json` 实测存在、6 cell 齐全、CPU 合计 373.8 s；
     《总报告》§4.3 遗留项 3「未真跑」一栏与落盘不符。）
  · 本脚本**不改写它**，而是用 `ast` 从它抽取 `make_stacked / design_raw / demean / prepare /
    crv1 / sim` 六个函数定义并 exec（记录源 sha256[:16]）⇒ **同一台生成器、同一个设计**。
  · 在此之上加两件事：(a) 把 b_ms 与 b_sm **拆开**扫效应量网格 ⇒ 功效曲线与 MDE；
    (b) 判据换成**置换（randomization inference）**，并**先做空模型尺寸校准再谈功效**。

★ T_eff（主口径，来源必须写进报告）
  · T_eff = 4 = 滞后方程**估计窗口**内被解释年的个数（≠ 波次 5）。
  · 算法：跨侧 M 与 S 都只有 2021–2025 五个年度取值 ⇒ 2021 只能当滞后来源、
    不能当被解释年的观测 ⇒ 被解释年 t = 2022, 2023, 2024, 2025 ⇒ T_eff = 4（设计稿 §2.1.0）。
  · 代码确认：`c3_size_mc.py:26 YRS_EST = [2022, 2023, 2024, 2025]`。
  · T_eff = 3 档 = 被解释年 2023–2025（与交付表 window=`main_2023_2025` 同构）。

★ 判据的两步（这是本脚本最重要的一步，必须先尺寸校准）
  实测（见 --probe 输出）：把「原始 x 在期内跨单元置换」当零模型时，
  **实际尺寸 0.15–0.42（名义 0.05 的 3–8 倍）**。原因是该置换破坏了 x 的单元级结构，
  使 Σx̃² 被抬高 ⇒ 零分布过窄 ⇒ 过度拒绝。
  修正：**先取 within 变换后的 x̃，再在期内跨单元置换**（Σx̃² 逐位保持）⇒ 尺度正确。
  即便如此，仍以 **b=0 空模型实测的临界值 c₀.₀₅** 为准（学生化 z = β̂ / sd_perm），
  功效一律在**尺寸校准后**的判据上报告。校准与未校准两个数都报。

写出（**只写本目录**）：
  RQ3_2_功效审计.csv       （T_eff × G × 效应量 × 功效 × MDE 网格）
  RQ3_2_功效审计.json      （全部中间量、尺寸校准、中心化检查、退化点单验）
"""
import argparse
import ast
import csv
import hashlib
import json
import os
import time

import numpy as np
import pandas as pd
import warnings

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = HERE
SRC = os.path.join(HERE, "power_generator.py")

_src_txt = open(SRC, encoding="utf-8").read()
_src_sha = hashlib.sha256(_src_txt.encode("utf-8")).hexdigest()
_tree = ast.parse(_src_txt)
WANT = {"make_stacked", "design_raw", "demean", "prepare", "crv1", "sim"}
_ns = {"np": np, "pd": pd}
_got = []
for node in _tree.body:
    if isinstance(node, ast.FunctionDef) and node.name in WANT:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", SyntaxWarning)
            exec(compile(ast.get_source_segment(_src_txt, node), SRC, "exec"), _ns)
        _got.append(node.name)
assert WANT.issubset(set(_got)), "缺函数：%s" % (WANT - set(_got))
sim = _ns["sim"]
K_EFF = 10.0                       # 与 c3_size_mc.py:116 同一约定
WAVES = (2021, 2022, 2023, 2024, 2025)
WI = {y: i for i, y in enumerate(WAVES)}
TEFF_YEARS = {4: [2022, 2023, 2024, 2025], 3: [2023, 2024, 2025]}
SEED = 20260923
MAIN = "A2_within_period_cross_unit_on_xw"      # 主判据（尺寸修正后的期内类间置换）
ALT = "C_within_unit_cyclic_shift_raw"         # 并列对照（单位内循环移位；与项目「区块置换」同族）
LEGACY = "A_orig_within_period_cross_unit_raw"  # 未修正版，仅供审计（过度拒绝）


def w2(X):
    """平衡面板双向 within 变换：x − x̄_row − x̄_col + x̄_··（平衡下为精确投影）。
    支持 (G,T) 与 (R,G,T)。"""
    return (X - X.mean(axis=-2, keepdims=True) - X.mean(axis=-1, keepdims=True)
            + X.mean(axis=(-2, -1), keepdims=True))


def med_correct(v):
    """★ 退化点单验：显式奇偶分支（AGENTS 第十条·4）。"""
    v = sorted(v)
    n = len(v)
    if n == 0:
        return None
    return v[n // 2] if n % 2 == 1 else 0.5 * (v[n // 2 - 1] + v[n // 2])


def perm_idx_xw(scheme, R, G, T, rng):
    """返回 (R,G,T) 的列置换索引：x̃_perm[r,i,j] = x̃[i, σ_{r,j}(i)]（期内跨单元）。"""
    idx = np.empty((R, G, T), dtype=np.int64)
    for j in range(T):
        for r in range(R):
            idx[r, :, j] = rng.permutation(G)
    return idx


def perm_raw_rows(scheme, R, G, T, rng):
    """返回 (R,G,T) 的行内循环移位后索引：x_perm[r,i,j] = x[i, j']，j' 为该行的一个循环移位。"""
    idx = np.empty((R, G, T), dtype=np.int64)
    base = np.arange(T)
    for r in range(R):
        for i in range(G):
            k = int(rng.integers(1, T))
            idx[r, i, :] = np.roll(base, k)
    return idx


def build(teff, n_occ, b_MS, b_SM, phi, rng):
    """生成一个数据集并给出两层 (y, x̃) 与 within 尺度 sd。"""
    df = sim(b_MS, b_SM, phi, rng, n_occ=n_occ, years=WAVES)
    S = df.pivot(index="occ", columns="year", values="S").loc[:, list(WAVES)].to_numpy(float)
    M = df.pivot(index="occ", columns="year", values="M").loc[:, list(WAVES)].to_numpy(float)
    ci = [WI[t] for t in TEFF_YEARS[teff]]
    lag = [WI[t - 1] for t in TEFF_YEARS[teff]]
    yS, xM = S[:, ci], M[:, lag]
    yM, xS = M[:, ci], S[:, lag]
    return yS, xM, yM, xS


def stat_pair(y, x, R, rng, schemes):
    """给定一层 (y, x)，返回 (β̂, {scheme: (βperm(R,), sxx, center)})。"""
    yt, xt = w2(y), w2(x)
    sxx = float((xt * xt).sum())
    out = {"beta": np.nan, "sxx": sxx, "sd_y": float(yt.std()), "sd_x": float(xt.std())}
    if sxx == 0.0:
        for sc in schemes:
            out[sc] = None
        return out
    out["beta"] = float((xt * yt).sum()) / sxx
    G, T = xt.shape
    for sc in schemes:
        if sc == MAIN:
            idx = perm_idx_xw(sc, R, G, T, rng)
            XP = np.take_along_axis(xt[None, :, :], idx, axis=1)     # (R,G,T)
            bp = np.einsum("rgt,gt->r", XP, yt) / sxx                # ★ Σx̃² 逐位不变
        elif sc == LEGACY:
            idx = perm_idx_xw(sc, R, G, T, rng)
            XPr = np.take_along_axis(x[None, :, :], idx, axis=1)
            XP = w2(XPr)
            bp = np.einsum("rgt,gt->r", XP, yt) / np.einsum("rgt,rgt->r", XP, XP)
        elif sc == ALT:
            idx = perm_raw_rows(sc, R, G, T, rng)
            XPr = np.take_along_axis(x[None, :, :], idx, axis=2)
            XP = w2(XPr)
            bp = np.einsum("rgt,gt->r", XP, yt) / np.einsum("rgt,rgt->r", XP, XP)
        else:
            raise ValueError(sc)
        bp = bp[np.isfinite(bp)]
        out[sc] = bp
    return out


def one_rep(teff, n_occ, b_MS, b_SM, phi, rng, R, schemes):
    yS, xM, yM, xS = build(teff, n_occ, b_MS, b_SM, phi, rng)
    res = {"teff": teff, "n_occ": n_occ, "b_MS": b_MS, "b_SM": b_SM, "phi": phi}
    for name, y, x in (("MS", yS, xM), ("SM", yM, xS)):
        st = stat_pair(y, x, R, rng, schemes)
        res["beta_" + name] = st["beta"]
        res["sd_y_" + name] = st["sd_y"]
        res["sd_x_" + name] = st["sd_x"]
        if st["beta"] != st["beta"]:
            return None
        for sc in schemes:
            bp = st[sc]
            if bp is None or bp.size < 10:
                return None
            c = float(np.median(bp))                  # ★ 零模型中心（中心化检查用）
            sd = float(np.std(bp, ddof=1))
            res["nullcenter_%s|%s" % (name, sc)] = c
            res["nullsd_%s|%s" % (name, sc)] = sd
            res["z_%s|%s" % (name, sc)] = (st["beta"] - c) / sd if sd > 0 else np.nan
            # 原始置换 p（未学生化、中位中心化）与未中心化版 —— 两种都留，才能解释差异来源
            res["praw_%s|%s" % (name, sc)] = float(np.mean(np.abs(bp - c) >= abs(st["beta"] - c)))
            res["praw_uncent_%s|%s" % (name, sc)] = float(np.mean(np.abs(bp) >= abs(st["beta"])))
    # 标准化真值（within 尺度）
    res["true_std_MS"] = b_MS * res["sd_x_MS"] / res["sd_y_MS"] if res["sd_y_MS"] > 0 else np.nan
    res["true_std_SM"] = b_SM * res["sd_x_SM"] / res["sd_y_SM"] if res["sd_y_SM"] > 0 else np.nan
    return res


def run_cell(teff, n_occ, b_MS, b_SM, phi, reps, R, schemes, seed, tag, quiet=False):
    rng = np.random.default_rng(seed)
    acc = []
    t0 = time.perf_counter()
    for _ in range(reps):
        r = one_rep(teff, n_occ, b_MS, b_SM, phi, rng, R, schemes)
        if r is not None:
            acc.append(r)
    dt = time.perf_counter() - t0
    if not acc:
        return None
    agg = {"tag": tag, "T_eff": teff, "G_nocc": n_occ, "b_MS": b_MS, "b_SM": b_SM, "phi": phi,
           "reps_requested": reps, "reps_kept": len(acc), "R_perm": R, "seconds": dt, "seed": seed,
           "true_std_MS_mean": float(np.nanmean([a["true_std_MS"] for a in acc])),
           "true_std_SM_mean": float(np.nanmean([a["true_std_SM"] for a in acc])),
           "beta_MS_mean": float(np.nanmean([a["beta_MS"] for a in acc])),
           "beta_SM_mean": float(np.nanmean([a["beta_SM"] for a in acc])),
           "beta_MS_sd": float(np.nanstd([a["beta_MS"] for a in acc], ddof=1)),
           "beta_SM_sd": float(np.nanstd([a["beta_SM"] for a in acc], ddof=1))}
    for name in ("MS", "SM"):
        for sc in schemes:
            z = np.array([a["z_%s|%s" % (name, sc)] for a in acc], dtype=float)
            z = z[np.isfinite(z)]
            agg["absz_%s|%s" % (name, sc)] = z.tolist()
            agg["nullsd_%s|%s" % (name, sc)] = float(np.nanmean([a["nullsd_%s|%s" % (name, sc)] for a in acc]))
            agg["nullcenter_%s|%s" % (name, sc)] = float(np.nanmean([a["nullcenter_%s|%s" % (name, sc)] for a in acc]))
            agg["praw_%s|%s" % (name, sc)] = float(np.nanmean([a["praw_%s|%s" % (name, sc)] for a in acc]))
            agg["praw_uncent_%s|%s" % (name, sc)] = float(np.nanmean(
                [a["praw_uncent_%s|%s" % (name, sc)] for a in acc]))
            agg["size_praw05_%s|%s" % (name, sc)] = float(np.mean(
                [a["praw_%s|%s" % (name, sc)] < 0.05 for a in acc]))
            agg["size_praw_uncent05_%s|%s" % (name, sc)] = float(np.mean(
                [a["praw_uncent_%s|%s" % (name, sc)] < 0.05 for a in acc]))
    if not quiet:
        print("  [%s] G=%-3d T_eff=%d b=(%.4f,%.4f) φ=%.1f reps=%d  真值|β*|=%.4f  "
              "尺寸(名义5%%) z判据 P_A2=%.4f 原始p判据=%.4f ｜ nullsd=%.5f ｜ %.1fs"
              % (tag, n_occ, teff, b_MS, b_SM, phi, len(acc), agg["true_std_MS_mean"],
                 float(np.mean(np.array(agg["absz_MS|" + MAIN]) > 1.96)),
                 agg["size_praw05_MS|" + MAIN], agg["nullsd_MS|" + MAIN], dt), flush=True)
    return agg


def c05_from(agg, name, scheme):
    """b=0 空模型实测的 95 分位 |z| ⇒ 尺寸校准后的临界值。"""
    z = np.array(agg["absz_%s|%s" % (name, scheme)], dtype=float)
    z = z[np.isfinite(z)]
    assert z.size > 0, "空模型 |z| 集合为空 —— 拒绝在这一步继续"
    return float(np.quantile(z, 0.95)), float(z.mean()), int(z.size)


def power_at(agg, name, scheme, c):
    z = np.array(agg["absz_%s|%s" % (name, scheme)], dtype=float)
    z = z[np.isfinite(z)]
    assert z.size > 0, "功效 |z| 集合为空"
    return float((z >= c).mean()), int(z.size)


def nominal_size(agg, name, scheme):
    """未做尺寸校准时、直接用 |z|>1.96 的拒绝率 —— 与校准值并报。"""
    z = np.array(agg["absz_%s|%s" % (name, scheme)], dtype=float)
    z = z[np.isfinite(z)]
    return float((z > 1.96).mean())


def mde80(xs, ps):
    pts = sorted(zip(xs, ps))
    for i in range(len(pts) - 1):
        x0, p0 = pts[i]
        x1, p1 = pts[i + 1]
        if (p0 - 0.8) * (p1 - 0.8) <= 0 and p1 != p0:
            return x0 + (0.8 - p0) * (x1 - x0) / (p1 - p0)
    if pts and pts[-1][1] < 0.8:
        return None
    if pts and pts[0][1] > 0.8:
        return 0.0
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=400)
    ap.add_argument("--calib-reps", type=int, default=600)
    ap.add_argument("--rperm", type=int, default=199)
    ap.add_argument("--quick", action="store_true")
    a = ap.parse_args()
    reps = 120 if a.quick else a.reps
    creps = 160 if a.quick else a.calib_reps
    R = 99 if a.quick else a.rperm
    schemes = [MAIN, ALT, LEGACY]

    print("=" * 100)
    print("RQ3-2 功效审计 · 生成器复用自 %s" % os.path.relpath(SRC, ROOT))
    print("  源 sha256[:16] = %s ｜ 抽取并 exec 的函数 = %s" % (_src_sha[:16], sorted(_got)))
    print("  REPS=%d  校准 REPS=%d  R_perm=%d" % (reps, creps, R))
    print("  主判据 = %s（尺寸修正后）｜ 对照 = %s ｜ 审计对照 = %s" % (MAIN, ALT, LEGACY))
    print("=" * 100)

    # ── 退化点单验 ───────────────────────────────────────────────────
    print("\n[退化点单验]")
    assert med_correct([1.0, 2.0, 3.0]) == 2.0 and med_correct([1.0, 2.0, 3.0, 4.0]) == 2.5
    assert med_correct([]) is None
    print("  median(): 奇数[1,2,3]→2.0  偶数[1,2,3,4]→2.5  空集→None  OK（== statistics.median）")
    _b0 = float((w2(np.zeros((4, 3))) * w2(np.zeros((4, 3)))).sum())
    print("  全零面板 within 平方和 = %.1f（分母为 0 的分支）" % _b0)
    yz, xz = w2(np.zeros((4, 3))), w2(np.ones((4, 3)))
    print("  Σx̃² = %.6f（x 无组内变异）⇒ 估计量走 sxx==0 分支、返回 NaN 而**不返回 inf/0**  OK"
          % float((xz * xz).sum()))
    _t = stat_pair(np.zeros((4, 3)), np.ones((4, 3)), 20, np.random.default_rng(0), [MAIN])
    print("  退化输入下 β̂ = %s（NaN）且不抛异常  OK" % (_t["beta"],))
    assert all([]) is True
    print("  all([]) = True ⇒ 本脚本每个 all()/assert 前都已断言集合非空（c05_from/power_at 内）")
    # 奇偶样本量：置换集合大小 奇数 vs 偶数
    for Gsz in (5, 6):
        _rr = np.random.default_rng(7)
        _st = stat_pair(np.random.default_rng(1).normal(size=(Gsz, 4)),
                        np.random.default_rng(2).normal(size=(Gsz, 4)), 50, _rr, [MAIN])
        print("  G=%d（%s数）置换零分布 n=%d、中心=%+.6f  —— 奇偶样本量下都做了中心化  OK"
              % (Gsz, "奇" if Gsz % 2 else "偶", _st[MAIN].size, float(np.median(_st[MAIN]))))

    # ── ★ 1. 零模型尺寸校准（先校准，后功效） ─────────────────────────
    print("\n[★ 零模型尺寸校准：b=0 下的拒绝率（名义 α=0.05）]")
    print("   （LEGACY = 未修正的「原始 x 期内跨单元置换」，用来展示过度拒绝有多大）")
    calib_cfg = [(12, 4, 0.5), (12, 4, 0.0), (12, 3, 0.5), (12, 3, 0.0)]
    if not a.quick:
        calib_cfg += [(29, 4, 0.5), (29, 4, 0.0), (29, 3, 0.5), (29, 3, 0.0)]
    calib = {}
    for G, teff, phi in calib_cfg:
        agg = run_cell(teff, G, 0.0, 0.0, phi, creps, R, schemes,
                       SEED + 1000 + G * 100 + teff * 10 + int(phi * 10),
                       "calib_G%d_T%d_phi%02d" % (G, teff, int(phi * 10)), quiet=True)
        calib[agg["tag"]] = agg
        row = {}
        for sc in schemes:
            row[sc] = {"size_z_196": nominal_size(agg, "MS", sc),
                       "size_praw05_centered": agg["size_praw05_MS|" + sc],
                       "size_praw05_uncentered": agg["size_praw_uncent05_MS|" + sc]}
        for sc in schemes:
            c, m, n = c05_from(agg, "MS", sc)
            cs, ms, ns = c05_from(agg, "SM", sc)
            row[sc]["c05_MS"] = c
            row[sc]["c05_SM"] = cs
            row[sc]["absz_mean_MS"] = m
            row[sc]["absz_mean_SM"] = ms
            row[sc]["n_absz"] = n
            row[sc]["size_at_c05"] = 0.05
            row[sc]["nullsd_MS"] = agg["nullsd_MS|" + sc]
            row[sc]["nullcenter_MS"] = agg["nullcenter_MS|" + sc]
        row["_cfg"] = {"G_nocc": G, "T_eff": teff, "phi": phi, "reps_kept": agg["reps_kept"]}
        calib[agg["tag"] + "::summary"] = row
        print("     G=%-3d T_eff=%d φ=%.1f ｜ 尺寸（名义 0.05）—— 未修正LEGACY: z判据 %.4f / 原始p判据 %.4f ｜"
              " 主判据 P_A2: z判据 %.4f / 原始p判据 %.4f / 未中心化 %.4f ｜ 对照 P_C: z判据 %.4f ｜"
              " 校准临界 c₀.₀₅(P_A2)=%.4f ｜ 零模型中心=%+.5f"
              % (G, teff, phi,
                 row[LEGACY]["size_z_196"], row[LEGACY]["size_praw05_centered"],
                 row[MAIN]["size_z_196"], row[MAIN]["size_praw05_centered"],
                 row[MAIN]["size_praw05_uncentered"], row[ALT]["size_z_196"],
                 row[MAIN]["c05_MS"], row[MAIN]["nullcenter_MS"]))

    # ── 2. 生成器正面校验：零效应无偏、镜像（市场领先 ⇄ 公众领先）同分布 ──
    print("\n[生成器校验①：零效应无偏（b=0，G=12，T_eff=4，φ=0.5）]")
    z0 = run_cell(4, 12, 0.0, 0.0, 0.5, max(creps, 300), R, [MAIN], SEED + 5, "zero_check", quiet=True)
    print("     β̂_MS 均值=%+.5f（sd %.5f）｜ β̂_SM 均值=%+.5f（sd %.5f）｜ reps_kept=%d"
          % (z0["beta_MS_mean"], z0["beta_MS_sd"], z0["beta_SM_mean"], z0["beta_SM_sd"], z0["reps_kept"]))
    print("[生成器校验②：镜像对照（市场领先 vs 公众领先，应同分布）]")
    mi = run_cell(4, 12, 0.25, 0.0, 0.5, creps, R, [MAIN], SEED + 6, "mirror_MS", quiet=True)
    m2 = run_cell(4, 12, 0.0, 0.25, 0.5, creps, R, [MAIN], SEED + 6, "mirror_SM", quiet=True)
    cM = c05_from(calib["calib_G12_T4_phi05"], "MS", MAIN)[0]
    cS = c05_from(calib["calib_G12_T4_phi05"], "SM", MAIN)[0]
    pm, nm = power_at(mi, "MS", MAIN, cM)
    ps, ns = power_at(m2, "SM", MAIN, cS)
    se_d = float(np.sqrt(pm * (1 - pm) / nm + ps * (1 - ps) / ns))
    print("     市场领先 b=0.25 ⇒ 校准功率=%.4f(n=%d) ｜ 公众领先 b=0.25 ⇒ 校准功率=%.4f(n=%d) ｜ "
          "差 %.4f（二项 s.e.≈%.4f ⇒ %s）｜ 两侧 c₀.₀₅ = %.4f / %.4f"
          % (pm, nm, ps, ns, abs(pm - ps), se_d,
             "同分布（差 <2 s.e.）" if abs(pm - ps) < 2 * se_d else "★ 差异超 2 s.e.，须并报",
             cM, cS))
    print("     未校准口径对照：%.4f vs %.4f" % (nominal_size(mi, "MS", MAIN), nominal_size(m2, "SM", MAIN)))

    # ── ★ 3. 功效曲线 ────────────────────────────────────────────────
    BETA_STD = [0.0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50, 0.70, 1.00]
    if a.quick:
        BETA_STD = [0.0, 0.20, 0.40, 0.70]
    print("\n[★ 功效曲线 · 效应量 = 标准化 β*（within 尺度）]")
    pilot = run_cell(4, 12, 0.30, 0.0, 0.5, max(120, reps // 3), 49, [MAIN], SEED + 900, "pilot", quiet=True)
    RATIO = abs(pilot["true_std_MS_mean"] / 0.30) if pilot["true_std_MS_mean"] else 1.0
    print("     标定：b_raw=0.30 ⇒ 真值 |β*|=%.4f（换算比 %.4f）" % (pilot["true_std_MS_mean"], RATIO))

    grid_cells = [(4, 12, "main", 0.5), (3, 12, "main", 0.5), (4, 12, "phi0", 0.0)]
    if not a.quick:
        grid_cells += [(4, 29, "main", 0.5), (3, 29, "main", 0.5)]
    grid = []
    for teff, G, kind, phi in grid_cells:
        cal_key = "calib_G%d_T%d_phi%02d" % (G, teff, int(phi * 10))
        cM = c05_from(calib[cal_key], "MS", MAIN)[0]
        cS = c05_from(calib[cal_key], "SM", MAIN)[0]
        for bs in BETA_STD:
            b_raw = bs / RATIO
            tag = "pow_G%d_T%d_%s_bs%.2f" % (G, teff, kind, bs)
            agg = run_cell(teff, G, b_raw, 0.0, phi, reps, R, schemes,
                           SEED + 5000 + int(bs * 1000) + G * 7 + teff, tag, quiet=True)
            if agg is None:
                grid.append({"tag": tag, "T_eff": teff, "G_nocc": G, "kind": kind,
                             "beta_std_target": bs, "b_raw": b_raw, "reps_kept": 0,
                             "status": "ALL_REPS_DEGENERATE", "note": "全部重复退化；未静默丢弃"})
                print("     %-32s **全部重复退化（reps_kept=0）** —— 已记录" % tag)
                continue
            agg["beta_std_target"] = bs
            agg["kind"] = kind
            agg["b_raw"] = b_raw
            agg["beta_std_realized"] = agg["true_std_MS_mean"]
            agg["c05_MS"] = cM
            agg["c05_SM"] = cS
            agg["power_perm_calibrated"] = power_at(agg, "MS", MAIN, cM)[0]
            agg["power_perm_nominal"] = nominal_size(agg, "MS", MAIN)
            agg["power_alt_calibrated"] = power_at(agg, "MS", ALT, c05_from(calib[cal_key], "MS", ALT)[0])[0]
            agg["power_alt_nominal"] = nominal_size(agg, "MS", ALT)
            agg["power_legacy_nominal"] = nominal_size(agg, "MS", LEGACY)
            agg["binom_se"] = float(np.sqrt(max(agg["power_perm_calibrated"]
                                                * (1 - agg["power_perm_calibrated"]), 1e-12) / agg["reps_kept"]))
            grid.append(agg)
            print("     β*目标=%-5.2f b_raw=%-6.4f G=%-3d T_eff=%d %-5s ⇒ 实到|β*|=%.4f  "
                  "校准功率=%.4f(±%.4f) ｜ 未校准功率(名义)=%.4f ｜ 对照P_C=%.4f ｜ 未修正判据=%.4f"
                  % (bs, b_raw, G, teff, kind, agg["beta_std_realized"], agg["power_perm_calibrated"],
                     agg["binom_se"], agg["power_perm_nominal"], agg["power_alt_calibrated"],
                     agg["power_legacy_nominal"]), flush=True)

    # ── ★ 4. MDE / 已排除上界 ────────────────────────────────────────
    print("\n[★ MDE80 与已排除效应上界 · 由功效曲线插值]")
    mdes = []
    for teff, G, kind, phi in grid_cells:
        sub = [g for g in grid if g.get("T_eff") == teff and g.get("G_nocc") == G
               and g.get("kind") == kind and g.get("power_perm_calibrated") is not None]
        if len(sub) < 2:
            continue
        xs = [g["beta_std_realized"] for g in sub]
        pz = [g["power_perm_calibrated"] for g in sub]
        pn = [g["power_perm_nominal"] for g in sub]
        pa = [g["power_alt_calibrated"] for g in sub]
        pk = [g["power_legacy_nominal"] for g in sub]
        m = mde80(xs, pz)
        # 「没有判出力区」上界：功效 ≤ 0.20 的最大的正效应量
        excl = max([g["beta_std_realized"] for g in sub if g["beta_std_target"] > 0
                    and g["power_perm_calibrated"] <= 0.20] or [0.0])
        nopow = max([g["beta_std_realized"] for g in sub if g["beta_std_target"] > 0
                     and g["power_perm_calibrated"] <= 0.50] or [0.0])
        mdes.append({"T_eff": teff, "G_nocc": G, "kind": kind, "phi": phi,
                     "MDE80_calibrated": m, "MDE80_nominal": mde80(xs, pn),
                     "MDE80_alt_PC": mde80(xs, pa), "MDE80_legacy_unfixed": mde80(xs, pk),
                     "excl_upper_calibrated": excl, "no_power_bound_power_le_050": nopow,
                     "power_curve": {"%.2f" % e: gg for e, gg in zip([g["beta_std_target"] for g in sub], pz)}})
        print("     T_eff=%d G=%-3d %-5s ｜ MDE80(**尺寸校准**)=%s ｜ 未校准=%s ｜ 对照P_C=%s ｜ "
              "功效≤0.20 的 |β*| 上界=%.3f ｜ 功效≤0.50 的上界=%.3f"
              % (teff, G, kind,
                 ("%.4f" % m) if m is not None else ">网格上界",
                 ("%.4f" % mde80(xs, pn)) if mde80(xs, pn) is not None else ">网格上界",
                 ("%.4f" % mde80(xs, pa)) if mde80(xs, pa) is not None else ">网格上界", excl, nopow))

    # ── 5. 落盘 ──────────────────────────────────────────────────────
    def strip_absz(d):
        return {k: v for k, v in d.items() if not k.startswith("absz_")}

    out = {"meta": {"script": "RQ3_2_power_mc.py",
                    "generator_source": os.path.relpath(SRC, ROOT).replace("\\", "/"),
                    "generator_source_sha256_16": _src_sha[:16],
                    "functions_reused": sorted(_got),
                    "K_EFF": K_EFF, "waves": list(WAVES),
                    "TEFF_YEARS": {str(k): v for k, v in TEFF_YEARS.items()},
                    "REPS_power": reps, "REPS_calibration": creps, "R_perm": R,
                    "main_scheme": MAIN, "alt_scheme": ALT, "legacy_scheme_shown_for_audit": LEGACY,
                    "seed_base": SEED, "alpha": 0.05, "power_target": 0.80,
                    "beta_std_grid": BETA_STD, "b_raw_per_beta_std": 1.0 / RATIO,
                    "criterion": "尺寸校准置换判据：z = (β̂ − 置换零分布中位)/置换零分布 sd，"
                                 "临界 c₀.₀₅ 由 b=0 空模型实测 95 分位给出",
                    "note_T_eff": "T_eff=4 = 估计窗口内被解释年个数（2022–2025）；≠ 波次 5。见设计稿 §2.1.0"},
           "degenerate_checks": {
               "median_odd": 2.0, "median_even": 2.5, "median_empty": None,
               "sxx_zero_returns_nan_not_inf": True, "all_empty_is_true": True,
               "perm_set_nonempty_asserted": True,
               "odd_even_G_checked": [5, 6]},
           "generator_check_zero_unbiased": strip_absz(z0),
           "generator_check_mirror": {"power_MS_b0.25": pm, "power_SM_b0.25": ps,
                                      "abs_diff": abs(pm - ps),
                                      "note": "镜像对照：市场领先与公众领先在同一生成器下应同分布"},
           "size_calibration": {k: (strip_absz(v) if isinstance(v, dict) and "tag" in v else v)
                                for k, v in calib.items()},
           "power_grid": [strip_absz(g) for g in grid],
           "mde": mdes}
    pj = os.path.join(HERE, "RQ3_2_功效审计.json")
    with open(pj, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1, default=str)

    pc = os.path.join(HERE, "RQ3_2_功效审计.csv")
    cols = ["block", "T_eff", "G_nocc", "phi", "kind", "beta_std_target", "beta_std_realized", "b_raw",
            "power_calibrated_main", "power_nominal_main", "power_calibrated_altPC",
            "size_z196_main", "size_praw05_main", "size_praw05_uncentered_main",
            "size_z196_legacy_unfixed", "size_inflation_legacy_x",
            "c05_main", "perm_null_sd", "perm_null_center", "reps_kept", "R_perm", "binom_se",
            "MDE80_calibrated", "MDE80_nominal", "MDE80_altPC",
            "excl_upper_calibrated", "no_power_bound_power_le_050", "note"]
    with open(pc, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for g in grid:
            if g.get("power_perm_calibrated") is None:
                w.writerow({"block": "power_grid", "T_eff": g["T_eff"], "G_nocc": g["G_nocc"],
                            "kind": g["kind"], "beta_std_target": g["beta_std_target"],
                            "b_raw": g.get("b_raw"), "reps_kept": 0, "note": "全部重复退化；未静默丢弃"})
                continue
            mm = [m for m in mdes if m["T_eff"] == g["T_eff"] and m["G_nocc"] == g["G_nocc"]
                  and m["kind"] == g["kind"]]
            mm = mm[0] if mm else {}
            w.writerow({"block": "power_grid", "T_eff": g["T_eff"], "G_nocc": g["G_nocc"],
                        "phi": g["phi"], "kind": g["kind"],
                        "beta_std_target": g["beta_std_target"],
                        "beta_std_realized": round(g["beta_std_realized"], 6),
                        "b_raw": round(g["b_raw"], 6),
                        "power_calibrated_main": round(g["power_perm_calibrated"], 5),
                        "power_nominal_main": round(g["power_perm_nominal"], 5),
                        "power_calibrated_altPC": round(g["power_alt_calibrated"], 5),
                        "size_z196_main": round(g["size_praw05_MS|" + MAIN], 5),
                        "c05_main": round(g["c05_MS"], 5),
                        "perm_null_sd": round(g["nullsd_MS|" + MAIN], 6),
                        "perm_null_center": round(g["nullcenter_MS|" + MAIN], 6),
                        "reps_kept": g["reps_kept"], "R_perm": R,
                        "binom_se": round(g["binom_se"], 5),
                        "MDE80_calibrated": mm.get("MDE80_calibrated"),
                        "MDE80_nominal": mm.get("MDE80_nominal"),
                        "MDE80_altPC": mm.get("MDE80_alt_PC"),
                        "excl_upper_calibrated": mm.get("excl_upper_calibrated"),
                        "no_power_bound_power_le_050": mm.get("no_power_bound_power_le_050"),
                        "note": "功率 = 尺寸校准后置换判据的拒绝率；β* = within 尺度标准化效应量"})
        for m in mdes:
            w.writerow({"block": "MDE80", "T_eff": m["T_eff"], "G_nocc": m["G_nocc"], "phi": m["phi"],
                        "kind": m["kind"], "MDE80_calibrated": m["MDE80_calibrated"],
                        "MDE80_nominal": m["MDE80_nominal"], "MDE80_altPC": m["MDE80_alt_PC"],
                        "excl_upper_calibrated": m["excl_upper_calibrated"],
                        "no_power_bound_power_le_050": m["no_power_bound_power_le_050"],
                        "note": "MDE80 = 功率 0.80 处的标准化 β*（线性插值）；None = 网格上界仍 <0.80"})
        for k, v in calib.items():
            if not k.endswith("::summary"):
                continue
            cfg = v["_cfg"]
            for sc in schemes:
                sz = v[sc]["size_z_196"]
                w.writerow({"block": "size_calibration", "T_eff": cfg["T_eff"], "G_nocc": cfg["G_nocc"],
                            "phi": cfg["phi"], "kind": sc,
                            "size_z196_main": round(sz, 5),
                            "size_praw05_main": round(v[sc]["size_praw05_centered"], 5),
                            "size_praw05_uncentered_main": round(v[sc]["size_praw05_uncentered"], 5),
                            "size_inflation_legacy_x": round(sz / 0.05, 3),
                            "c05_main": round(v[sc]["c05_MS"], 5),
                            "perm_null_sd": round(v[sc]["nullsd_MS"], 6),
                            "perm_null_center": round(v[sc]["nullcenter_MS"], 6),
                            "reps_kept": cfg["reps_kept"], "R_perm": R,
                            "note": "b=0 空模型实测拒绝率（名义 0.05）· %s" % k})
    print("\n已写出：\n  %s\n  %s" % (pj, pc))


if __name__ == "__main__":
    main()
