"""Verify the hazard pipeline on the historical year, and cross-check the
result against the independent UDel climatology already used. Two different
climate inputs through the same niche should give broadly similar suitable
months; large disagreement would indicate a unit or aggregation error."""
import sys
import numpy as np
sys.path.insert(0, '.')
from hazard_pipeline import monthly, suitable_months, VAR, CS
from netCDF4 import Dataset
import geopandas as gpd
from rasterio.features import rasterize
from rasterio.transform import from_origin
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

Tk, la, lo = monthly('nex/tas_day_GFDL-ESM4_historical_r1i1p1f1_gr1_2000_v2.0.nc', 'tas')
Pk, _, _ = monthly('nex/pr_day_GFDL-ESM4_historical_r1i1p1f1_gr1_2000_v2.0.nc', 'pr')
T = Tk - 273.15
R = Pk * 86400.0
print(f'grid {T.shape}, lat {la.min():.2f}..{la.max():.2f}, lon {lo.min():.2f}..{lo.max():.2f}')
print(f'T range {T.min():.1f}..{T.max():.1f} C     R range {R.min():.2f}..{R.max():.2f} mm/day')

sm_nex = suitable_months(T, R, VAR['median'])
print(f'suitable months: mean {np.nanmean(sm_nex):.2f}, '
      f'min {np.nanmin(sm_nex):.0f}, max {np.nanmax(sm_nex):.0f}')

# --- UDel comparison on the same footprint ----------------------------
DAYS = np.array([31, 28.25, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])
a = Dataset('air.mon.v501.ltm.1981-2010.nc'); p = Dataset('precip.mon.v501.ltm.1981-2010.nc')
ulat = a.variables['lat'][:].astype(float); ulon = a.variables['lon'][:].astype(float)
uT = np.ma.filled(a.variables['air'][:].astype(float), np.nan)
uP = np.ma.filled(p.variables['precip'][:].astype(float), np.nan)
uR = (uP * 10.0) / DAYS[:, None, None]
ulon180 = np.where(ulon > 180, ulon - 360, ulon)
i = np.abs(la[:, None] - ulat[None, :]).argmin(axis=1)
j = np.abs(lo[:, None] - ulon180[None, :]).argmin(axis=1)
uT_r = uT[:, i][:, :, j]; uR_r = uR[:, i][:, :, j]
sm_udel = suitable_months(uT_r, uR_r, VAR['median'])
land = np.isfinite(uT_r[0])

d = sm_nex[land] - sm_udel[land]
print(f'\nOn UDel land cells (n={land.sum():,}):')
print(f'  NEX-GDDP mean suitable months  {sm_nex[land].mean():.2f}')
print(f'  UDel     mean suitable months  {sm_udel[land].mean():.2f}')
print(f'  mean difference                {d.mean():+.2f}')
print(f'  median |difference|            {np.median(np.abs(d)):.2f}')
print(f'  agreement within 1 month       {100*(np.abs(d)<=1).mean():.1f}%')
print(f'  agreement within 2 months      {100*(np.abs(d)<=2).mean():.1f}%')
print('\nNote: NEX-GDDP is a single year (2000); UDel is a 1981-2010 mean, so')
print('some disagreement is expected from interannual variability alone.')
np.savez_compressed('pipeline_hist.npz', lat=la, lon=lo, sm=sm_nex)
print('wrote pipeline_hist.npz')
