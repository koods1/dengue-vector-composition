"""Why do cell-months stop being suitable under warming?

mechanism.py answers this for the baseline: which cell-months are unsuitable
now, and why. This answers the question the Methods actually raise, which is
about *change*: of the cell-months that are suitable in 2005-2014 and
unsuitable by 2086-2095, how many are lost to heat and how many to rainfall
washout? The two have different policy readings, so they should not be
reported as one number.

Classification follows mechanism.py. For a given rainfall the niche admits a
thermal window, and for a given temperature a rainfall window; an unsuitable
cell-month is attributed to whichever bound it violates.
"""
import sys
import numpy as np

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

SCEN = ['ssp126', 'ssp245', 'ssp585']

nz = np.load('niche_python.npz')
nT, nR, MED = nz['T'], nz['R'], nz['MedianM']

TLIM = np.full((nR.size, 2), np.nan)
for j in range(nR.size):
    c = np.where(MED[:, j] > 0)[0]
    if c.size:
        TLIM[j] = (nT[c[0]], nT[c[-1]])
RLIM = np.full((nT.size, 2), np.nan)
for i in range(nT.size):
    c = np.where(MED[i, :] > 0)[0]
    if c.size:
        RLIM[i] = (nR[c[0]], nR[c[-1]])

dT, dR = nT[1] - nT[0], nR[1] - nR[0]


def idx(v, ax, d):
    return np.clip(np.round((v - ax[0]) / d).astype(int), 0, ax.size - 1)


def suitable(T, R):
    ok = (T >= nT[0]) & (T <= nT[-1]) & (R >= nR[0]) & (R <= nR[-1])
    return ok & (MED[idx(np.nan_to_num(T), nT, dT),
                     idx(np.nan_to_num(R), nR, dR)] > 0)


def classify(T, R):
    """Return arrays of booleans: too cold, too hot, too wet, too dry."""
    j = idx(np.clip(R, nR[0], nR[-1]), nR, dR)
    i = idx(np.clip(T, nT[0], nT[-1]), nT, dT)
    tlo, thi = TLIM[j, 0], TLIM[j, 1]
    rlo, rhi = RLIM[i, 0], RLIM[i, 1]
    cold = np.isfinite(tlo) & (T < tlo)
    hot = np.isfinite(thi) & (T > thi)
    wet = np.isfinite(rhi) & (R > rhi) & ~cold & ~hot
    dry = np.isfinite(rlo) & (R < rlo) & ~cold & ~hot
    # rainfall outside the tabulated range entirely
    wet |= (~np.isfinite(rhi)) & (R > nR[-1] / 2) & ~cold & ~hot
    return cold, hot, wet, dry


z = np.load('ensemble_monthly.npz')
MODELS = sorted({k.split('__')[0] for k in z.files if k not in ('lat', 'lon')})
print(f'{len(MODELS)} models x {len(SCEN)} scenarios, median Kaye niche\n')

rows = {}
for scen in SCEN:
    tot = cold = hot = wet = dry = other = 0
    for m in MODELS:
        Th = z[f'{m}__historical__tas'] - 273.15
        Rh = z[f'{m}__historical__pr'] * 86400.0
        Tf = z[f'{m}__{scen}__tas'] - 273.15
        Rf = z[f'{m}__{scen}__pr'] * 86400.0
        for mo in range(12):
            good = np.isfinite(Th[mo]) & np.isfinite(Tf[mo])
            lost = good & suitable(Th[mo], Rh[mo]) & ~suitable(Tf[mo], Rf[mo])
            if not lost.any():
                continue
            c, h, w, d = classify(Tf[mo][lost], Rf[mo][lost])
            n = int(lost.sum())
            tot += n
            cold += int(c.sum()); hot += int(h.sum())
            wet += int(w.sum()); dry += int(d.sum())
            other += n - int(c.sum() + h.sum() + w.sum() + d.sum())
    rows[scen] = (tot, cold, hot, wet, dry, other)

print('Cell-months suitable in 2005-2014 and unsuitable by 2086-2095,')
print('attributed to the bound they violate (summed over 8 models):\n')
print(f"{'scenario':<10}{'lost':>10}{'too hot':>12}{'washout':>12}"
      f"{'too cold':>11}{'too dry':>10}{'other':>8}")
print('-' * 73)
for scen in SCEN:
    tot, cold, hot, wet, dry, other = rows[scen]
    if tot == 0:
        print(f'{scen:<10}{0:>10}')
        continue
    print(f'{scen:<10}{tot:>10,}'
          f'{100*hot/tot:>11.1f}%{100*wet/tot:>11.1f}%'
          f'{100*cold/tot:>10.1f}%{100*dry/tot:>9.1f}%{100*other/tot:>7.1f}%')

print('\nInterpretation. The Methods state that in monsoon Asia washout is')
print('likely the more common contraction mechanism. This tests that claim')
print('directly for the study region under the CMIP6 ensemble.')
