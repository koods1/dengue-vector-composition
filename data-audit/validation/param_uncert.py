"""B. Does parametric uncertainty in the ecological niche rival the effect
of warming? Repeats the headroom analysis under the 2.5th, 50th and 97.5th
percentile niches of Kaye et al."""
import numpy as np, sys, json
from netCDF4 import Dataset
from scipy.io import loadmat
import geopandas as gpd
from shapely.geometry import Point
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

DAYS = np.array([31, 28.25, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])
COUNTRIES = ['Malaysia', 'Indonesia', 'Thailand', 'Philippines', 'Vietnam',
             'India', 'Bangladesh', 'Cambodia', 'Sri Lanka']
NAMEFIX = {'Vietnam': ['Vietnam', 'Viet Nam']}

lk = loadmat('MLookupTable.mat')
nT, nR = lk['Temperatures'].ravel(), lk['Rainfalls'].ravel()
dT, dR = nT[1] - nT[0], nR[1] - nR[0]
VARIANTS = {'2.5th pct': lk['SmallestM'], 'median': lk['MedianM'],
            '97.5th pct': lk['BiggestM']}

def mk_suit(M):
    def f(T, R):
        ok = (T >= nT[0]) & (T <= nT[-1]) & (R >= nR[0]) & (R <= nR[-1])
        i = np.clip(np.round((np.nan_to_num(T) - nT[0]) / dT).astype(int), 0, nT.size - 1)
        j = np.clip(np.round((np.nan_to_num(R) - nR[0]) / dR).astype(int), 0, nR.size - 1)
        return ok & (M[i, j] > 0)
    return f

a = Dataset('air.mon.v501.ltm.1981-2010.nc'); p = Dataset('precip.mon.v501.ltm.1981-2010.nc')
lat = a.variables['lat'][:].astype(float); lon = a.variables['lon'][:].astype(float)
T = np.ma.filled(a.variables['air'][:].astype(float), np.nan)
P = np.ma.filled(p.variables['precip'][:].astype(float), np.nan)
R = (P * 10.0) / DAYS[:, None, None]
lon180 = np.where(lon > 180, lon - 360, lon)
m1 = (lon180 >= 66) & (lon180 <= 142); m2 = (lat >= -12) & (lat <= 38)
T = T[:, m2][:, :, m1]; R = R[:, m2][:, :, m1]
la, lo = lat[m2], lon180[m1]

world = gpd.read_file('ne110.geojson')
LO, LA = np.meshgrid(lo, la)
pts = gpd.GeoDataFrame(geometry=[Point(x, y) for x, y in zip(LO.ravel(), LA.ravel())],
                       crs=world.crs)
j = gpd.sjoin(pts, world[['NAME', 'geometry']], how='left', predicate='within')
j = j[~j.index.duplicated(keep='first')]
cname = j['NAME'].values.reshape(LO.shape)

deltas = [0, 1, 2, 3, 4, 5]
out = {}
for vname, M in VARIANTS.items():
    suit = mk_suit(M)
    out[vname] = {}
    for d in deltas:
        s = np.stack([suit(T[m] + d, R[m]) for m in range(12)]).sum(axis=0).astype(float)
        s[~np.isfinite(T[0])] = np.nan
        for c in COUNTRIES:
            msk = np.isin(cname, NAMEFIX.get(c, [c])) & np.isfinite(T[0])
            out[vname].setdefault(c, []).append(float(np.nanmean(s[msk])) if msk.sum() else np.nan)

print('Suitable months per year by niche variant and warming increment\n')
hdr = f"{'country':<12}{'niche':<12}" + ''.join(f'{"+" + str(d):>7}' for d in deltas)
print(hdr); print('-' * len(hdr))
for c in COUNTRIES:
    for vname in VARIANTS:
        print(f'{c:<12}{vname:<12}' + ''.join(f'{out[vname][c][i]:>7.2f}' for i in range(len(deltas))))
    print()

print('\nCompeting sources of spread, per country (suitable months/year):')
print(f"{'country':<12}{'niche spread':>14}{'warming spread':>16}{'ratio':>8}")
print('-' * 52)
ratios = []
for c in COUNTRIES:
    niche_sp = max(out[v][c][0] for v in VARIANTS) - min(out[v][c][0] for v in VARIANTS)
    warm_sp = max(out['median'][c]) - min(out['median'][c])
    r = niche_sp / warm_sp if warm_sp > 0 else np.nan
    ratios.append(r)
    print(f'{c:<12}{niche_sp:>14.2f}{warm_sp:>16.2f}{r:>8.1f}')
print('-' * 52)
print(f"{'median ratio':<12}{'':>14}{'':>16}{np.nanmedian(ratios):>8.1f}")
print('\nniche spread   = range across the 2.5th/50th/97.5th percentile niches at +0 C')
print('warming spread = range across +0 to +5 C under the median niche')
json.dump(out, open('param_uncert.json', 'w'), indent=1)
print('\nwrote param_uncert.json')
