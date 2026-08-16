"""H. Hazard pipeline against real NEX-GDDP-CMIP6 input.

Steps: read daily tas/pr -> subset to study region -> aggregate to monthly
mean temperature and mean daily rainfall -> evaluate the ecological niche
per month -> suitable months per year -> zonal aggregate to units.

PIPELINE TEST ONLY. Single calendar years are used, which the analysis design
explicitly rejects (see Methods). Nothing here is a climatological result.
"""
import sys, glob, os, json
import numpy as np
from netCDF4 import Dataset
from scipy.io import loadmat
import geopandas as gpd
from rasterio.features import rasterize
from rasterio.transform import from_origin
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

W, E, S, N = 66.0, 142.0, -12.0, 38.0
CS = ['Singapore', 'Malaysia', 'Indonesia', 'Thailand', 'Philippines',
      'Vietnam', 'India', 'Bangladesh', 'Cambodia', 'Sri Lanka']

lk = loadmat('MLookupTable.mat')
nT, nR = lk['Temperatures'].ravel(), lk['Rainfalls'].ravel()
dT, dR = nT[1] - nT[0], nR[1] - nR[0]
VAR = {'2.5th pct': lk['SmallestM'], 'median': lk['MedianM'],
       '97.5th pct': lk['BiggestM']}


def monthly(path, name):
    """daily -> 12 monthly means over the study window"""
    d = Dataset(path)
    lat = d.variables['lat'][:].astype(float)
    lon = d.variables['lon'][:].astype(float)
    lo = np.where(lon > 180, lon - 360, lon)
    mi = np.where((lo >= W) & (lo <= E))[0]
    mj = np.where((lat >= S) & (lat <= N))[0]
    v = d.variables[name]
    t = d.variables['time']
    from netCDF4 import num2date
    dates = num2date(t[:], t.units, only_use_cftime_datetimes=False,
                     only_use_python_datetimes=True)
    mon = np.array([x.month for x in dates])
    v.set_auto_maskandscale(True)
    out = np.zeros((12, mj.size, mi.size), float)
    nfill = 0
    for m in range(1, 13):
        idx = np.where(mon == m)[0]
        acc = np.zeros((mj.size, mi.size), float)
        cnt = np.zeros((mj.size, mi.size), float)
        for k in idx:                      # one global chunk per day
            # masked array -> NaN, so fill values never enter the mean
            day = np.ma.filled(v[k, mj[0]:mj[-1] + 1, mi[0]:mi[-1] + 1], np.nan)
            good = np.isfinite(day)
            nfill += int((~good).sum())
            acc += np.where(good, day, 0.0)
            cnt += good
        with np.errstate(invalid='ignore', divide='ignore'):
            out[m - 1] = np.where(cnt > 0, acc / np.maximum(cnt, 1), np.nan)
    if nfill:
        print(f'    {name}: {nfill:,} masked cell-days excluded')
    return out, lat[mj], lo[mi]


def suitable_months(T, R, M):
    sm = np.zeros(T.shape[1:], float)
    for m in range(12):
        t, r = T[m], R[m]
        ok = np.isfinite(t) & np.isfinite(r)
        i = np.clip(np.round((np.nan_to_num(t) - nT[0]) / dT).astype(int), 0, nT.size - 1)
        j = np.clip(np.round((np.nan_to_num(r) - nR[0]) / dR).astype(int), 0, nR.size - 1)
        sm += (ok & (M[i, j] > 0))
    return sm


def run(scen, yr):
    ft = f'nex/tas_day_GFDL-ESM4_{scen}_r1i1p1f1_gr1_{yr}_v2.0.nc'
    fp = f'nex/pr_day_GFDL-ESM4_{scen}_r1i1p1f1_gr1_{yr}_v2.0.nc'
    for f in (ft, fp):
        if not os.path.exists(f):
            print(f'missing {f}'); return None
    Tk, la, lo = monthly(ft, 'tas')
    Pk, _, _ = monthly(fp, 'pr')
    T = Tk - 273.15                    # K -> degC
    R = Pk * 86400.0                   # kg m-2 s-1 -> mm/day
    print(f'  {scen} {yr}: T {np.nanmin(T):.1f}..{np.nanmax(T):.1f} C, '
          f'R {np.nanmin(R):.2f}..{np.nanmax(R):.2f} mm/day')
    return T, R, la, lo


if __name__ == '__main__':
    res = {}
    for scen, yr in (('historical', 2000), ('ssp585', 2090)):
        out = run(scen, yr)
        if out is None:
            sys.exit('pipeline test aborted: inputs not present')
        T, R, la, lo = out
        res[(scen, yr)] = {k: suitable_months(T, R, M) for k, M in VAR.items()}
        LA, LO = la, lo

    # zonal aggregation, reusing the E pipeline's approach.
    # NEX-GDDP latitude is ASCENDING (row 0 = southernmost). Raster transforms
    # are north-up by convention, so flip the fields to descending latitude
    # before rasterising, or unit masks end up vertically mirrored.
    if LA[0] < LA[-1]:
        LA = LA[::-1]
        for k in res:
            for v_ in res[k]:
                res[k][v_] = res[k][v_][::-1, :]
        print('  flipped fields to north-up for aggregation')
    g = gpd.read_file('ne10_adm1.geojson')
    g = g[g['admin'].isin(CS)].reset_index(drop=True)
    g['uid'] = np.arange(1, len(g) + 1)
    res_deg = abs(LO[1] - LO[0])
    tr = from_origin(LO[0] - res_deg / 2, LA[0] + res_deg / 2, res_deg, res_deg)
    uid = rasterize(((geom, int(u)) for geom, u in zip(g.geometry, g['uid'])),
                    out_shape=(LA.size, LO.size), transform=tr, fill=0, dtype='int32')
    wgt = np.cos(np.deg2rad(LA))[:, None] * np.ones((1, LO.size))

    print(f'\n{"country":<13}{"hist 2000":>11}{"ssp585 2090":>13}{"change":>9}')
    print('-' * 46)
    summary = {}
    for c in CS:
        m = np.isin(g['admin'].values, [c])
        ids = set(g['uid'].values[m])
        msk = np.isin(uid, list(ids))
        msk_use = msk
        if not msk_use.any():
            print(f'{c:<13}     -- no cells --'); continue
        row = {}
        for key in ('historical', 'ssp585'):
            yr = 2000 if key == 'historical' else 2090
            sm = res[(key, yr)]['median']
            row[key] = float(np.average(sm[msk_use], weights=wgt[msk_use]))
        summary[c] = row
        print(f'{c:<13}{row["historical"]:>11.2f}{row["ssp585"]:>13.2f}'
              f'{row["ssp585"] - row["historical"]:>9.2f}')
    json.dump(summary, open('pipeline_test.json', 'w'), indent=1)
    print('\nwrote pipeline_test.json')
    print('\nREMINDER: single years; pipeline verification only, not a result.')
