import urllib.request, json, csv, time, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
DS = 'd4eb19bc-fdce-415f-9a61-49b036009840'

def fetch(extra, tag, cap=25000):
    rows, off = [], 0
    while off < cap:
        url = (f'https://api.gbif.org/v1/occurrence/search?datasetKey={DS}'
               f'&limit=300&offset={off}{extra}')
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                d = json.loads(r.read().decode('utf8'))
        except Exception as e:
            print(f'  {tag} offset {off} failed: {type(e).__name__}', flush=True)
            break
        if off == 0:
            print(f'  {tag}: {d.get("count")} records', flush=True)
        for x in d['results']:
            la, lo = x.get('decimalLatitude'), x.get('decimalLongitude')
            if la is not None and lo is not None:
                rows.append((la, lo, x.get('year'), x.get('country')))
        off += 300
        if d.get('endOfRecords'):
            break
    return rows

reg = fetch('&decimalLatitude=-12,38&decimalLongitude=66,142', 'study region')
print(f'  got {len(reg)} georeferenced in region', flush=True)
with open('aegypti_occ_region.csv', 'w', newline='', encoding='utf8') as fh:
    w = csv.writer(fh); w.writerow(['lat', 'lon', 'year', 'country']); w.writerows(reg)
print('wrote aegypti_occ_region.csv', flush=True)
