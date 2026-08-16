"""Four-way comparison: put ecological and climate uncertainty on one footing.

For each country, each ecological niche, each climate model and each scenario,
compute the change in annual suitable months between the historical window
(2005-2014) and end-century (2086-2095). Then decompose the variance of that
change across its three sources.

This replaces the delta-warming proxy: warming is now taken from the models
themselves rather than imposed uniformly, and rainfall changes with it.
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
# Natural Earth 1:110m omits Singapore entirely - it falls below that file's
# scale threshold - which is why Singapore dropped out of earlier hazard
# tables. The 1:10m file includes it. Switching changes the other nine
# countries' suitability by at most 0.02 months (checked), so the finer
# boundaries are used throughout for consistency rather than special-casing.
BOUNDS, BCOL = 'ne10_adm1.geojson', 'admin'
SCEN = ['ssp126', 'ssp245', 'ssp585']

z = np.load('ensemble_monthly.npz')
LA, LO = z['lat'], z['lon']
MODELS = sorted({k.split('__')[0] for k in z.files if k not in ('lat', 'lon')})

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

NICHES = {
    'aegypti': {'Kaye median': grid_fn(kaye['MedianM'], kT, kR),
                'Kaye 97.5th': grid_fn(kaye['BiggestM'], kT, kR),
                'Liu-Helmersson': grid_fn(lh['MedianM'], lT, lR),
                'Mordecai': band_fn(17.8, 34.6),
                'Ryan': band_fn(21.3, 34.0)},
    'albopictus': {'Mordecai': band_fn(16.2, 31.6),
                   'Ryan': band_fn(19.9, 29.4)},
}

# ---- country masks ----------------------------------------------------
world = gpd.read_file(BOUNDS)
LOg, LAg = np.meshgrid(LO, LA)
pts = gpd.GeoDataFrame(geometry=[Point(x, y) for x, y in zip(LOg.ravel(), LAg.ravel())],
                       crs=world.crs)
jn = gpd.sjoin(pts, world[[BCOL, 'geometry']], how='left', predicate='within')
jn = jn[~jn.index.duplicated(keep='first')]
cname = jn[BCOL].values.reshape(LOg.shape)
land = np.isfinite(z[f'{MODELS[0]}__historical__tas'][0])
MASK = {c: (np.isin(cname, NAMEFIX.get(c, [c])) & land) for c in CS}
for c, m in MASK.items():
    if m.sum() == 0:
        raise SystemExit(f'{c} has no land cell - mask source or grid is wrong')
print('cells per country: ' + ', '.join(f'{c} {MASK[c].sum()}' for c in CS) + '\n')
W = np.cos(np.deg2rad(LA))[:, None] * np.ones((1, LO.size))

def months(model, scen, fn):
    T = z[f'{model}__{scen}__tas'] - 273.15
    R = z[f'{model}__{scen}__pr'] * 86400.0
    sm = np.zeros(T.shape[1:], float)
    for m in range(12):
        sm += fn(T[m], R[m])
    return sm

# ---- assemble ---------------------------------------------------------
rows = []
for sp, ns in NICHES.items():
    for nname, fn in ns.items():
        hist = {m: months(m, 'historical', fn) for m in MODELS}
        for m, s in itertools.product(MODELS, SCEN):
            fut = months(m, s, fn)
            d = fut - hist[m]
            for c in CS:
                msk = MASK[c]
                rows.append(dict(species=sp, niche=nname, model=m, scenario=s,
                                 country=c,
                                 change=float(np.average(d[msk], weights=W[msk])),
                                 future=float(np.average(fut[msk], weights=W[msk])),
                                 hist=float(np.average(hist[m][msk], weights=W[msk]))))
print(f'{len(rows)} country x niche x model x scenario combinations\n')

# ---- variance decomposition ------------------------------------------
def decompose(sub):
    """main-effects variance shares for niche, model, scenario"""
    vals = np.array([r['change'] for r in sub])
    tot = vals.var()
    if tot == 0:
        return dict(niche=np.nan, model=np.nan, scenario=np.nan, resid=np.nan, total=0.0)
    out = {}
    for fac in ('niche', 'model', 'scenario'):
        g = collections.defaultdict(list)
        for r in sub:
            g[r[fac]].append(r['change'])
        means = np.array([np.mean(v) for v in g.values()])
        wts = np.array([len(v) for v in g.values()], float); wts /= wts.sum()
        out[fac] = float(np.sum(wts * (means - vals.mean()) ** 2) / tot)
    out['resid'] = float(max(0.0, 1 - sum(out.values())))
    out['total'] = float(tot)
    return out

print('Variance in projected CHANGE in suitable months, by source')
print('(share of total variance; historical 2005-2014 -> 2086-2095)\n')
summary = {}
for sp in ('aegypti', 'albopictus'):
    print(f'--- Ae. {sp} ---')
    print(f"{'country':<12}{'niche':>9}{'model':>9}{'scenario':>10}{'resid':>8}"
          f"{'sd(mo)':>9}{'mean chg':>10}")
    print('-' * 68)
    for c in CS:
        sub = [r for r in rows if r['species'] == sp and r['country'] == c]
        d = decompose(sub)
        mean_chg = np.mean([r['change'] for r in sub])
        print(f'{c:<12}{d["niche"]:>9.2f}{d["model"]:>9.2f}{d["scenario"]:>10.2f}'
              f'{d["resid"]:>8.2f}{np.sqrt(d["total"]):>9.2f}{mean_chg:>10.2f}')
        summary[f'{sp}|{c}'] = d
    print()

# ---- headline: does the ensemble agree on direction? -----------------
print('Directional agreement across all niche x model x scenario members')
print(f"{'country':<12}{'aegypti: n':>12}{'% decline':>11}"
      f"{'albopictus: n':>15}{'% decline':>11}")
print('-' * 62)
for c in CS:
    line = f'{c:<12}'
    for sp in ('aegypti', 'albopictus'):
        sub = [r['change'] for r in rows if r['species'] == sp and r['country'] == c]
        line += f'{len(sub):>12}{100*np.mean(np.array(sub) < -0.25):>11.0f}' if sp == 'aegypti' \
                else f'{len(sub):>15}{100*np.mean(np.array(sub) < -0.25):>11.0f}'
    print(line)

json.dump({'rows': rows, 'variance': summary}, open('decomposition.json', 'w'))
print('\nwrote decomposition.json')
