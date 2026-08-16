"""Why are cell-months unsuitable at baseline in the study region?
Tests the claim, written into Methods 2.3, that rainfall washout is the
more common contraction mechanism in monsoon Asia."""
import numpy as np, sys
from netCDF4 import Dataset
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

DAYS = np.array([31, 28.25, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])
nz = np.load('niche_python.npz')
nT, nR, MED = nz['T'], nz['R'], nz['MedianM']
dT, dR = nT[1] - nT[0], nR[1] - nR[0]

# per-rainfall thermal window, and per-temperature rainfall window
TLIM = np.full((nR.size, 2), np.nan)
for j in range(nR.size):
    c = np.where(MED[:, j] > 0)[0]
    if c.size:
        TLIM[j] = (nT[c[0]], nT[c[-1]])
RLIM = np.full((nT.size, 2), np.nan)
for i in range(nT.size):
    c = np.where(MED[i, :] > 0)[0]
    if c.size:
        RLIM[i] = (nR[c[0]], nR[c[-1]])

a = Dataset('air.mon.v501.ltm.1981-2010.nc')
p = Dataset('precip.mon.v501.ltm.1981-2010.nc')
lat = a.variables['lat'][:].astype(float)
lon = a.variables['lon'][:].astype(float)
T = np.ma.filled(a.variables['air'][:].astype(float), np.nan)
P = np.ma.filled(p.variables['precip'][:].astype(float), np.nan)
R = (P * 10.0) / DAYS[:, None, None]
lon180 = np.where(lon > 180, lon - 360, lon)
m1 = (lon180 >= 66) & (lon180 <= 142)
m2 = (lat >= -12) & (lat <= 38)
T = T[:, m2][:, :, m1]; R = R[:, m2][:, :, m1]

tot = cold = hot = wet = dry = suit = 0
for m in range(12):
    t, r = T[m], R[m]
    ok = np.isfinite(t) & np.isfinite(r)
    ti = np.clip(np.round((np.nan_to_num(t) - nT[0]) / dT).astype(int), 0, nT.size - 1)
    ri = np.clip(np.round((np.nan_to_num(r) - nR[0]) / dR).astype(int), 0, nR.size - 1)
    S = ok & (MED[ti, ri] > 0)
    U = ok & ~S
    tlo, thi = TLIM[ri, 0], TLIM[ri, 1]
    rlo, rhi = RLIM[ti, 0], RLIM[ti, 1]
    # classify unsuitable cell-months
    is_wet = U & (np.isnan(tlo) | (r > np.nan_to_num(rhi, nan=1e9)))
    is_hot = U & ~is_wet & np.isfinite(thi) & (t > thi)
    is_cold = U & ~is_wet & np.isfinite(tlo) & (t < tlo)
    is_dry = U & ~is_wet & ~is_hot & ~is_cold
    tot += U.sum(); cold += is_cold.sum(); hot += is_hot.sum()
    wet += is_wet.sum(); dry += is_dry.sum(); suit += S.sum()

print('Baseline cell-months in the study region (UDel 1981-2010, median niche)')
print(f'  suitable                {suit:>7}')
print(f'  unsuitable              {tot:>7}')
for lbl, v in [('too cold', cold), ('too hot', hot),
               ('too wet (washout)', wet), ('other/unclassified', dry)]:
    print(f'    {lbl:<22}{v:>7}  ({100 * v / max(tot,1):>5.1f}% of unsuitable)')

print('\nWettest suitable and unsuitable months, to sanity-check the ceiling:')
allr = R[np.isfinite(R)]
print(f'  regional rainfall range {allr.min():.2f} to {allr.max():.2f} mm/day')
print(f'  niche washout ceiling   ~{np.nanmax(RLIM[:,1]):.1f} mm/day (max over temperature)')
