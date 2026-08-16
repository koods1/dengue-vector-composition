"""Does the ten-year window length materially change the answer?

Only ten years per window were downloaded, so a twenty-year comparison is not
possible from the data held. The tractable equivalent is to split each
ten-year window into two five-year halves and ask how far the halves differ
from each other and from the full decade. That measures the quantity the
Methods flag: how much internal variability survives the averaging.

One model suffices for a sensitivity, so this uses GFDL-ESM4 alone --
about 9 GB rather than the 258 GB of the full ensemble.

Fetches, reduces, reports, and leaves the raw files for the caller to delete.
"""
import os, sys, time, urllib.request, urllib.parse
import xml.etree.ElementTree as ET
import numpy as np
from multiprocessing import Pool

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

B = 'https://nex-gddp-cmip6.s3.amazonaws.com/'
ROOT = 'NEX-GDDP-CMIP6'
NS = '{http://s3.amazonaws.com/doc/2006-03-01/}'
MODEL = 'GFDL-ESM4'
WINDOWS = {'historical': range(2005, 2015), 'ssp585': range(2086, 2096)}
VARS = ['tas', 'pr']
OUT = 'wlen'
W, E, S, N = 66.0, 142.0, -12.0, 38.0
os.makedirs(OUT, exist_ok=True)


def member():
    q = {'list-type': '2', 'prefix': f'{ROOT}/{MODEL}/historical/',
         'delimiter': '/', 'max-keys': '50'}
    with urllib.request.urlopen(B + '?' + urllib.parse.urlencode(q), timeout=90) as r:
        x = ET.fromstring(r.read())
    return x.findall(NS + 'CommonPrefixes')[0].find(NS + 'Prefix').text \
            .rstrip('/').split('/')[-1]


def fetch(mem):
    jobs = [(s, y, v) for s, yrs in WINDOWS.items() for y in yrs for v in VARS]
    print(f'{len(jobs)} files for {MODEL}', flush=True)
    got, t0 = 0, time.time()
    for i, (scen, y, v) in enumerate(jobs, 1):
        cands = [f'{v}_day_{MODEL}_{scen}_{mem}_gr1_{y}_v2.0.nc',
                 f'{v}_day_{MODEL}_{scen}_{mem}_gn_{y}_v2.0.nc']
        if any(os.path.exists(os.path.join(OUT, c))
               and os.path.getsize(os.path.join(OUT, c)) > 5e7 for c in cands):
            continue
        for c in cands:
            try:
                tmp = os.path.join(OUT, c + '.part')
                urllib.request.urlretrieve(
                    f'{B}{ROOT}/{MODEL}/{scen}/{mem}/{v}/{c}', tmp)
                os.replace(tmp, os.path.join(OUT, c))
                got += os.path.getsize(os.path.join(OUT, c))
                break
            except Exception:
                continue
        if i % 8 == 0:
            el = time.time() - t0
            print(f'  {i}/{len(jobs)}  {got/1e9:.1f} GB  '
                  f'ETA {(len(jobs)-i)*(el/max(i,1))/60:.0f} min', flush=True)
    print(f'downloaded {got/1e9:.1f} GB\n', flush=True)


def monthly(path):
    """Twelve monthly means over the study region for one file-year."""
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
    mon = np.array([x.month for x in num2date(
        t[:], t.units, calendar=getattr(t, 'calendar', 'standard'),
        only_use_cftime_datetimes=False)])
    out = np.full((12, mj.size, mi.size), np.nan, dtype='float32')
    for m in range(1, 13):
        idx = np.where(mon == m)[0]
        if idx.size == 0:
            continue
        acc = np.zeros((mj.size, mi.size)); cnt = np.zeros((mj.size, mi.size))
        for k in idx:
            day = np.ma.filled(v[k, mj[0]:mj[-1]+1, mi[0]:mi[-1]+1], np.nan)
            good = np.isfinite(day)
            acc += np.where(good, day, 0.0); cnt += good
        with np.errstate(invalid='ignore'):
            out[m-1] = np.where(cnt > 0, acc / np.maximum(cnt, 1), np.nan)
    d.close()
    return os.path.basename(path), out


if __name__ == '__main__':
    mem = member()
    fetch(mem)

    files = sorted(f for f in os.listdir(OUT) if f.endswith('.nc'))
    print(f'reducing {len(files)} files', flush=True)
    with Pool(5) as pool:
        red = dict(pool.imap_unordered(
            monthly, [os.path.join(OUT, f) for f in files], chunksize=2))
    np.savez_compressed('wlen_monthly.npz', **red)
    print(f'reduced {len(red)} file-years\n', flush=True)
