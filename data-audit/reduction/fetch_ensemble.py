"""Download a reduced but real CMIP6 ensemble for the variance decomposition.

Design: 8 models spanning the CMIP6 equilibrium-climate-sensitivity range,
3 SSPs, a 10-year end-century window and a 10-year historical baseline.
10-year windows are a compromise -- 20 would be better for internal
variability -- and this is stated in Methods.

Resumable: already-present files of plausible size are skipped.
"""
import urllib.request, urllib.parse, os, sys, time
import xml.etree.ElementTree as ET
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

B = 'https://nex-gddp-cmip6.s3.amazonaws.com/'
ROOT = 'NEX-GDDP-CMIP6'
NS = '{http://s3.amazonaws.com/doc/2006-03-01/}'
MODELS = ['INM-CM4-8', 'GFDL-ESM4', 'MIROC6',          # lower sensitivity
          'MPI-ESM1-2-HR', 'NorESM2-MM', 'ACCESS-ESM1-5',  # mid
          'CanESM5', 'UKESM1-0-LL']                    # higher
WINDOWS = {'historical': range(2005, 2015),
           'ssp126': range(2086, 2096),
           'ssp245': range(2086, 2096),
           'ssp585': range(2086, 2096)}
VARS = ['tas', 'pr']
OUT = 'ens'
os.makedirs(OUT, exist_ok=True)

def ls(prefix):
    q = {'list-type': '2', 'prefix': prefix, 'delimiter': '/', 'max-keys': '50'}
    with urllib.request.urlopen(B + '?' + urllib.parse.urlencode(q), timeout=90) as r:
        x = ET.fromstring(r.read())
    return [p.find(NS + 'Prefix').text for p in x.findall(NS + 'CommonPrefixes')]

ens = {}
for m in MODELS:
    try:
        e = ls(f'{ROOT}/{m}/historical/')
        ens[m] = e[0].rstrip('/').split('/')[-1]
    except Exception as ex:
        print(f'{m}: cannot resolve ensemble member ({ex})')
print('ensemble members:', ens, flush=True)

jobs = []
for m, member in ens.items():
    for scen, yrs in WINDOWS.items():
        for y in yrs:
            for v in VARS:
                jobs.append((m, member, scen, y, v))
print(f'{len(jobs)} files queued\n', flush=True)

done = bytes_got = 0
t0 = time.time()
for i, (m, member, scen, y, v) in enumerate(jobs, 1):
    fn = f'{v}_day_{m}_{scen}_{member}_gn_{y}_v2.0.nc'
    alt = f'{v}_day_{m}_{scen}_{member}_gr1_{y}_v2.0.nc'
    dest = os.path.join(OUT, alt)
    if os.path.exists(dest) and os.path.getsize(dest) > 5e7:
        done += 1; continue
    got = False
    for cand in (alt, fn):
        url = f'{B}{ROOT}/{m}/{scen}/{member}/{v}/{cand}'
        try:
            tmp = os.path.join(OUT, cand + '.part')
            urllib.request.urlretrieve(url, tmp)
            os.replace(tmp, os.path.join(OUT, cand))
            bytes_got += os.path.getsize(os.path.join(OUT, cand))
            got = True
            break
        except Exception:
            continue
    done += 1
    if not got:
        print(f'  MISS {m} {scen} {y} {v}', flush=True)
    if i % 20 == 0:
        el = time.time() - t0
        rate = bytes_got / el / 1e6 if el else 0
        eta = (len(jobs) - i) * (el / i) / 3600
        print(f'  {i}/{len(jobs)}  {bytes_got/1e9:.1f} GB  '
              f'{rate:.1f} MB/s  ETA {eta:.1f} h', flush=True)
print(f'\ncomplete: {done} files, {bytes_got/1e9:.1f} GB in '
      f'{(time.time()-t0)/3600:.2f} h')
