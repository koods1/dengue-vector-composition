"""Two sensitivity checks the Methods promise.

1. Leave-one-model-out. Does any single GCM carry the mainland/maritime
   split in albopictus agreement? Recompute the agreement fraction with
   each model dropped in turn and report the range.

2. Warming already realised. The ensemble historical window is 2005-2014,
   whereas the uniform-warming sensitivity is expressed relative to the
   1981-2010 observed climatology. State how much warming separates the
   two, per country, so the two framings can be read against each other.
"""
import sys, json, itertools
import numpy as np
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

CS = ['Malaysia', 'Indonesia', 'Thailand', 'Philippines', 'Vietnam', 'India',
      'Bangladesh', 'Cambodia', 'Sri Lanka', 'Singapore']
MAINLAND = {'Thailand', 'Cambodia', 'Bangladesh', 'Sri Lanka', 'Vietnam', 'India'}

# ---------- 1. leave-one-model-out -------------------------------------
rows = json.load(open('decomposition.json'))['rows']
MODELS = sorted({r['model'] for r in rows})


def agree(sp, c, drop=None):
    v = [r['change'] for r in rows if r['species'] == sp and r['country'] == c
         and r['model'] != drop]
    return 100.0 * np.mean(np.array(v) < -0.25)


print('1. Leave-one-model-out: % of albopictus members projecting decline\n')
print(f"{'country':<13}{'all 8':>8}" + ''.join(f'{m[:9]:>10}' for m in MODELS))
print('-' * (21 + 10 * len(MODELS)))
worst = 0.0
for c in CS:
    full = agree('albopictus', c)
    outs = [agree('albopictus', c, m) for m in MODELS]
    worst = max(worst, max(abs(o - full) for o in outs))
    print(f'{c:<13}{full:>8.0f}' + ''.join(f'{o:>10.0f}' for o in outs))
print(f'\nLargest shift from dropping any single model: {worst:.0f} '
      f'percentage points.')

mland = [agree('albopictus', c) for c in CS if c in MAINLAND]
marit = [agree('albopictus', c) for c in CS if c not in MAINLAND]
print(f'Mainland range {min(mland):.0f}-{max(mland):.0f}%, '
      f'maritime {min(marit):.0f}-{max(marit):.0f}%, full ensemble.')
sep = []
for m in MODELS:
    a = min(agree('albopictus', c, m) for c in CS if c in MAINLAND)
    b = max(agree('albopictus', c, m) for c in CS if c not in MAINLAND)
    sep.append(a - b)
print(f'Mainland minimum minus maritime maximum, dropping each model in '
      f'turn: {min(sep):+.0f} to {max(sep):+.0f} percentage points.')
print('The split survives removal of any single model.' if min(sep) > 0
      else 'WARNING: the split does not survive removal of some model.')

# ---------- 2. warming already realised --------------------------------
print('\n\n2. Warming between the 1981-2010 observed climatology and the')
print('   2005-2014 ensemble historical window, by country\n')
try:
    import geopandas as gpd
    from shapely.geometry import Point
    from netCDF4 import Dataset
except ImportError as e:
    sys.exit(f'   skipped, missing dependency: {e}')

z = np.load('ensemble_monthly.npz')
LA, LO = z['lat'], z['lon']
MODELS8 = sorted({k.split('__')[0] for k in z.files if k not in ('lat', 'lon')})
land = np.isfinite(z[f'{MODELS8[0]}__historical__tas'][0])

d = Dataset('air.mon.v501.ltm.1981-2010.nc')
ulat = d.variables['lat'][:].astype(float)
ulon = d.variables['lon'][:].astype(float)
uT = np.ma.filled(d.variables['air'][:].astype(float), np.nan).mean(axis=0)
ulon = np.where(ulon > 180, ulon - 360, ulon)
oi = np.argsort(ulon); ulon = ulon[oi]; uT = uT[:, oi]
if ulat[0] > ulat[-1]:
    ulat = ulat[::-1]; uT = uT[::-1]

# nearest-neighbour sample of the 0.5 deg observed grid onto the 0.25 deg grid
ii = np.abs(LA[:, None] - ulat[None, :]).argmin(axis=1)
jj = np.abs(LO[:, None] - ulon[None, :]).argmin(axis=1)
uT_on = uT[np.ix_(ii, jj)]

ens = np.nanmean([z[f'{m}__historical__tas'] - 273.15 for m in MODELS8],
                 axis=0).mean(axis=0)

world = gpd.read_file('ne10_adm1.geojson')
LOg, LAg = np.meshgrid(LO, LA)
pts = gpd.GeoDataFrame(geometry=[Point(x, y) for x, y in
                                 zip(LOg.ravel(), LAg.ravel())], crs=world.crs)
jn = gpd.sjoin(pts, world[['admin', 'geometry']], how='left', predicate='within')
jn = jn[~jn.index.duplicated(keep='first')]
cname = jn['admin'].values.reshape(LOg.shape)
W = np.cos(np.deg2rad(LA))[:, None] * np.ones((1, LO.size))
NF = {'Vietnam': ['Vietnam', 'Viet Nam']}

print(f"{'country':<13}{'UDel 1981-2010':>16}{'ens 2005-2014':>15}{'warming':>10}")
print('-' * 54)
out = {}
for c in CS:
    m = np.isin(cname, NF.get(c, [c])) & land & np.isfinite(uT_on)
    if not m.any():
        continue
    a = np.average(uT_on[m], weights=W[m])
    b = np.average(ens[m], weights=W[m])
    out[c] = b - a
    print(f'{c:<13}{a:>15.2f}{b:>15.2f}{b-a:>+10.2f}')
print(f'\nRange {min(out.values()):+.2f} to {max(out.values()):+.2f} C; '
      f'mean {np.mean(list(out.values())):+.2f} C.')
