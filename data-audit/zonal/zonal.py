"""E. Admin-1 boundaries and the zonal aggregation pipeline.

Builds an area-weighted grid-to-unit aggregation and reports whether each
unit is resolvable at the hazard grid resolution. Applied to the baseline
suitable-months field as a working test.
"""
import sys, json
import numpy as np
import geopandas as gpd
from netCDF4 import Dataset
from scipy.io import loadmat
from rasterio.features import rasterize
from rasterio.transform import from_origin
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

CS = ['Singapore', 'Malaysia', 'Indonesia', 'Thailand', 'Philippines',
      'Vietnam', 'India', 'Bangladesh', 'Cambodia', 'Sri Lanka']
FINE = 0.05          # rasterisation resolution, degrees
W, E, S, N = 66.0, 142.0, -12.0, 38.0

g = gpd.read_file('ne10_adm1.geojson')
g = g[g['admin'].isin(CS)].reset_index(drop=True)
g['uid'] = np.arange(1, len(g) + 1)

# --- unit areas on an equal-area projection ---------------------------
ga = g.to_crs('EPSG:6933')
g['area_km2'] = ga.geometry.area / 1e6

# --- rasterise unit ids at FINE resolution ----------------------------
nx = int(round((E - W) / FINE)); ny = int(round((N - S) / FINE))
tr = from_origin(W, N, FINE, FINE)
uid = rasterize(((geom, int(u)) for geom, u in zip(g.geometry, g['uid'])),
                out_shape=(ny, nx), transform=tr, fill=0, all_touched=False,
                dtype='int32')
print(f'rasterised {len(g)} units to {ny} x {nx} at {FINE} deg '
      f'({(uid > 0).sum():,} fine cells assigned)')

flat_lat = N - (np.arange(ny) + 0.5) * FINE
flat_lon = W + (np.arange(nx) + 0.5) * FINE
wgt = np.cos(np.deg2rad(flat_lat))[:, None] * np.ones((1, nx))   # area weight

# --- baseline suitable months on the 0.5 deg climatology grid ---------
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
sm[~np.isfinite(T[0])] = np.nan

# nearest-neighbour lookup from fine cells to the 0.5 deg grid
clon180 = np.where(clon > 180, clon - 360, clon)
li = np.abs(flat_lat[:, None] - clat[None, :]).argmin(axis=1)
lj = np.abs(flat_lon[:, None] - clon180[None, :]).argmin(axis=1)
FIELD = sm[np.ix_(li, lj)]

# --- aggregate ---------------------------------------------------------
rows = []
for u, name, adm, ar in zip(g['uid'], g['name'], g['admin'], g['area_km2']):
    msk = uid == u
    n_fine = int(msk.sum())
    if n_fine == 0:
        rows.append((adm, name, ar, 0, np.nan, 0)); continue
    vals = FIELD[msk]; w = wgt[msk]
    good = np.isfinite(vals)
    val = float(np.average(vals[good], weights=w[good])) if good.any() else np.nan
    # distinct 0.5 deg parent cells touched
    par = set(zip(li[np.where(msk.any(axis=1))[0]], lj[np.where(msk.any(axis=0))[0]]))
    rows.append((adm, name, ar, n_fine, val, len(par)))

CELL025 = 0.25 * 0.25 * 111.32 ** 2      # km2 at equator
print(f'\nOne 0.25 deg cell is about {CELL025:.0f} km2 at the equator\n')
print(f"{'country':<13}{'units':>6}{'median km2':>12}{'min km2':>10}"
      f"{'<1 cell':>9}{'no data':>9}{'mean months':>12}")
print('-' * 71)
summary = {}
for c in CS:
    sel = [r for r in rows if r[0] == c]
    ars = np.array([r[2] for r in sel])
    small = int((ars < CELL025).sum())
    nod = int(sum(1 for r in sel if not np.isfinite(r[4])))
    vals = np.array([r[4] for r in sel if np.isfinite(r[4])])
    summary[c] = dict(units=len(sel), median_km2=float(np.median(ars)),
                      min_km2=float(ars.min()), below_one_cell=small,
                      no_data=nod, mean_months=float(vals.mean()) if vals.size else None)
    print(f'{c:<13}{len(sel):>6}{np.median(ars):>12,.0f}{ars.min():>10,.0f}'
          f'{small:>9}{nod:>9}{vals.mean() if vals.size else float("nan"):>12.2f}')
print('-' * 71)
tot = len(rows)
print(f"{'TOTAL':<13}{tot:>6}")
json.dump(summary, open('zonal_summary.json', 'w'), indent=1)

import csv
with open('admin1_suitability.csv', 'w', newline='', encoding='utf8') as fh:
    w_ = csv.writer(fh)
    w_.writerow(['country', 'unit', 'area_km2', 'fine_cells', 'suitable_months', 'parent_cells_05deg'])
    for r in rows: w_.writerow([r[0], r[1], round(r[2], 1), r[3],
                                '' if not np.isfinite(r[4]) else round(r[4], 3), r[5]])
print('\nwrote admin1_suitability.csv, zonal_summary.json')
