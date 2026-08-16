"""Mid-century window (2046-2055) for the same 8 models and 3 SSPs, so that
threshold crossings can be expressed as dates rather than temperature offsets.

Same structure as fetch_ensemble.py and resumable in the same way: files
already present with plausible size are skipped, so this can be interrupted
and restarted freely.
"""
import urllib.request, urllib.parse, os, sys, time
import xml.etree.ElementTree as ET
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

B = 'https://nex-gddp-cmip6.s3.amazonaws.com/'
ROOT = 'NEX-GDDP-CMIP6'
NS = '{http://s3.amazonaws.com/doc/2006-03-01/}'
MODELS = ['INM-CM4-8', 'GFDL-ESM4', 'MIROC6',
          'MPI-ESM1-2-HR', 'NorESM2-MM', 'ACCESS-ESM1-5',
          'CanESM5', 'UKESM1-0-LL']
SCEN = ['ssp126', 'ssp245', 'ssp585']
YEARS = range(2046, 2056)
VARS = ['tas', 'pr']
OUT = 'ens'                      # same directory; filenames disambiguate by year
os.makedirs(OUT, exist_ok=True)


def ls(prefix):
    q = {'list-type': '2', 'prefix': prefix, 'delimiter': '/', 'max-keys': '50'}
    with urllib.request.urlopen(B + '?' + urllib.parse.urlencode(q), timeout=90) as r:
        x = ET.fromstring(r.read())
    return [p.find(NS + 'Prefix').text for p in x.findall(NS + 'CommonPrefixes')]


ens = {}
for m in MODELS:
    try:
        ens[m] = ls(f'{ROOT}/{m}/historical/')[0].rstrip('/').split('/')[-1]
    except Exception as e:
        print(f'{m}: cannot resolve ensemble member ({e})', flush=True)
print('members:', ens, flush=True)

jobs = [(m, ens[m], s, y, v) for m in ens for s in SCEN for y in YEARS for v in VARS]
print(f'{len(jobs)} files queued for 2046-2055\n', flush=True)

got_bytes = 0
t0 = time.time()
for i, (m, member, scen, y, v) in enumerate(jobs, 1):
    cands = [f'{v}_day_{m}_{scen}_{member}_gr1_{y}_v2.0.nc',
             f'{v}_day_{m}_{scen}_{member}_gn_{y}_v2.0.nc']
    if any(os.path.exists(os.path.join(OUT, c))
           and os.path.getsize(os.path.join(OUT, c)) > 5e7 for c in cands):
        continue
    ok = False
    for c in cands:
        try:
            tmp = os.path.join(OUT, c + '.part')
            urllib.request.urlretrieve(f'{B}{ROOT}/{m}/{scen}/{member}/{v}/{c}', tmp)
            os.replace(tmp, os.path.join(OUT, c))
            got_bytes += os.path.getsize(os.path.join(OUT, c))
            ok = True
            break
        except Exception:
            continue
    if not ok:
        print(f'  MISS {m} {scen} {y} {v}', flush=True)
    if i % 40 == 0:
        el = time.time() - t0
        print(f'  {i}/{len(jobs)}  {got_bytes/1e9:.1f} GB  '
              f'{got_bytes/el/1e6:.1f} MB/s  ETA {(len(jobs)-i)*(el/i)/3600:.1f} h',
              flush=True)

print(f'\ncomplete: {got_bytes/1e9:.1f} GB in {(time.time()-t0)/3600:.2f} h')
