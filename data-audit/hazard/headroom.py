"""Baseline Aedes aegypti suitability across the ten study countries, and
thermal headroom under uniform warming increments.

Climate: UDel v5.01 long-term monthly means 1981-2010, 0.5 degree.
Niche:   Kaye et al. (2024) median ecological niche, reproduced exactly
         (see niche_reimpl.py).

This is a delta-warming sensitivity, not a projection: it applies uniform
temperature increments to observed climatology and holds rainfall fixed.
It answers how much warming a location can absorb before losing suitable
months, and by which mechanism months are lost.
"""
import numpy as np, sys, json
from netCDF4 import Dataset
import geopandas as gpd
from shapely.geometry import Point
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

DAYS = np.array([31, 28.25, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])
COUNTRIES = ['Singapore', 'Malaysia', 'Indonesia', 'Thailand', 'Philippines',
             'Vietnam', 'India', 'Bangladesh', 'Cambodia', 'Sri Lanka']

# ---------- niche ----------
nz = np.load('niche_python.npz')
nT, nR, MED = nz['T'], nz['R'], nz['MedianM']
dT = nT[1] - nT[0]
dR = nR[1] - nR[0]

def suitable(T, R):
    """boolean suitability from the median niche; out-of-table -> unsuitable"""
    ok = (T >= nT[0]) & (T <= nT[-1]) & (R >= nR[0]) & (R <= nR[-1])
    i = np.clip(np.round((T - nT[0]) / dT).astype(int), 0, nT.size - 1)
    j = np.clip(np.round((R - nR[0]) / dR).astype(int), 0, nR.size - 1)
    return ok & (MED[i, j] > 0)

# upper thermal limit and rainfall ceiling, for mechanism attribution
TMAX_AT_R = np.full(nR.size, np.nan)
for j in range(nR.size):
    col = np.where(MED[:, j] > 0)[0]
    if col.size:
        TMAX_AT_R[j] = nT[col[-1]]

def too_hot(T, R):
    j = np.clip(np.round((R - nR[0]) / dR).astype(int), 0, nR.size - 1)
    lim = TMAX_AT_R[j]
    return np.where(np.isnan(lim), False, T > lim)

# ---------- climate ----------
a = Dataset('air.mon.v501.ltm.1981-2010.nc')
p = Dataset('precip.mon.v501.ltm.1981-2010.nc')
lat = a.variables['lat'][:].astype(float)
lon = a.variables['lon'][:].astype(float)
T = np.ma.filled(a.variables['air'][:].astype(float), np.nan)         # degC
P = np.ma.filled(p.variables['precip'][:].astype(float), np.nan)      # cm/month
R = (P * 10.0) / DAYS[:, None, None]                                  # mm/day

lon180 = np.where(lon > 180, lon - 360, lon)
inreg = (lon180 >= 66) & (lon180 <= 142)
inlat = (lat >= -12) & (lat <= 38)
T = T[:, inlat][:, :, inreg]
R = R[:, inlat][:, :, inreg]
la, lo = lat[inlat], lon180[inreg]
print(f'region grid: {T.shape[1]} lat x {T.shape[2]} lon, {np.isfinite(T[0]).sum()} land cells')

# ---------- country mask ----------
world = gpd.read_file('ne110.geojson')
NAMEFIX = {'Vietnam': ['Vietnam', 'Viet Nam'], 'Sri Lanka': ['Sri Lanka']}
LO, LA = np.meshgrid(lo, la)
pts = gpd.GeoDataFrame(geometry=[Point(x, y) for x, y in zip(LO.ravel(), LA.ravel())],
                       crs=world.crs)
joined = gpd.sjoin(pts, world[['NAME', 'geometry']], how='left', predicate='within')
joined = joined[~joined.index.duplicated(keep='first')]
cname = joined['NAME'].values.reshape(LO.shape)

# ---------- baseline and warming ----------
deltas = [0, 1, 2, 3, 4, 5]
res = {}
for d in deltas:
    s = np.stack([suitable(T[m] + d, R[m]) for m in range(12)])
    res[d] = s.sum(axis=0).astype(float)
    res[d][~np.isfinite(T[0])] = np.nan

print('\nSuitable months per year (land-cell mean within country)')
hdr = f"{'country':<13}{'cells':>6}" + ''.join(f'{"+" + str(d):>7}' for d in deltas) + f"{'change':>8}"
print(hdr); print('-' * len(hdr))
summary = {}
for c in COUNTRIES:
    names = NAMEFIX.get(c, [c])
    m = np.isin(cname, names) & np.isfinite(T[0])
    if m.sum() == 0:
        print(f'{c:<13}{0:>6}   -- no land cells at 0.5 deg --')
        continue
    row = [np.nanmean(res[d][m]) for d in deltas]
    summary[c] = {'cells': int(m.sum()), 'months': [round(float(v), 2) for v in row]}
    print(f'{c:<13}{m.sum():>6}' + ''.join(f'{v:>7.2f}' for v in row)
          + f'{row[-1] - row[0]:>8.2f}')

# ---------- mechanism of loss ----------
print('\nMechanism of month-loss under +3 C (months lost per cell-year, region total)')
lost_hot = lost_wet = lost_any = 0
for m in range(12):
    base = suitable(T[m], R[m])
    warm = suitable(T[m] + 3, R[m])
    lost = base & ~warm
    hot = lost & too_hot(T[m] + 3, R[m])
    lost_any += np.nansum(lost)
    lost_hot += np.nansum(hot)
    lost_wet += np.nansum(lost & ~hot)
print(f'  months lost total          {lost_any:>8.0f}')
print(f'  attributable to heat       {lost_hot:>8.0f}  ({100 * lost_hot / max(lost_any,1):.1f}%)')
print(f'  attributable to other      {lost_wet:>8.0f}  ({100 * lost_wet / max(lost_any,1):.1f}%)')

# ---------- how close to the ceiling today ----------
print('\nBaseline months already within 2 C of the upper thermal limit')
near = 0; tot = 0
for m in range(12):
    base = suitable(T[m], R[m])
    j = np.clip(np.round((R[m] - nR[0]) / dR).astype(int), 0, nR.size - 1)
    lim = TMAX_AT_R[j]
    near += np.nansum(base & np.isfinite(lim) & ((lim - T[m]) < 2))
    tot += np.nansum(base)
print(f'  {near:.0f} of {tot:.0f} suitable cell-months ({100 * near / max(tot,1):.1f}%)')

json.dump(summary, open('headroom_summary.json', 'w'), indent=1)
np.savez_compressed('headroom_grids.npz', lat=la, lon=lo,
                    **{f'd{d}': res[d] for d in deltas})
print('\nwrote headroom_summary.json, headroom_grids.npz')
