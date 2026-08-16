"""A. Baseline validation of the suitability surface against observed
Ae. aegypti occurrence (Kraemer et al. compendium via GBIF), for the study
region. Presence-background evaluation: the compendium is presence-only,
so 'specificity' is relative to random land background, not true absence.
"""
import csv, sys
import numpy as np
from netCDF4 import Dataset
from scipy.io import loadmat
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

DAYS = np.array([31, 28.25, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])
lk = loadmat('MLookupTable.mat')
nT, nR = lk['Temperatures'].ravel(), lk['Rainfalls'].ravel()
dT, dR = nT[1] - nT[0], nR[1] - nR[0]
VAR = {'2.5th pct': lk['SmallestM'], 'median': lk['MedianM'], '97.5th pct': lk['BiggestM']}

a = Dataset('air.mon.v501.ltm.1981-2010.nc'); p = Dataset('precip.mon.v501.ltm.1981-2010.nc')
lat = a.variables['lat'][:].astype(float); lon = a.variables['lon'][:].astype(float)
T = np.ma.filled(a.variables['air'][:].astype(float), np.nan)
P = np.ma.filled(p.variables['precip'][:].astype(float), np.nan)
R = (P * 10.0) / DAYS[:, None, None]
lon360 = lon.copy()

def months(M):
    ok = lambda t, r: ((t >= nT[0]) & (t <= nT[-1]) & (r >= nR[0]) & (r <= nR[-1]))
    out = np.zeros(T.shape[1:], float)
    for m in range(12):
        t, r = T[m], R[m]
        i = np.clip(np.round((np.nan_to_num(t) - nT[0]) / dT).astype(int), 0, nT.size - 1)
        j = np.clip(np.round((np.nan_to_num(r) - nR[0]) / dR).astype(int), 0, nR.size - 1)
        out += (ok(t, r) & (M[i, j] > 0))
    out[~np.isfinite(T[0])] = np.nan
    return out

SM = {k: months(M) for k, M in VAR.items()}
land = np.isfinite(T[0])

def cell(la, lo):
    lo = lo % 360
    i = int(np.argmin(np.abs(lat - la))); j = int(np.argmin(np.abs(lon360 - lo)))
    return i, j

occ = [(float(r['lat']), float(r['lon'])) for r in
       csv.DictReader(open('aegypti_occ_region.csv', encoding='utf8'))]
idx = [cell(la, lo) for la, lo in occ]
idx = [(i, j) for i, j in idx if land[i, j]]
print(f'occurrence records in region: {len(occ)}; on land grid: {len(idx)}')

rng = np.random.default_rng(0)
li, lj = np.where(land & (lat[:, None] >= -12) & (lat[:, None] <= 38)
                  & (((lon360 % 360 >= 66) & (lon360 % 360 <= 142))[None, :]))
pick = rng.choice(len(li), size=min(20000, len(li) * 4), replace=True)
bg = [(li[k], lj[k]) for k in pick]
print(f'background land cells sampled: {len(bg)} from {len(li)} unique cells\n')

def auc(pos, neg):
    allv = np.concatenate([pos, neg])
    order = np.argsort(allv, kind='mergesort')
    ranks = np.empty_like(order, dtype=float)
    ranks[order] = np.arange(1, allv.size + 1)
    # average ranks for ties
    s = np.sort(allv); i = 0
    while i < s.size:
        j = i
        while j + 1 < s.size and s[j + 1] == s[i]:
            j += 1
        if j > i:
            m = (i + j) / 2 + 1
            ranks[np.isin(allv, s[i])] = m
        i = j + 1
    rp = ranks[:pos.size].sum()
    return (rp - pos.size * (pos.size + 1) / 2) / (pos.size * neg.size)

print(f"{'niche':<12}{'sens(>=1mo)':>13}{'mean mo occ':>13}{'mean mo bg':>12}{'AUC':>7}")
print('-' * 58)
res = {}
for k in VAR:
    sm = SM[k]
    po = np.array([sm[i, j] for i, j in idx])
    bo = np.array([sm[i, j] for i, j in bg])
    sens = (po >= 1).mean()
    res[k] = (sens, po.mean(), bo.mean(), auc(po, bo))
    print(f'{k:<12}{sens * 100:>12.1f}%{po.mean():>13.2f}{bo.mean():>12.2f}{res[k][3]:>7.3f}')

print('\nWhere the median niche fails: occurrence points in cells with 0 suitable months')
sm = SM['median']
fails = [(la, lo) for (la, lo), (i, j) in
         zip([o for o in occ], [cell(*o) for o in occ])
         if land[i, j] and sm[i, j] == 0]
print(f'  {len(fails)} of {len(idx)} points ({100 * len(fails) / len(idx):.1f}%)')
if fails:
    fa = np.array(fails)
    print(f'  latitude range  {fa[:,0].min():.1f} to {fa[:,0].max():.1f}')
    print(f'  longitude range {fa[:,1].min():.1f} to {fa[:,1].max():.1f}')
    # why do they fail?
    hot = wet = cold = 0
    for la, lo in fails:
        i, j = cell(la, lo)
        t = T[:, i, j]; r = R[:, i, j]
        if np.nanmax(r) > 18.6: wet += 1
        elif np.nanmin(t) < 17: cold += 1
        elif np.nanmax(t) > 34: hot += 1
    print(f'  of these: {wet} have a month above the washout ceiling, '
          f'{cold} a month below 17 C, {hot} a month above 34 C')
