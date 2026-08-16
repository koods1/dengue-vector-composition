"""How much of the Ae. albopictus result rests on the upper thermal bound?

The albopictus ensemble is two temperature-only bands, Mordecai (16.2-31.6
C) and Ryan (19.9-29.4 C). Under warming the lower bound does almost no
work, so one parameter -- the upper bound -- carries the projected decline.
The Methods promise an explicit sensitivity on it.

We sweep the upper bound from 28 to 34 C, holding the lower bound at the
published values, and report the mean projected change and the fraction of
ensemble members declining, per country. This says how fast the headline
result degrades as that one parameter moves.
"""
import sys, itertools
import numpy as np
import geopandas as gpd
from shapely.geometry import Point

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

CS = ['Malaysia', 'Indonesia', 'Thailand', 'Philippines', 'Vietnam', 'India',
      'Bangladesh', 'Cambodia', 'Sri Lanka', 'Singapore']
NF = {'Vietnam': ['Vietnam', 'Viet Nam']}
SCEN = ['ssp126', 'ssp245', 'ssp585']
LOWER = {'Mordecai': 16.2, 'Ryan': 19.9}
PUBLISHED = {'Mordecai': 31.6, 'Ryan': 29.4}
SWEEP = [28.0, 29.0, 29.4, 30.0, 31.0, 31.6, 32.0, 33.0, 34.0]

z = np.load('ensemble_monthly.npz')
LA, LO = z['lat'], z['lon']
MODELS = sorted({k.split('__')[0] for k in z.files if k not in ('lat', 'lon')})
land = np.isfinite(z[f'{MODELS[0]}__historical__tas'][0])

world = gpd.read_file('ne10_adm1.geojson')
LOg, LAg = np.meshgrid(LO, LA)
pts = gpd.GeoDataFrame(geometry=[Point(x, y) for x, y in
                                 zip(LOg.ravel(), LAg.ravel())], crs=world.crs)
jn = gpd.sjoin(pts, world[['admin', 'geometry']], how='left', predicate='within')
jn = jn[~jn.index.duplicated(keep='first')]
cname = jn['admin'].values.reshape(LOg.shape)
MASK = {c: (np.isin(cname, NF.get(c, [c])) & land) for c in CS}
W = np.cos(np.deg2rad(LA))[:, None] * np.ones((1, LO.size))


def months(model, scen, lo, hi):
    T = z[f'{model}__{scen}__tas'] - 273.15
    return sum(((T[m] >= lo) & (T[m] <= hi)) for m in range(12)).astype(float)


print('Ae. albopictus, historical (2005-2014) to 2086-2095.')
print('Mean change in suitable months, by upper thermal bound.')
print('Published bounds: Mordecai 31.6 C, Ryan 29.4 C.\n')
print(f"{'upper (C)':>10}" + ''.join(f'{c[:9]:>10}' for c in CS) + f"{'mean':>9}{'decl%':>7}")
print('-' * (10 + 10 * len(CS) + 16))

for hi in SWEEP:
    per_country, decl = [], []
    for c in CS:
        k = MASK[c]
        ch = []
        for nm, lo in LOWER.items():
            for m, s in itertools.product(MODELS, SCEN):
                h = months(m, 'historical', lo, hi)
                f = months(m, s, lo, hi)
                ch.append(float(np.average((f - h)[k], weights=W[k])))
        per_country.append(np.mean(ch))
        decl.append(100.0 * np.mean(np.array(ch) < -0.25))
    tag = ''
    if hi in PUBLISHED.values():
        tag = ' *'
    print(f'{hi:>10.1f}' + ''.join(f'{v:>10.2f}' for v in per_country)
          + f'{np.mean(per_country):>9.2f}{np.mean(decl):>6.0f}%{tag}')

print('\n* published value. Rows either side show how the projected decline')
print('changes if the single upper-bound parameter is moved by 1 C.')
