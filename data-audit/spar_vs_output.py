"""Does self-assessed IHR SPAR surveillance capacity agree with the
surveillance output these countries actually publish?

Observed output coded from the source assessment (Methods Table 1) as an
ordinal score: spatial resolution (0 national, 1 admin-1, 2 admin-2 or
finer) + frequency (0 annual, 1 monthly, 2 weekly, 3 daily).

The paper reports no correlation. With ten countries a rank correlation
carries no useful information, and the sweep below is the demonstration
rather than a result: the sign of rho depends on how the output measure is
coded, running from +0.31 (spatial resolution alone) to -0.59 (publication
frequency alone, dropping the two countries whose coding rests on the
weakest sources). Nothing downstream depends on any of these numbers. What
the paper uses is the ranking contrast -- maximum self-assessed score
alongside the least granular published output, and vice versa -- which the
disagreement table at the end prints directly.

Viet Nam and Cambodia are the two countries with no published guideline and
the least direct evidence: Viet Nam's national-only coding is established in
supplementary section 7.1, Cambodia's from the WHO Bulletin paper
co-authored by its national programme. They are retained, and also reported
dropped, as a sensitivity -- not because the coding is unsettled.
"""
import csv
import itertools
import os
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
D = os.path.dirname(os.path.abspath(__file__)) + '/gho'

# observed published output: (spatial, frequency), see Methods Table 1
OBS = {
    'Bangladesh':  (2, 3),   # district, daily
    'Malaysia':    (2, 3),   # district/locality, daily
    'Singapore':   (2, 2),   # cluster/locality, weekly
    'Sri Lanka':   (2, 2),   # district, weekly
    'Thailand':    (1, 2),   # province, weekly
    'Philippines': (1, 2),   # region, weekly
    'Indonesia':   (1, 2),   # province, weekly
    'India':       (1, 0),   # state, annual
    'Viet Nam':    (0, 2),   # national only, weekly
    'Cambodia':    (1, 1),   # province collected, monthly
}
WEAKEST_SOURCED = {'Viet Nam', 'Cambodia'}

CODINGS = {
    'spatial+freq':   lambda s, f: s + f,
    'spatial only':   lambda s, f: s,
    'freq only':      lambda s, f: f,
    '2*spatial+freq': lambda s, f: 2 * s + f,
    'spatial+2*freq': lambda s, f: s + 2 * f,
}
SETS = {
    'all ten': lambda c: True,
    'n=8':     lambda c: c not in WEAKEST_SOURCED,
}

vals = {}
with open(f'{D}/gho_latest.csv', encoding='utf8') as fh:
    for row in csv.DictReader(fh):
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
    den = (sum((a - mx) ** 2 for a in rx)
           * sum((b - my) ** 2 for b in ry)) ** 0.5
    return num / den if den else float('nan')


print(f"{'country':<13}{'SPAR C05':>9}{'obs spatial':>12}"
      f"{'obs freq':>9}{'obs total':>10}")
print('-' * 55)
rows = []
for c in sorted(OBS, key=lambda k: -(OBS[k][0] + OBS[k][1])):
    spar = float(vals[c]['SPAR C05 surveillance [value]'])
    s, f = OBS[c]
    print(f'{c:<13}{spar:>9.0f}{s:>12}{f:>9}{s + f:>10}')
    rows.append((c, spar, s, f))

print('\nRank correlation is NOT a result. It is reported only to show that '
      'its\nsign is an artefact of the output coding, at n=10.\n')
print(f"{'output coding':<16}{'set':<10}{'n':>3}{'rho':>8}")
print('-' * 37)
allrho = []
for (cname, fn), (sname, keep) in itertools.product(
        CODINGS.items(), SETS.items()):
    sub = [r for r in rows if keep(r[0])]
    rho = spearman([r[1] for r in sub], [fn(r[2], r[3]) for r in sub])
    allrho.append(rho)
    print(f'{cname:<16}{sname:<10}{len(sub):>3}{rho:>+8.2f}')
print(f'\nrange across {len(allrho)} codings: '
      f'{min(allrho):+.2f} to {max(allrho):+.2f}')

print('\nLargest disagreements, composite coding '
      '(SPAR rank minus observed rank):')
sp = sorted(rows, key=lambda r: -r[1])
ob = sorted(rows, key=lambda r: -(r[2] + r[3]))
spr = {r[0]: i for i, r in enumerate(sp)}
obr = {r[0]: i for i, r in enumerate(ob)}
for c in sorted(spr, key=lambda k: -abs(spr[k] - obr[k]))[:4]:
    print(f'  {c:<13} SPAR rank {spr[c] + 1:>2}, '
          f'observed rank {obr[c] + 1:>2}   (delta {obr[c] - spr[c]:+d})')
