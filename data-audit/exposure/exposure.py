"""I. Population exposure pipeline. Combines the 1 km SSP population
projection with the suitability surface and aggregates to admin-1 units.

Exposure is defined as population weighted by the fraction of the year
that is climatically suitable, which avoids an arbitrary suitability
threshold and preserves the seasonal-length signal the model produces.
"""
import sys, csv
import numpy as np
import rasterio
from rasterio.windows import from_bounds
from rasterio.features import rasterize
from rasterio.transform import from_origin
import geopandas as gpd
from netCDF4 import Dataset
from scipy.io import loadmat
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

W, E, S, N = 66.0, 142.0, -12.0, 38.0
CS = ['Singapore', 'Malaysia', 'Indonesia', 'Thailand', 'Philippines',
      'Vietnam', 'India', 'Bangladesh', 'Cambodia', 'Sri Lanka']

# ---- population -------------------------------------------------------
with rasterio.open('pop/SSP2_2050.tif') as ds:
    print(f'population raster {ds.width} x {ds.height}, dtype {ds.dtypes[0]}, '
          f'crs {ds.crs}, nodata {ds.nodata}')
    win = from_bounds(W, S, E, N, ds.transform)
    pop = ds.read(1, window=win).astype('float64')
    ptr = ds.window_transform(win)
    nod = ds.nodata
pop[~np.isfinite(pop)] = 0.0
if nod is not None:
    pop[pop == nod] = 0.0
pop[pop < 0] = 0.0
ph, pw = pop.shape
print(f'region window {ph} x {pw}; total population {pop.sum() / 1e6:,.1f} million')

plat = ptr.f + (np.arange(ph) + 0.5) * ptr.e      # e is negative
plon = ptr.c + (np.arange(pw) + 0.5) * ptr.a

# ---- suitability on the 0.5 deg grid, mapped onto the pop grid --------
DAYS = np.array([31, 28.25, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])
lk = loadmat('MLookupTable.mat')
nT, nR, MED = lk['Temperatures'].ravel(), lk['Rainfalls'].ravel(), lk['MedianM']
dT, dR = nT[1] - nT[0], nR[1] - nR[0]
a = Dataset('air.mon.v501.ltm.1981-2010.nc'); p = Dataset('precip.mon.v501.ltm.1981-2010.nc')
clat = a.variables['lat'][:].astype(float); clon = a.variables['lon'][:].astype(float)
T = np.ma.filled(a.variables['air'][:].astype(float), np.nan)
P = np.ma.filled(p.variables['precip'][:].astype(float), np.nan)
R = (P * 10.0) / DAYS[:, None, None]
sm = np.zeros(T.shape[1:], float)
for m in range(12):
    t, r = T[m], R[m]
    ok = np.isfinite(t) & np.isfinite(r)
    i = np.clip(np.round((np.nan_to_num(t) - nT[0]) / dT).astype(int), 0, nT.size - 1)
    j = np.clip(np.round((np.nan_to_num(r) - nR[0]) / dR).astype(int), 0, nR.size - 1)
    sm += (ok & (MED[i, j] > 0))
clon180 = np.where(clon > 180, clon - 360, clon)
si = np.abs(plat[:, None] - clat[None, :]).argmin(axis=1)
sj = np.abs(plon[:, None] - clon180[None, :]).argmin(axis=1)
SUIT = sm[np.ix_(si, sj)]                       # months, on the pop grid
SUIT = np.nan_to_num(SUIT, nan=0.0)

# ---- admin-1 units ----------------------------------------------------
g = gpd.read_file('ne10_adm1.geojson')
g = g[g['admin'].isin(CS)].reset_index(drop=True)
g['uid'] = np.arange(1, len(g) + 1)
uid = rasterize(((geom, int(u)) for geom, u in zip(g.geometry, g['uid'])),
                out_shape=(ph, pw), transform=ptr, fill=0, dtype='int32')
print(f'rasterised {len(g)} units onto the population grid')

# ---- aggregate --------------------------------------------------------
frac = SUIT / 12.0
rows = []
for u, name, adm in zip(g['uid'], g['name'], g['admin']):
    m = uid == u
    if not m.any():
        rows.append((adm, name, 0.0, 0.0, np.nan)); continue
    tot = pop[m].sum()
    exp = (pop[m] * frac[m]).sum()
    rows.append((adm, name, tot, exp, exp / tot if tot > 0 else np.nan))

print(f"\n{'country':<13}{'pop 2050 (M)':>14}{'exposed (M)':>13}{'share':>8}{'units':>7}")
print('-' * 55)
for c in CS:
    sel = [r for r in rows if r[0] == c]
    tp = sum(r[2] for r in sel) / 1e6
    te = sum(r[3] for r in sel) / 1e6
    print(f'{c:<13}{tp:>14,.1f}{te:>13,.1f}{(te / tp if tp else float("nan")):>8.2f}{len(sel):>7}')
print('-' * 55)
tp = sum(r[2] for r in rows) / 1e6; te = sum(r[3] for r in rows) / 1e6
print(f"{'TOTAL':<13}{tp:>14,.1f}{te:>13,.1f}{te / tp:>8.2f}")

with open('exposure_admin1.csv', 'w', newline='', encoding='utf8') as fh:
    w = csv.writer(fh)
    w.writerow(['country', 'unit', 'pop_2050_ssp2', 'suitability_weighted_exposed',
                'exposed_share'])
    for r in rows:
        w.writerow([r[0], r[1], round(r[2], 1), round(r[3], 1),
                    '' if not np.isfinite(r[4]) else round(r[4], 4)])
print('\nwrote exposure_admin1.csv')
