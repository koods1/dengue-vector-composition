"""Select GHCN-Daily stations in the ten study countries with long recent
records of both daily precipitation and daily mean temperature."""
import sys, collections
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

CC = {'IN': 'India', 'BG': 'Bangladesh', 'CE': 'Sri Lanka', 'TH': 'Thailand',
      'VM': 'Vietnam', 'RP': 'Philippines', 'ID': 'Indonesia', 'MY': 'Malaysia',
      'SN': 'Singapore', 'CB': 'Cambodia'}

meta = {}
for line in open('ghcnd-stations.txt', encoding='utf8', errors='replace'):
    sid = line[0:11]
    if sid[:2] in CC:
        meta[sid] = dict(lat=float(line[12:20]), lon=float(line[21:30]),
                         name=line[41:71].strip(), country=CC[sid[:2]])

inv = collections.defaultdict(dict)
for line in open('ghcnd-inventory.txt', encoding='utf8', errors='replace'):
    sid = line[0:11]
    if sid in meta:
        el = line[31:35].strip()
        inv[sid][el] = (int(line[36:40]), int(line[41:45]))

cands = collections.defaultdict(list)
for sid, e in inv.items():
    if 'PRCP' not in e:
        continue
    p0, p1 = e['PRCP']
    has_t = ('TAVG' in e) or ('TMAX' in e and 'TMIN' in e)
    if not has_t or p1 < 2018 or (p1 - p0) < 15:
        continue
    if 'TAVG' in e:
        t0, t1 = e['TAVG']
    else:
        t0 = max(e['TMAX'][0], e['TMIN'][0]); t1 = min(e['TMAX'][1], e['TMIN'][1])
    if t1 < 2018 or (t1 - t0) < 15:
        continue
    span = min(p1, t1) - max(p0, t0)
    cands[meta[sid]['country']].append((span, sid, meta[sid], max(p0, t0), min(p1, t1)))

print(f"{'country':<13}{'n':>4}  best stations (span, id, name)")
sel = {}
for c in CC.values():
    lst = sorted(cands.get(c, []), reverse=True)
    print(f'{c:<13}{len(lst):>4}  ', end='')
    if not lst:
        print('-- none --'); continue
    keep = lst[:3]
    sel[c] = keep
    print('; '.join(f'{s[1]} {s[2]["name"][:18]} ({s[3]}-{s[4]})' for s in keep))

with open('stations_selected.txt', 'w', encoding='utf8') as fh:
    for c, lst in sel.items():
        for span, sid, m, y0, y1 in lst:
            fh.write(f'{sid}\t{c}\t{m["name"]}\t{m["lat"]}\t{m["lon"]}\t{y0}\t{y1}\n')
print(f'\nwrote stations_selected.txt ({sum(len(v) for v in sel.values())} stations)')
