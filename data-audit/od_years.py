import csv, sys, collections
csv.field_size_limit(10**7)
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

TARGETS = ['SINGAPORE', 'MALAYSIA', 'INDONESIA', 'THAILAND', 'PHILIPPINES',
           'VIET NAM', 'INDIA', 'BANGLADESH', 'CAMBODIA', 'SRI LANKA']
T = set(TARGETS)

# country -> year -> best spatial res seen, and finest temporal res
sub = collections.defaultdict(lambda: collections.defaultdict(set))   # subnational rows
tmp = collections.defaultdict(lambda: collections.defaultdict(set))   # temporal res of subnational rows

with open('Spatial_extract_V1_3.csv', encoding='utf-8', errors='replace', newline='') as fh:
    for row in csv.DictReader(fh):
        c = (row['adm_0_name'] or '').strip().upper()
        if c not in T:
            continue
        y = (row['Year'] or '').strip()
        if not y.isdigit():
            continue
        s = (row['S_res'] or '').strip()
        if s in ('Admin1', 'Admin2'):
            sub[c][int(y)].add(s)
            tmp[c][int(y)].add((row['T_res'] or '').strip())

def runs(years):
    """compress sorted year list into ranges"""
    ys = sorted(years)
    if not ys:
        return 'NONE'
    out, start, prev = [], ys[0], ys[0]
    for y in ys[1:]:
        if y == prev + 1:
            prev = y; continue
        out.append(f'{start}-{prev}' if start != prev else f'{start}')
        start = prev = y
    out.append(f'{start}-{prev}' if start != prev else f'{start}')
    return ','.join(out)

print('Subnational (Admin1/Admin2) availability by year, OpenDengue V1.3\n')
for c in TARGETS:
    ys = sub.get(c, {})
    print(f'{c}')
    print(f'   subnational years : {runs(ys.keys())}')
    recent = sorted(y for y in ys if y >= 2015)
    print(f'   >=2015            : {runs(recent)}')
    if recent:
        tr = set()
        for y in recent:
            tr |= tmp[c][y]
        print(f'   temporal res >=2015: {sorted(tr)}')
    print()
