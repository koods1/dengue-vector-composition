"""Quantitative niche validation against two independent location sets that
Kaye et al. used graphically (their Figure S7):

  Kraemer locations       - places where Ae. aegypti has been observed
  Liu outbreak locations  - places where DENGUE OUTBREAKS have occurred

The second matters because it tests the niche against transmission rather
than vector presence, which is the gap our limitations section names.

Also compares the Kaye niche against the Liu-Helmersson alternative
parameterisation, one of the pre-specified sensitivity analyses.
"""
import csv, sys
import numpy as np
from scipy.io import loadmat
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def load_niche(path):
    d = loadmat(path)
    T = d['Temperatures'].ravel(); R = d['Rainfalls'].ravel()
    out = {}
    for k, lab in (('SmallestM', '2.5th'), ('MedianM', 'median'),
                   ('BiggestM', '97.5th')):
        if k in d:
            out[lab] = d[k]
    return T, R, out

def inside(T, R, grid, nT, nR):
    dT = nT[1] - nT[0]; dR = nR[1] - nR[0]
    ok = (T >= nT[0]) & (T <= nT[-1]) & (R >= nR[0]) & (R <= nR[-1])
    i = np.clip(np.round((np.nan_to_num(T) - nT[0]) / dT).astype(int), 0, nT.size - 1)
    j = np.clip(np.round((np.nan_to_num(R) - nR[0]) / dR).astype(int), 0, nR.size - 1)
    return ok & (grid[i, j] > 0)

def read_locs(path):
    rows = []
    for r in csv.DictReader(open(path, encoding='utf8-sig' if False else 'utf8')):
        try:
            rows.append((r['location'], float(r['T']), float(r['R'])))
        except (KeyError, ValueError, TypeError):
            continue
    return rows

kra = read_locs('niches/KraemerMosquitoLocations.csv')
liu = read_locs('niches/LiuDengueOutbreakLocations.csv')
print(f'Kraemer vector-occurrence locations : {len(kra)}')
print(f'Liu dengue-outbreak locations       : {len(liu)}\n')

nT, nR, KAYE = load_niche('MLookupTable.mat')
print('=== Kaye et al. niche ===')
print(f"{'location set':<28}{'2.5th':>9}{'median':>9}{'97.5th':>9}")
print('-' * 55)
for lab, rows in (('Ae. aegypti occurrence', kra), ('dengue outbreaks', liu)):
    T = np.array([r[1] for r in rows]); R = np.array([r[2] for r in rows])
    cells = []
    for v in ('2.5th', 'median', '97.5th'):
        ins = inside(T, R, KAYE[v], nT, nR)
        cells.append(f'{100 * ins.mean():>8.1f}%')
    print(f'{lab:<28}' + ''.join(cells))

print('\nLocations OUTSIDE the median niche:')
for lab, rows in (('occurrence', kra), ('outbreak', liu)):
    T = np.array([r[1] for r in rows]); R = np.array([r[2] for r in rows])
    ins = inside(T, R, KAYE['median'], nT, nR)
    out = [(rows[k][0], T[k], R[k]) for k in np.where(~ins)[0]]
    print(f'  {lab}: {len(out)} of {len(rows)}')
    for nm, t, r in out[:8]:
        print(f'     {nm[:38]:38s} T={t:5.1f}  R={r:5.2f}')

# ---- alternative parameterisation -----------------------------------
try:
    nT2, nR2, LH = load_niche('niches/LiuHelmersson_MLookupTable.mat')
    print('\n=== Liu-Helmersson alternative parameterisation ===')
    print(f'  grid {nT2.size} x {nR2.size}, variants available: {list(LH)}')
    key = 'median' if 'median' in LH else list(LH)[0]
    for lab, rows in (('Ae. aegypti occurrence', kra), ('dengue outbreaks', liu)):
        T = np.array([r[1] for r in rows]); R = np.array([r[2] for r in rows])
        ins = inside(T, R, LH[key], nT2, nR2)
        print(f'  {lab:<26} inside: {100 * ins.mean():.1f}%')
    a_k = (KAYE['median'] > 0).mean()
    a_l = (LH[key] > 0).mean()
    print(f'\n  niche area, fraction of the T-R grid admitted:')
    print(f'    Kaye median          {a_k:.4f}')
    print(f'    Liu-Helmersson       {a_l:.4f}  ({a_l / a_k:.2f}x Kaye)')
except Exception as e:
    print(f'\nLiu-Helmersson comparison failed: {type(e).__name__}: {e}')
