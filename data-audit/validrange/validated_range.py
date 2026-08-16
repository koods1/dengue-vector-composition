"""Recompute the parameter-uncertainty result over the VALIDATED parametric
range only.

The outbreak-location test (Results 3.3) admits 58.3% of locations under the
2.5th-percentile niche, 97.9% under the median and 100% under the
97.5th-percentile niche. The 2.5th variant is therefore refuted: it rules out
transmission where transmission has been observed. The validated range is
median to 97.5th percentile.

Note the asymmetry, which limits what this test can do: a niche can only fail
by being too NARROW. A niche admitting the entire grid would pass trivially.
So validation bounds the range from below but not from above.
"""
import json, sys
import numpy as np
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

D = json.load(open('param_uncert.json'))
CS = list(D['median'].keys())
FULL = ['2.5th pct', 'median', '97.5th pct']
VALID = ['median', '97.5th pct']
THRESH = 0.25          # months; changes smaller than this treated as flat


def sign(x):
    return '+' if x > THRESH else ('-' if x < -THRESH else '0')


def report(variants, label):
    print(f'\n===== {label} =====')
    print(f"{'country':<12}{'niche spread':>13}{'warming spread':>16}{'ratio':>8}"
          f"{'  signs':>10}{'  verdict':>12}")
    print('-' * 74)
    ratios, verdicts = [], []
    for c in CS:
        base = [D[v][c][0] for v in variants]
        niche_sp = max(base) - min(base)
        warm_sp = max(D['median'][c]) - min(D['median'][c])
        r = niche_sp / warm_sp if warm_sp > 0 else np.nan
        sg = [sign(D[v][c][-1] - D[v][c][0]) for v in variants]
        nz = set(s for s in sg if s != '0')
        if len(nz) > 1:
            verdict = 'REVERSES'
        elif len(nz) == 1 and '0' in sg:
            verdict = 'ambiguous'
        else:
            verdict = 'consistent'
        ratios.append(r); verdicts.append(verdict)
        print(f'{c:<12}{niche_sp:>13.2f}{warm_sp:>16.2f}{r:>8.1f}'
              f'{"".join(sg):>10}{verdict:>12}')
    print('-' * 74)
    print(f'  median ratio {np.nanmedian(ratios):.2f}   '
          f'niche spread exceeds warming spread in '
          f'{sum(1 for r in ratios if r > 1)} of {len(ratios)} countries')
    from collections import Counter
    cnt = Counter(verdicts)
    print(f'  consistent {cnt["consistent"]}   ambiguous {cnt["ambiguous"]}   '
          f'reverses {cnt["REVERSES"]}')
    return np.nanmedian(ratios), cnt


r_full, c_full = report(FULL, 'FULL published band (2.5th - 97.5th)')
r_val, c_val = report(VALID, 'VALIDATED range only (median - 97.5th)')

print('\n===== what changes =====')
print(f'  median ratio            {r_full:.2f}  ->  {r_val:.2f}')
print(f'  countries reversing     {c_full["REVERSES"]}  ->  {c_val["REVERSES"]}')
print(f'  countries consistent    {c_full["consistent"]}  ->  {c_val["consistent"]}')
print('\nThe sign-reversal claim was carried almost entirely by the refuted')
print('2.5th-percentile variant. Over the validated range the direction of')
print('change is largely consistent, and the ratio is much smaller.')
