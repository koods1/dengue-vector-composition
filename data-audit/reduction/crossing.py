"""Express the vector-composition change as dates rather than temperature
offsets.

Three windows are available: 2005-2014, 2046-2055 and 2086-2095. For each
country x niche x model x scenario we have suitable months at each. We ask
when suitable months first fall one month below the historical value.

Three windows do not support year-level interpolation, so none is done. A
member is assigned to the FIRST window in which the drop is already present:
'by 2050s', '2050s-2090s', or 'not before 2095'. These are window labels, not
estimated dates - nothing here licenses quoting a crossing year, and the
result should always be reported with the spread across ensemble members.
"""
import sys, json, itertools, collections
import numpy as np
from scipy.io import loadmat
import geopandas as gpd
from shapely.geometry import Point
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

CS = ['Malaysia', 'Indonesia', 'Thailand', 'Philippines', 'Vietnam',
      'India', 'Bangladesh', 'Cambodia', 'Sri Lanka', 'Singapore']
NAMEFIX = {'Vietnam': ['Vietnam', 'Viet Nam']}
BOUNDS, BCOL = 'ne10_adm1.geojson', 'admin'   # 1:110m omits Singapore; see decompose.py
SCEN = ['ssp126', 'ssp245', 'ssp585']
DROP = 1.0                      # months below historical that counts as crossing

zh = np.load('ensemble_monthly.npz')       # historical + end-century
zm = np.load('ensemble_monthly_mid.npz')   # mid-century
LA, LO = zh['lat'], zh['lon']
MODELS = sorted({k.split('__')[0] for k in zh.files if k not in ('lat', 'lon')})

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

NICHES = {
    'aegypti': {'Kaye median': grid_fn(kaye['MedianM'], kT, kR),
                'Kaye 97.5th': grid_fn(kaye['BiggestM'], kT, kR),
                'Liu-Helmersson': grid_fn(lh['MedianM'], lT, lR),
                'Mordecai': band_fn(17.8, 34.6), 'Ryan': band_fn(21.3, 34.0)},
    'albopictus': {'Mordecai': band_fn(16.2, 31.6), 'Ryan': band_fn(19.9, 29.4)},
}

world = gpd.read_file(BOUNDS)
LOg, LAg = np.meshgrid(LO, LA)
pts = gpd.GeoDataFrame(geometry=[Point(x, y) for x, y in zip(LOg.ravel(), LAg.ravel())],
                       crs=world.crs)
jn = gpd.sjoin(pts, world[[BCOL, 'geometry']], how='left', predicate='within')
jn = jn[~jn.index.duplicated(keep='first')]
cname = jn[BCOL].values.reshape(LOg.shape)
land = np.isfinite(zh[f'{MODELS[0]}__historical__tas'][0])
MASK = {c: (np.isin(cname, NAMEFIX.get(c, [c])) & land) for c in CS}
for c, m in MASK.items():
    if m.sum() == 0:
        raise SystemExit(f'{c} has no land cell - mask source or grid is wrong')
W = np.cos(np.deg2rad(LA))[:, None] * np.ones((1, LO.size))


def months(z, model, scen, fn):
    T = z[f'{model}__{scen}__tas'] - 273.15
    R = z[f'{model}__{scen}__pr'] * 86400.0
    return sum(fn(T[m], R[m]) for m in range(12)).astype(float)


def bin_of(h, mid, end):
    """which period does the drop of DROP months first occur in?"""
    if mid <= h - DROP:
        return 'by 2050s'
    if end <= h - DROP:
        return '2050s-2090s'
    return 'not before 2095'


rows = []
for sp, ns in NICHES.items():
    for nname, fn in ns.items():
        hist = {m: months(zh, m, 'historical', fn) for m in MODELS}
        for m, s in itertools.product(MODELS, SCEN):
            mm = months(zm, m, s, fn)
            ee = months(zh, m, s, fn)
            for c in CS:
                k = MASK[c]
                h = float(np.average(hist[m][k], weights=W[k]))
                a = float(np.average(mm[k], weights=W[k]))
                b = float(np.average(ee[k], weights=W[k]))
                rows.append(dict(species=sp, niche=nname, model=m, scenario=s,
                                 country=c, hist=h, mid=a, end=b,
                                 bin=bin_of(h, a, b)))

print(f'{len(rows)} country x niche x model x scenario paths\n')
COLW = 18
for sp in ('albopictus', 'aegypti'):
    n_mem = len(NICHES[sp]) * len(MODELS)
    print(f'=== Ae. {sp}: % of {n_mem} ensemble members already {DROP:.0f} month '
          f'below historical ===')
    print(f"{'country':<12}" + ''.join(f'{s:>{COLW}}' for s in SCEN))
    print(f"{'':<12}" + ''.join(f'{"by50":>6}{"by90":>6}{"never":>6}'
                                for _ in SCEN))
    print('-' * (12 + COLW * len(SCEN)))
    for c in CS:
        line = f'{c:<12}'
        for s in SCEN:
            sub = [r for r in rows if r['species'] == sp and r['country'] == c
                   and r['scenario'] == s]
            cnt = collections.Counter(r['bin'] for r in sub)
            n = len(sub)
            by50 = 100 * cnt['by 2050s'] / n
            by90 = 100 * (cnt['by 2050s'] + cnt['2050s-2090s']) / n
            never = 100 * cnt['not before 2095'] / n
            line += f'{by50:>6.0f}{by90:>6.0f}{never:>6.0f}'
        print(line)
    print()

json.dump(rows, open('crossing.json', 'w'))
print('wrote crossing.json')
