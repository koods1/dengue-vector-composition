import csv, sys, collections
csv.field_size_limit(10**7)
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

TARGETS = {
    'SINGAPORE', 'MALAYSIA', 'INDONESIA', 'THAILAND', 'PHILIPPINES',
    'VIET NAM', 'VIETNAM', 'INDIA', 'BANGLADESH', 'CAMBODIA', 'SRI LANKA',
}

path = 'Spatial_extract_V1_3.csv'
stat = collections.defaultdict(lambda: {
    'rows': 0, 'sres': collections.Counter(), 'tres': collections.Counter(),
    'adm1': set(), 'adm2': set(), 'years': set(),
    'adm1_years': set(),          # years with any Admin1+ data
})

with open(path, encoding='utf-8', errors='replace', newline='') as fh:
    r = csv.DictReader(fh)
    for i, row in enumerate(r):
        c = (row['adm_0_name'] or '').strip().upper()
        if c not in TARGETS:
            continue
        s = stat[c]
        s['rows'] += 1
        sres = (row['S_res'] or '').strip()
        tres = (row['T_res'] or '').strip()
        s['sres'][sres] += 1
        s['tres'][tres] += 1
        y = (row['Year'] or '').strip()
        if y.isdigit():
            s['years'].add(int(y))
            if sres in ('Admin1', 'Admin2'):
                s['adm1_years'].add(int(y))
        a1 = (row['adm_1_name'] or '').strip()
        a2 = (row['adm_2_name'] or '').strip()
        if a1 and a1 != 'NA':
            s['adm1'].add(a1)
        if a2 and a2 != 'NA':
            s['adm2'].add(a2)

order = ['SINGAPORE', 'MALAYSIA', 'INDONESIA', 'THAILAND', 'PHILIPPINES',
         'VIET NAM', 'VIETNAM', 'INDIA', 'BANGLADESH', 'CAMBODIA', 'SRI LANKA']

print(f"{'country':<12} {'rows':>9} {'adm1':>5} {'adm2':>6} {'yrs':>11} "
      f"{'adm1 yrs (recent)':>19}  best_S  best_T")
print('-' * 108)
for c in order:
    if c not in stat:
        continue
    s = stat[c]
    ys = sorted(s['years'])
    a1y = sorted(y for y in s['adm1_years'] if y >= 2010)
    span = f"{ys[0]}-{ys[-1]}" if ys else '-'
    a1span = (f"{a1y[0]}-{a1y[-1]} (n={len(a1y)})" if a1y else 'NONE')
    bs = 'Admin2' if s['sres']['Admin2'] else ('Admin1' if s['sres']['Admin1'] else 'Admin0')
    bt = 'Week' if s['tres']['Week'] else ('Month' if s['tres']['Month'] else 'Year')
    print(f"{c:<12} {s['rows']:>9,} {len(s['adm1']):>5} {len(s['adm2']):>6} "
          f"{span:>11} {a1span:>19}  {bs:<7} {bt}")

print('\nS_res / T_res detail:')
for c in order:
    if c not in stat:
        continue
    s = stat[c]
    print(f"  {c:<12} S={dict(s['sres'])}")
    print(f"  {'':<12} T={dict(s['tres'])}")
