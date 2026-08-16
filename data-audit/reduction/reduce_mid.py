"""Reduce the mid-century window (2046-2055) to monthly regional
climatologies.

Rewritten to be robust to interruption:
  - accumulates a running sum per (model, scenario, variable) instead of
    holding every file's array, cutting peak memory from ~2.8 GB to ~280 MB
  - checkpoints every 60 files, so a kill costs at most a minute of work and
    a restart resumes from the checkpoint
"""
import os, sys, glob, time, re, pickle
import numpy as np
from multiprocessing import Pool

W, E, S, N = 66.0, 142.0, -12.0, 38.0
NWORK = 5
CKPT = 'reduce_mid.ckpt'
OUT = 'ensemble_monthly_mid.npz'


def monthly_one(path):
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
    dates = num2date(t[:], t.units, calendar=getattr(t, 'calendar', 'standard'),
                     only_use_cftime_datetimes=False)
    mon = np.array([x.month for x in dates])
    out = np.full((12, mj.size, mi.size), np.nan, dtype='float32')
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
    return os.path.basename(path), out, lat[mj], lo[mi]


def key_of(name):
    var, rest = name.split('_day_')[0], name.split('_day_')[1].split('_')
    return f'{rest[0]}__{rest[1]}__{var}'


if __name__ == '__main__':
    files = sorted(f for f in glob.glob('ens/*.nc')
                   if re.search(r'_(204[6-9]|205[0-5])_', os.path.basename(f)))
    state = {'sum': {}, 'n': {}, 'done': set(), 'lat': None, 'lon': None}
    if os.path.exists(CKPT):
        state = pickle.load(open(CKPT, 'rb'))
        print(f'resuming: {len(state["done"])} files already reduced', flush=True)
    todo = [f for f in files if os.path.basename(f) not in state['done']]
    print(f'{len(files)} files, {len(todo)} to do, {NWORK} workers', flush=True)

    t0 = time.time()
    with Pool(NWORK) as pool:
        for i, (name, arr, la, lo) in enumerate(
                pool.imap_unordered(monthly_one, todo, chunksize=2), 1):
            k = key_of(name)
            # Accumulate sum and COUNT over finite values only. np.nansum
            # would turn an all-NaN (ocean) cell into 0, silently destroying
            # the land mask - which is exactly what went wrong first time.
            good = np.isfinite(arr)
            if k in state['sum']:
                state['sum'][k] += np.where(good, arr, 0.0)
                state['n'][k] += good
            else:
                state['sum'][k] = np.where(good, arr, 0.0).astype('float64')
                state['n'][k] = good.astype('int16')
            state['done'].add(name)
            state['lat'], state['lon'] = la, lo
            if i % 60 == 0:
                pickle.dump(state, open(CKPT, 'wb'))
                el = time.time() - t0
                print(f'  {i}/{len(todo)}  {el/60:.1f} min  '
                      f'ETA {(len(todo)-i)*(el/i)/60:.1f} min  [checkpointed]',
                      flush=True)

    import numpy as _np
    out = {}
    for k in state['sum']:
        n = state['n'][k]
        with _np.errstate(invalid='ignore', divide='ignore'):
            m = _np.where(n > 0, state['sum'][k] / _np.maximum(n, 1), _np.nan)
        out[k] = m.astype('float32')
    # every land cell should have contributed exactly 10 years
    mx = {k: int(state['n'][k].max()) for k in state['n']}
    bad = {k: v for k, v in mx.items() if v != 10}
    if bad:
        print(f'  !! wrong year counts: {bad}', flush=True)
    np.savez_compressed(OUT, lat=state['lat'], lon=state['lon'], **out)
    print(f'\nwrote {OUT}  {os.path.getsize(OUT)/1e6:.1f} MB  '
          f'({len(out)} combinations)  in {(time.time()-t0)/60:.1f} min')
    if os.path.exists(CKPT):
        os.remove(CKPT)
