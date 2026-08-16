"""Reduce the raw NEX-GDDP ensemble to monthly regional climatologies.

640 daily global files -> for each (model, scenario, variable) a single
12 x lat x lon array of monthly means over the 10-year window. The result is
a few megabytes and the raw archive can then be deleted.

Parallel across files; the job is decompression-bound.
"""
import os, sys, glob, time, collections
import numpy as np
from multiprocessing import Pool

W, E, S, N = 66.0, 142.0, -12.0, 38.0
NWORK = 6


def monthly_one(path):
    """daily -> 12 monthly means over the study window; masks fill values"""
    from netCDF4 import Dataset, num2date
    d = Dataset(path)
    lat = d.variables['lat'][:].astype(float)
    lon = d.variables['lon'][:].astype(float)
    lo = np.where(lon > 180, lon - 360, lon)
    mi = np.where((lo >= W) & (lo <= E))[0]
    mj = np.where((lat >= S) & (lat <= N))[0]
    var = 'tas' if 'tas_day' in os.path.basename(path) else 'pr'
    v = d.variables[var]
    v.set_auto_maskandscale(True)
    t = d.variables['time']
    # CMIP6 models use different calendars: proleptic_gregorian/standard,
    # 365_day (noleap), and 360_day (UKESM1-0-LL). Only cftime can represent
    # all three, and deriving month from a day index would misalign the
    # 360-day model by several days by December.
    dates = num2date(t[:], t.units, calendar=getattr(t, 'calendar', 'standard'),
                     only_use_cftime_datetimes=False)
    mon = np.array([x.month for x in dates])
    out = np.full((12, mj.size, mi.size), np.nan)
    for m in range(1, 13):
        idx = np.where(mon == m)[0]
        if idx.size == 0:
            continue
        acc = np.zeros((mj.size, mi.size)); cnt = np.zeros((mj.size, mi.size))
        for k in idx:
            day = np.ma.filled(v[k, mj[0]:mj[-1] + 1, mi[0]:mi[-1] + 1], np.nan)
            good = np.isfinite(day)
            acc += np.where(good, day, 0.0); cnt += good
        with np.errstate(invalid='ignore'):
            out[m - 1] = np.where(cnt > 0, acc / np.maximum(cnt, 1), np.nan)
    d.close()
    return path, out, lat[mj], lo[mi]


def key_of(path):
    n = os.path.basename(path)
    var, rest = n.split('_day_')[0], n.split('_day_')[1].split('_')
    return (rest[0], rest[1], var)          # model, scenario, variable


if __name__ == '__main__':
    files = sorted(glob.glob('ens/*.nc'))
    print(f'{len(files)} files, {NWORK} workers', flush=True)
    acc = collections.defaultdict(list)
    LA = LO = None
    t0 = time.time()
    with Pool(NWORK) as pool:
        for i, (path, arr, la, lo) in enumerate(
                pool.imap_unordered(monthly_one, files, chunksize=4), 1):
            acc[key_of(path)].append(arr)
            LA, LO = la, lo
            if i % 80 == 0:
                el = time.time() - t0
                print(f'  {i}/{len(files)}  {el/60:.1f} min  '
                      f'ETA {(len(files)-i)*(el/i)/60:.1f} min', flush=True)

    out = {}
    for (model, scen, var), arrs in acc.items():
        stack = np.stack(arrs)                      # years x 12 x lat x lon
        out[f'{model}|{scen}|{var}'] = np.nanmean(stack, axis=0).astype('float32')
        if len(arrs) != 10:
            print(f'  !! {model} {scen} {var}: {len(arrs)} years, expected 10')

    np.savez_compressed('ensemble_monthly.npz', lat=LA, lon=LO,
                        **{k.replace('|', '__'): v for k, v in out.items()})
    sz = os.path.getsize('ensemble_monthly.npz')
    print(f'\nwrote ensemble_monthly.npz  {sz/1e6:.1f} MB  '
          f'({len(out)} model-scenario-variable combinations)')
    print(f'total {(time.time()-t0)/60:.1f} min')
    print(f'reduction factor: {147.4e9/sz:,.0f}x')
