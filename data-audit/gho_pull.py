"""Pull D-ACI quantitative indicators for the ten study countries from the
WHO Global Health Observatory OData API. Writes a tidy CSV plus a
latest-value matrix. Reproducible: no auth required."""
import json, sys, time, urllib.request, csv, os

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

OUT = os.path.dirname(os.path.abspath(__file__)) + '/gho'
os.makedirs(OUT, exist_ok=True)

COUNTRIES = ['SGP', 'MYS', 'IDN', 'THA', 'PHL', 'VNM', 'IND', 'BGD', 'KHM', 'LKA']
NAME = {'SGP': 'Singapore', 'MYS': 'Malaysia', 'IDN': 'Indonesia', 'THA': 'Thailand',
        'PHL': 'Philippines', 'VNM': 'Viet Nam', 'IND': 'India', 'BGD': 'Bangladesh',
        'KHM': 'Cambodia', 'LKA': 'Sri Lanka'}

IND = {
    # SPAR 2nd edition capacity scores (1-5 scale, annual self-assessment)
    'IHRSPAR2_C01': 'SPAR C01 policy/legal',
    'IHRSPAR2_C03': 'SPAR C03 financing',
    'IHRSPAR2_C04': 'SPAR C04 laboratory',
    'IHRSPAR2_C05': 'SPAR C05 surveillance',
    'IHRSPAR2_C06': 'SPAR C06 human resources',
    'IHRSPAR2_C07': 'SPAR C07 health emergency mgmt',
    'IHRSPAR2_C08': 'SPAR C08 health services provision',
    # Health system resourcing
    'WHS6_102': 'Hospital beds per 10k',
    'HWF_0001': 'Medical doctors per 10k',
    'HWF_0006': 'Nurses/midwives per 10k',
    'WHS4_100': 'DTP3 coverage %',
    'GHED_GGHE-DGDP_SHA2011': 'Govt health exp % GDP',
    'GHED_OOPSCHE_SHA2011': 'OOP % of CHE',
    'UHC_INDEX_REPORTED': 'UHC service coverage index',
}

def fetch(code):
    url = f'https://ghoapi.azureedge.net/api/{code}'
    try:
        with urllib.request.urlopen(url, timeout=120) as r:
            return json.loads(r.read().decode('utf8'))['value']
    except Exception as e:
        print(f'  !! {code}: {e}')
        return []

rows = []
latest = {c: {} for c in COUNTRIES}
for code, label in IND.items():
    vals = fetch(code)
    keep = [v for v in vals if v.get('SpatialDim') in COUNTRIES
            and v.get('SpatialDimType') == 'COUNTRY']
    # prefer records with no sex/other disaggregation
    byc = {}
    for v in keep:
        c = v['SpatialDim']
        y = v.get('TimeDim')
        if y is None:
            continue
        val = v.get('NumericValue')
        if val is None:
            continue
        rows.append({'iso3': c, 'country': NAME[c], 'code': code, 'indicator': label,
                     'year': y, 'value': val})
        if c not in byc or y > byc[c][0]:
            byc[c] = (y, val)
    for c, (y, val) in byc.items():
        latest[c][label] = (y, val)
    print(f'{code:26s} {label:36s} n_countries={len(byc)}')
    time.sleep(0.2)

with open(f'{OUT}/daci_gho_tidy.csv', 'w', newline='', encoding='utf8') as fh:
    w = csv.DictWriter(fh, fieldnames=['iso3', 'country', 'code', 'indicator', 'year', 'value'])
    w.writeheader()
    w.writerows(sorted(rows, key=lambda r: (r['iso3'], r['code'], r['year'])))

labels = list(IND.values())
with open(f'{OUT}/daci_gho_latest.csv', 'w', newline='', encoding='utf8') as fh:
    w = csv.writer(fh)
    w.writerow(['country', 'iso3'] + [f'{l} [value]' for l in labels] + [f'{l} [year]' for l in labels])
    for c in COUNTRIES:
        vals = [latest[c].get(l, (None, None))[1] for l in labels]
        yrs = [latest[c].get(l, (None, None))[0] for l in labels]
        w.writerow([NAME[c], c] + vals + yrs)

print('\n=== LATEST VALUES ===')
hdr = f"{'country':<12}" + ''.join(f'{l[:15]:>17}' for l in labels[:7])
print(hdr)
for c in COUNTRIES:
    line = f'{NAME[c]:<12}'
    for l in labels[:7]:
        y, v = latest[c].get(l, (None, None))
        line += f'{(str(v) + " (" + str(y) + ")") if v is not None else "--":>17}'
    print(line)
print()
hdr = f"{'country':<12}" + ''.join(f'{l[:15]:>17}' for l in labels[7:])
print(hdr)
for c in COUNTRIES:
    line = f'{NAME[c]:<12}'
    for l in labels[7:]:
        y, v = latest[c].get(l, (None, None))
        line += f'{(str(round(v,1)) + " (" + str(y) + ")") if v is not None else "--":>17}'
    print(line)
print(f'\nwrote {OUT}/daci_gho_tidy.csv and daci_gho_latest.csv ({len(rows)} rows)')
