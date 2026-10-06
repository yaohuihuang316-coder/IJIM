"""Exact six source functions, no top-level legacy simulation."""
import numpy as np
import pandas as pd
YRS_EST=[2022,2023,2024,2025]

def make_stacked(panel, occs):
    m = panel.set_index(["occ", "year"])["M"]
    s = panel.set_index(["occ", "year"])["S"]
    rows = []
    for occ in occs:
        for t in YRS_EST:
            rows.append(dict(occ=occ, year=t, d=0, y=s.get((occ, t), np.nan), x=m.get((occ, t - 1), np.nan)))
            rows.append(dict(occ=occ, year=t, d=1, y=m.get((occ, t), np.nan), x=s.get((occ, t - 1), np.nan)))
    st = pd.DataFrame(rows).dropna(subset=["y", "x"]).reset_index(drop=True)
    st["x_side"] = st["x"] * st["d"]; st["side"] = st["d"].astype(float)
    st["occ"] = st["occ"].astype(str)
    st["occ_lay"] = st["occ"] + "|" + st["d"].astype(str)
    return st

def design_raw(st, mode):
    n = len(st); d = st["d"].to_numpy(float); yv = st["year"].to_numpy()
    if mode == "shared":
        X = np.zeros((n, 3 + len(YRS_EST) - 1))
        X[:, 0] = st["x"]; X[:, 1] = st["x_side"]; X[:, 2] = d
        for j, y in enumerate(YRS_EST[1:]):
            X[:, 3 + j] = (yv == y).astype(float)
    else:
        X = np.zeros((n, 2 + 2 * (len(YRS_EST) - 1)))
        X[:, 0] = st["x"]; X[:, 1] = st["x_side"]
        for j, y in enumerate(YRS_EST[1:]):
            m_ = (yv == y).astype(float)
            X[:, 2 + j] = m_ * (1 - d); X[:, 2 + len(YRS_EST) - 1 + j] = m_ * d
    return X

def demean(Z, groups):
    Zd = Z.copy()
    for g in np.unique(groups):
        m = groups == g
        Zd[m] -= Z[m].mean(axis=0)
    return Zd

def prepare(st, mode, k_eff):
    d = st["d"].to_numpy()
    grp_fe = st["occ"].to_numpy() if mode == "shared" else st["occ_lay"].to_numpy()
    Xd = demean(design_raw(st, mode), grp_fe)
    yd = demean(st["y"].to_numpy(float).reshape(-1, 1), grp_fe).ravel()
    grp = st["occ"].to_numpy(); occs = np.array(sorted(set(grp)))
    A0, A1, b0, b1 = [], [], [], []
    for o in occs:
        for lay, AL, bL in [(0, A0, b0), (1, A1, b1)]:
            m = (grp == o) & (d == lay)
            AL.append(Xd[m].T @ Xd[m]); bL.append(Xd[m].T @ yd[m])
    return dict(Xd=Xd, yd=yd, grp=grp, occs=occs, A0=np.stack(A0), A1=np.stack(A1),
                b0=np.stack(b0), b1=np.stack(b1)), k_eff

def crv1(Xd, resid, groups, k_eff):
    n, k = Xd.shape
    xtx = np.linalg.pinv(Xd.T @ Xd); meat = np.zeros((k, k))
    for g in np.unique(groups):
        m_ = groups == g; sg = Xd[m_].T @ resid[m_]; meat += np.outer(sg, sg)
    G = len(np.unique(groups))
    return (G / (G - 1.0)) * ((n - 1.0) / (n - k_eff)) * (xtx @ meat @ xtx)

def sim(b_ms, b_sm, phi, rng, n_occ=29, years=(2021, 2022, 2023, 2024, 2025)):
    n = n_occ
    a, m_ = rng.normal(0, 1, n), rng.normal(0, 1, n)
    h = {y: rng.normal(0, .3) for y in years}; g = {y: rng.normal(0, .3) for y in years}
    u, v = rng.normal(0, 1, n), rng.normal(0, 1, n)
    Sp, Mp = a + rng.normal(0, 1, n), m_ + rng.normal(0, 1, n)
    S = np.zeros((n, len(years))); M = np.zeros((n, len(years)))
    for j, y in enumerate(years):
        v = phi * v + rng.normal(0, 1, n); u = phi * u + rng.normal(0, 1, n)
        S[:, j] = a + h[y] + b_ms * Mp
        M[:, j] = m_ + g[y] + b_sm * Sp
        S[:, j] += v; M[:, j] += u
        Sp, Mp = S[:, j], M[:, j]
    return pd.DataFrame(dict(occ=np.tile(np.array(["o%02d" % i for i in range(n)]), len(years)),
                             year=np.repeat(np.array(years), n), S=S.T.ravel(), M=M.T.ravel()))
