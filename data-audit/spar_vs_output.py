"""Does self-assessed IHR SPAR surveillance capacity agree with the
surveillance output these countries actually publish?

Observed output coded from the source assessment (Methods Table 2) as an
ordinal score: spatial resolution (0 national, 1 admin-1, 2 admin-2 or
finer) + frequency (0 annual, 1 monthly, 2 weekly, 3 daily).
Viet Nam and Cambodia are coded provisionally pending confirmation and
are reported both included and excluded.
"""
import csv, os, sys, itertools
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
D = os.path.dirname(os.path.abspath(__file__)) + '/gho'

# observed published output: (spatial, frequency), see Methods Table 2
OBS = {
    'Bangladesh':  (2, 3),   # district, daily
    'Malaysia':    (2, 3),   # district/locality, daily
    'Singapore':   (2, 2),   # cluster/locality, weekly
    'Sri Lanka':   (2, 2),   # district, weekly
    'Thailand':    (1, 2),   # province, weekly
    'Philippines': (1, 2),   # region, weekly
    'Indonesia':   (1, 2),   # province, weekly
    'India':       (1, 0),   # state, annual
    'Viet Nam':    (0, 2),   # national only (provisional), weekly
    'Cambodia':    (1, 1),   # province collected, monthly (provisional)
}
PROVISIONAL = {'Viet Nam', 'Cambodia'}

vals = {}
with open(f'{D}/daci_gho_latest.csv', encoding='utf8') as fh:
    r = csv.DictReader(fh)
    for row in r:
        vals[row['country']] = row

def spearman(xs, ys):
    n = len(xs)
    def rank(v):
        order = sorted(range(n), key=lambda i: v[i])
        rk = [0.0] * n
        i = 0
        while i < n:
            j = i
            while j + 1 < n and v[order[j + 1]] == v[order[i]]:
                j += 1
            avg = (i + j) / 2 + 1
            for k in range(i, j + 1):
                rk[order[k]] = avg
            i = j + 1
        return rk
    rx, ry = rank(xs), rank(ys)
    mx, my = sum(rx) / n, sum(ry) / n
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = (sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry)) ** 0.5
    return num / den if den else float('nan')

print(f"{'country':<13}{'SPAR C05':>9}{'obs spatial':>12}{'obs freq':>9}{'obs total':>10}")
print('-' * 55)
rows = []
for c in sorted(OBS, key=lambda k: -(OBS[k][0] + OBS[k][1])):
    spar = float(vals[c]['SPAR C05 surveillance [value]'])
    s, f = OBS[c]
    flag = ' *' if c in PROVISIONAL else ''
    print(f'{c:<13}{spar:>9.0f}{s:>12}{f:>9}{s + f:>10}{flag}')
    rows.append((c, spar, s + f))
print('  * provisional, pending confirmation')

for label, keep in [('all ten', lambda c: True),
                    ('excluding provisional', lambda c: c not in PROVISIONAL)]:
    sub = [r for r in rows if keep(r[0])]
    rho = spearman([r[1] for r in sub], [r[2] for r in sub])
    print(f'\nSpearman rho, SPAR C05 vs observed output ({label}, n={len(sub)}): {rho:+.2f}')

print('\nLargest disagreements (SPAR rank minus observed rank):')
n = len(rows)
sp = sorted(rows, key=lambda r: -r[1])
ob = sorted(rows, key=lambda r: -r[2])
spr = {r[0]: i for i, r in enumerate(sp)}
obr = {r[0]: i for i, r in enumerate(ob)}
for c in sorted(spr, key=lambda k: -abs(spr[k] - obr[k]))[:4]:
    print(f'  {c:<13} SPAR rank {spr[c] + 1:>2}, observed rank {obr[c] + 1:>2}'
          f'   (delta {obr[c] - spr[c]:+d})')
