"""Treat the validated niches as an ensemble and ask what they agree on.

Rather than reporting spread, this builds a CONSENSUS SURFACE: for each
location-month, the fraction of independently derived, validated
parameterisations that admit it. Each niche is evaluated on the actual
observed (T, R) of that location-month, so niches using temperature only and
niches using temperature and rainfall can be combined without harmonising
their variable sets.

Then, instead of a spread in suitable months, we report the WARMING THRESHOLD
at which each country's consensus suitability begins to fall - a statement
about the place, with an honest range attached, rather than a statement about
models.

Validated set (admitting >=95% of observed dengue outbreak locations):
  Ae. aegypti     Kaye median, Kaye 97.5th, Mordecai, Ryan, Liu-Helmersson
  Ae. albopictus  Mordecai, Ryan
Excluded: Kaye 2.5th percentile (58.3% - refuted).
"""
import sys, json
import numpy as np
from netCDF4 import Dataset
from scipy.io import loadmat
import geopandas as gpd
from shapely.geometry import Point
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

CS = ['Malaysia', 'Indonesia', 'Thailand', 'Philippines', 'Vietnam',
      'India', 'Bangladesh', 'Cambodia', 'Sri Lanka']
NAMEFIX = {'Vietnam': ['Vietnam', 'Viet Nam']}

# ---- niches -----------------------------------------------------------
kaye = loadmat('MLookupTable.mat')
kT, kR = kaye['Temperatures'].ravel(), kaye['Rainfalls'].ravel()
lh = loadmat('niches/LiuHelmersson_MLookupTable.mat')
lT, lR = lh['Temperatures'].ravel(), lh['Rainfalls'].ravel()

def grid_fn(G, Tax, Rax):
    dT, dR = Tax[1] - Tax[0], Rax[1] - Rax[0]
    def f(T, R):
        ok = (T >= Tax[0]) & (T <= Tax[-1]) & (R >= Rax[0]) & (R <= Rax[-1])
        i = np.clip(np.round((np.nan_to_num(T) - Tax[0]) / dT).astype(int), 0, Tax.size - 1)
        j = np.clip(np.round((np.nan_to_num(R) - Rax[0]) / dR).astype(int), 0, Rax.size - 1)
        return ok & (G[i, j] > 0)
    return f

def band_fn(lo, hi):
    return lambda T, R: np.isfinite(T) & (T >= lo) & (T <= hi)

AEGYPTI = {
    'Kaye median':      grid_fn(kaye['MedianM'], kT, kR),
    'Kaye 97.5th':      grid_fn(kaye['BiggestM'], kT, kR),
    'Liu-Helmersson':   grid_fn(lh['MedianM'], lT, lR),
    'Mordecai aegypti': band_fn(17.8, 34.6),
    'Ryan aegypti':     band_fn(21.3, 34.0),
}
ALBO = {
    'Mordecai albopictus': band_fn(16.2, 31.6),
    'Ryan albopictus':     band_fn(19.9, 29.4),
}

# ---- climate ----------------------------------------------------------
DAYS = np.array([31, 28.25, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])
a = Dataset('air.mon.v501.ltm.1981-2010.nc'); p = Dataset('precip.mon.v501.ltm.1981-2010.nc')
lat = a.variables['lat'][:].astype(float); lon = a.variables['lon'][:].astype(float)
T0 = np.ma.filled(a.variables['air'][:].astype(float), np.nan)
P0 = np.ma.filled(p.variables['precip'][:].astype(float), np.nan)
R0 = (P0 * 10.0) / DAYS[:, None, None]
lo180 = np.where(lon > 180, lon - 360, lon)
m1 = (lo180 >= 66) & (lo180 <= 142); m2 = (lat >= -12) & (lat <= 38)
T0 = T0[:, m2][:, :, m1]; R0 = R0[:, m2][:, :, m1]
la, lo = lat[m2], lo180[m1]
land = np.isfinite(T0[0])

world = gpd.read_file('ne110.geojson')
LO, LA = np.meshgrid(lo, la)
pts = gpd.GeoDataFrame(geometry=[Point(x, y) for x, y in zip(LO.ravel(), LA.ravel())],
                       crs=world.crs)
jn = gpd.sjoin(pts, world[['NAME', 'geometry']], how='left', predicate='within')
jn = jn[~jn.index.duplicated(keep='first')]
cname = jn['NAME'].values.reshape(LO.shape)
MASK = {c: (np.isin(cname, NAMEFIX.get(c, [c])) & land) for c in CS}

DELTAS = np.arange(0, 5.01, 0.25)

def consensus_months(niches, d):
    """expected suitable months = mean over niches of the count of suitable
    months, i.e. the consensus-weighted seasonal length"""
    n = len(niches)
    acc = np.zeros(T0.shape[1:], float)
    agree_hi = np.zeros(T0.shape[1:], float)   # months where ALL niches agree
    for m in range(12):
        t, r = T0[m] + d, R0[m]
        votes = np.zeros(t.shape, float)
        for f in niches.values():
            votes += f(t, r)
        acc += votes / n
        agree_hi += (votes == n)
    acc[~land] = np.nan; agree_hi[~land] = np.nan
    return acc, agree_hi

print('Consensus suitable months per year (mean over validated niches)')
print('and unanimous months (all niches agree)\n')
res = {'aegypti': {}, 'albopictus': {}}
for sp, niches in (('aegypti', AEGYPTI), ('albopictus', ALBO)):
    print(f'--- Ae. {sp}  ({len(niches)} niches) ---')
    print(f"{'country':<12}{'+0 cons':>9}{'+0 unan':>9}{'+2 cons':>9}"
          f"{'+4 cons':>9}{'threshold':>11}")
    print('-' * 60)
    curves = {c: [] for c in CS}
    unan0 = {}
    for d in DELTAS:
        cons, unan = consensus_months(niches, d)
        for c in CS:
            curves[c].append(float(np.nanmean(cons[MASK[c]])))
            if d == 0:
                unan0[c] = float(np.nanmean(unan[MASK[c]]))
    for c in CS:
        y = np.array(curves[c])
        base = y[0]
        # warming at which consensus suitability first falls 1 month below baseline
        below = np.where(y <= base - 1.0)[0]
        thr = f'{DELTAS[below[0]]:.2f} C' if below.size else '> +5 C'
        i2 = int(np.argmin(np.abs(DELTAS - 2))); i4 = int(np.argmin(np.abs(DELTAS - 4)))
        print(f'{c:<12}{base:>9.2f}{unan0[c]:>9.2f}{y[i2]:>9.2f}{y[i4]:>9.2f}{thr:>11}')
        res[sp][c] = {'deltas': DELTAS.tolist(), 'consensus': y.tolist(),
                      'unanimous_at_0': unan0[c], 'threshold': thr}
    print()

print('=== what the ensemble agrees on ===')
print('threshold = warming at which consensus suitability falls 1 month below present\n')
print(f"{'country':<12}{'aegypti':>12}{'albopictus':>14}{'ordering':>12}")
print('-' * 52)
for c in CS:
    ta, tb = res['aegypti'][c]['threshold'], res['albopictus'][c]['threshold']
    def num(s):
        return 99.0 if s.startswith('>') else float(s.split()[0])
    order = 'albopictus first' if num(tb) < num(ta) else (
        'aegypti first' if num(ta) < num(tb) else 'same')
    print(f'{c:<12}{ta:>12}{tb:>14}{order:>12}')

json.dump(res, open('consensus.json', 'w'), indent=1)
print('\nwrote consensus.json')
