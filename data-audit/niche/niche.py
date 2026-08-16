"""Characterise the Kaye et al. ecological niche from the published lookup
table, and quantify how much warming is required to push a location out of
it. Bears on whether the 'tropical contraction' signal in the underlying
thesis is mechanistically plausible within the Asian study region."""
import numpy as np, sys
from scipy.io import loadmat
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

d = loadmat('MLookupTable.mat')
T = d['Temperatures'].ravel()
R = d['Rainfalls'].ravel()
NICHE = {k: d[k] for k in ('MedianM', 'MeanM', 'SmallestM', 'BiggestM')}

def limits(M, r):
    """suitable temperature range at rainfall r"""
    j = int(np.argmin(np.abs(R - r)))
    col = M[:, j] > 0
    if not col.any():
        return None
    i = np.where(col)[0]
    return T[i[0]], T[i[-1]]

print('Median niche: suitable temperature range by rainfall')
print(f"{'rain mm/d':>10} {'T_min':>7} {'T_max':>7} {'width':>7}")
for r in [0, 0.5, 1, 2, 3, 5, 8, 12, 16, 20, 25, 30]:
    lim = limits(NICHE['MedianM'], r)
    if lim is None:
        print(f'{r:>10.1f}      -- unsuitable at all temperatures --')
    else:
        print(f'{r:>10.1f} {lim[0]:>7.1f} {lim[1]:>7.1f} {lim[1] - lim[0]:>7.1f}')

print('\nUpper thermal limit across the three niche variants (at 4 mm/day):')
for k in ('SmallestM', 'MedianM', 'BiggestM'):
    lim = limits(NICHE[k], 4)
    lbl = {'SmallestM': '2.5th pct', 'MedianM': 'median', 'BiggestM': '97.5th pct'}[k]
    print(f'  {lbl:>11}: {lim[0]:.1f} to {lim[1]:.1f} C')

# How much warming pushes a currently-suitable location out?
print('\nWarming headroom: degrees C of warming before a location at monthly')
print('mean T and 4 mm/day rainfall leaves the median niche')
lim = limits(NICHE['MedianM'], 4)
print(f"{'current T':>10} {'headroom':>10}")
for t in [24, 26, 27, 28, 29, 30, 31, 32]:
    head = lim[1] - t
    print(f'{t:>10.0f} {head:>10.1f}')

# rainfall ceiling
print('\nRainfall ceiling at 28 C (washout):')
i = int(np.argmin(np.abs(T - 28)))
row = NICHE['MedianM'][i, :] > 0
if row.any():
    j = np.where(row)[0]
    print(f'  suitable rainfall {R[j[0]]:.1f} to {R[j[-1]]:.1f} mm/day')
    print(f'  (upper bound is the larval flush-out term)')
