"""Is the species divergence an artefact of unequal model structure?

The two vectors are not represented on equal footing. Ae. aegypti has
mechanistic temperature-AND-rainfall niches (Kaye, Liu-Helmersson) as well as
temperature-only bands (Mordecai, Ryan); Ae. albopictus has only the
temperature-only bands. A reviewer can reasonably ask whether the projected
divergence between the species is driven by that structural difference rather
than by ecology.

The test: restrict BOTH species to the temperature-only bands, which exist for
both and come from the same two model families. That is a matched comparison -
same variable set, same authors, same functional form. If the divergence
survives it is not an artefact of the rainfall term.
"""
import sys, json
import numpy as np
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

rows = json.load(open('decomposition.json'))['rows']
CS = ['Malaysia', 'Indonesia', 'Thailand', 'Philippines', 'Vietnam', 'India',
      'Bangladesh', 'Cambodia', 'Sri Lanka', 'Singapore']
TONLY = {'Mordecai', 'Ryan'}


def sel(sp, c, niches=None):
    return np.array([r['change'] for r in rows if r['species'] == sp
                     and r['country'] == c
                     and (niches is None or r['niche'] in niches)])


print('Mean change in suitable months, historical (2005-2014) -> 2086-2095\n')
print(f"{'':<13}{'MATCHED: T-only bands':>28}{'':>4}{'full ensemble':>26}")
print(f"{'country':<13}{'aegypti':>10}{'albo':>9}{'gap':>9}{'':>4}"
      f"{'aegypti':>10}{'albo':>9}{'gap':>9}")
print('-' * 80)
gm, gf = [], []
for c in CS:
    a, b = sel('aegypti', c, TONLY).mean(), sel('albopictus', c, TONLY).mean()
    A, B = sel('aegypti', c).mean(), sel('albopictus', c).mean()
    gm.append(b - a); gf.append(B - A)
    print(f'{c:<13}{a:>10.2f}{b:>9.2f}{b-a:>9.2f}{"":>4}'
          f'{A:>10.2f}{B:>9.2f}{B-A:>9.2f}')
print('-' * 80)
print(f'{"mean gap":<13}{"":>10}{"":>9}{np.mean(gm):>9.2f}{"":>4}'
      f'{"":>10}{"":>9}{np.mean(gf):>9.2f}')

print(f'\nSpecies gap under the matched comparison : {np.mean(gm):+.2f} months')
print(f'Species gap under the full ensemble      : {np.mean(gf):+.2f} months')
print(f'Difference attributable to model structure: '
      f'{abs(np.mean(gm) - np.mean(gf)):.2f} months')

# How much does dropping the rainfall-aware niches move aegypti alone?
d = [abs(sel('aegypti', c, TONLY).mean() - sel('aegypti', c).mean()) for c in CS]
print(f'\nLargest shift in the aegypti mean when its rainfall-aware niches are '
      f'removed: {max(d):.2f} months ({CS[int(np.argmax(d))]})')
print('The albopictus columns are identical by construction: that species has '
      'only\ntemperature-only niches, so the full ensemble IS the matched set '
      'for it.')

json.dump({'matched_gap': float(np.mean(gm)), 'full_gap': float(np.mean(gf)),
           'per_country': {c: {'matched': float(g), 'full': float(f)}
                           for c, g, f in zip(CS, gm, gf)}},
          open('asymmetry.json', 'w'), indent=1)
print('\nwrote asymmetry.json')
