"""Compare five-year against ten-year averaging windows.

Reads the per-file-year monthly reductions written by window_length.py and
recomputes suitable months per country under three definitions of each
window: the first five years, the second five years, and the full decade.
The quantity the paper reports is the CHANGE between windows, so that is what
is compared; the spread between the two five-year halves is the part of the
estimate attributable to sampling rather than to forcing.
"""
import sys, itertools
import numpy as np
import geopandas as gpd
from shapely.geometry import Point
from scipy.io import loadmat

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

CS = ['Malaysia', 'Indonesia', 'Thailand', 'Philippines', 'Vietnam', 'India',
      'Bangladesh', 'Cambodia', 'Sri Lanka', 'Singapore']
NF = {'Vietnam': ['Vietnam', 'Viet Nam']}
LBL = {'Vietnam': 'Viet Nam'}

z = np.load('wlen_monthly.npz')
files = list(z.files)


def years(scen):
    out = {}
    for f in files:
        if f'_{scen}_' not in f:
            continue
        y = int(f.rsplit('_', 2)[-2])
        out.setdefault(y, {})['tas' if f.startswith('tas') else 'pr'] = f
    return out


HIST, FUT = years('historical'), years('ssp585')
print(f'historical years {min(HIST)}-{max(HIST)}, ssp585 {min(FUT)}-{max(FUT)}')

# grid comes from the full-ensemble reduction, which used the same subset
ref = np.load('ensemble_monthly.npz')
LA, LO = ref['lat'], ref['lon']
land = np.isfinite(ref[f'GFDL-ESM4__historical__tas'][0])

world = gpd.read_file('ne10_adm1.geojson')
LOg, LAg = np.meshgrid(LO, LA)
pts = gpd.GeoDataFrame(geometry=[Point(x, y) for x, y in
                                 zip(LOg.ravel(), LAg.ravel())], crs=world.crs)
jn = gpd.sjoin(pts, world[['admin', 'geometry']], how='left', predicate='within')
jn = jn[~jn.index.duplicated(keep='first')]
cname = jn['admin'].values.reshape(LOg.shape)
MASK = {c: (np.isin(cname, NF.get(c, [c])) & land) for c in CS}
Wt = np.cos(np.deg2rad(LA))[:, None] * np.ones((1, LO.size))

kaye = loadmat('MLookupTable.mat')
kT, kR = kaye['Temperatures'].ravel(), kaye['Rainfalls'].ravel()
dT, dR = kT[1] - kT[0], kR[1] - kR[0]
MED = kaye['MedianM']


def aeg(T, R):
    ok = (T >= kT[0]) & (T <= kT[-1]) & (R >= kR[0]) & (R <= kR[-1])
    i = np.clip(np.round((np.nan_to_num(T) - kT[0]) / dT).astype(int), 0, kT.size - 1)
    j = np.clip(np.round((np.nan_to_num(R) - kR[0]) / dR).astype(int), 0, kR.size - 1)
    return ok & (MED[i, j] > 0)


def albo(T, R):
    return np.isfinite(T) & (T >= 16.2) & (T <= 31.6)      # Mordecai band


def months(yrs, table, fn):
    """Suitable months averaged over the given years."""
    T = np.nanmean([z[table[y]['tas']] for y in yrs], axis=0) - 273.15
    R = np.nanmean([z[table[y]['pr']] for y in yrs], axis=0) * 86400.0
    return sum(fn(T[m], R[m]) for m in range(12)).astype(float)


DEFS = {'first 5': lambda t: sorted(t)[:5],
        'last 5':  lambda t: sorted(t)[5:],
        'full 10': lambda t: sorted(t)}

for name, fn in (('Ae. aegypti (Kaye median)', aeg),
                 ('Ae. albopictus (Mordecai)', albo)):
    print(f'\n=== {name}: change in suitable months, 2005-2014 to 2086-2095 ===')
    print(f"{'country':<13}" + ''.join(f'{d:>10}' for d in DEFS)
          + f"{'half-spread':>13}")
    print('-' * 62)
    ch = {d: {} for d in DEFS}
    for c in CS:
        k = MASK[c]
        for d, pick in DEFS.items():
            h = months(pick(HIST), HIST, fn)
            f_ = months(pick(FUT), FUT, fn)
            ch[d][c] = float(np.average((f_ - h)[k], weights=Wt[k]))
        spread = abs(ch['first 5'][c] - ch['last 5'][c])
        print(f'{LBL.get(c, c):<13}' + ''.join(f'{ch[d][c]:>10.2f}' for d in DEFS)
              + f'{spread:>13.2f}')
    sp = [abs(ch['first 5'][c] - ch['last 5'][c]) for c in CS]
    dev = [max(abs(ch['first 5'][c] - ch['full 10'][c]),
               abs(ch['last 5'][c] - ch['full 10'][c])) for c in CS]
    print('-' * 62)
    print(f'  spread between five-year halves: mean {np.mean(sp):.2f}, '
          f'max {np.max(sp):.2f} months')
    print(f'  deviation of a half from the decade: mean {np.mean(dev):.2f}, '
          f'max {np.max(dev):.2f} months')
