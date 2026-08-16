import urllib.request, sys, os, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
os.makedirs('ghcn', exist_ok=True)
BASE = ('https://www.ncei.noaa.gov/access/services/data/v1?dataset=daily-summaries'
        '&stations={sid}&startDate=2005-01-01&endDate=2024-12-31'
        '&dataTypes=PRCP,TAVG,TMAX,TMIN&format=csv&units=metric')
rows = [l.rstrip('\n').split('\t') for l in open('stations_selected.txt', encoding='utf8')]
for sid, country, name, lat, lon, y0, y1 in rows:
    out = f'ghcn/{sid}.csv'
    if os.path.exists(out) and os.path.getsize(out) > 2000:
        print(f'{sid} {country:<12} cached'); continue
    try:
        with urllib.request.urlopen(BASE.format(sid=sid), timeout=180) as r:
            data = r.read()
        open(out, 'wb').write(data)
        print(f'{sid} {country:<12} {len(data):>9,} bytes  {name[:24]}')
    except Exception as e:
        print(f'{sid} {country:<12} FAILED {type(e).__name__}: {e}')
    time.sleep(0.4)
