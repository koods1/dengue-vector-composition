"""Download the minimum set of NEX-GDDP files needed to verify the hazard
pipeline end to end: one model, one historical year and one end-of-century
year under SSP5-8.5, temperature and precipitation.

This is a PIPELINE TEST, not a climatological result. Single years are
exactly what the analysis design rejects; the point here is only to prove
that download, monthly aggregation, niche evaluation and zonal aggregation
work against real CMIP6 input.
"""
import urllib.request, os, sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
B = 'https://nex-gddp-cmip6.s3.amazonaws.com/NEX-GDDP-CMIP6'
M, ENS = 'GFDL-ESM4', 'r1i1p1f1'
JOBS = [('historical', 2000), ('historical', 2000), ('ssp585', 2090), ('ssp585', 2090)]
VARS = ['tas', 'pr', 'tas', 'pr']
os.makedirs('nex', exist_ok=True)

for (scen, yr), var in zip(JOBS, VARS):
    fn = f'{var}_day_{M}_{scen}_{ENS}_gr1_{yr}_v2.0.nc'
    out = f'nex/{fn}'
    if os.path.exists(out) and os.path.getsize(out) > 1e8:
        print(f'{fn}  cached', flush=True); continue
    url = f'{B}/{M}/{scen}/{ENS}/{var}/{fn}'
    t0 = time.time()
    try:
        urllib.request.urlretrieve(url, out)
        sz = os.path.getsize(out)
        print(f'{fn}  {sz:,} bytes in {time.time()-t0:.0f}s', flush=True)
    except Exception as e:
        print(f'{fn}  FAILED {type(e).__name__}: {e}', flush=True)
print('done')
