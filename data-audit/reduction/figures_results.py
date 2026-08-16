"""Result figures for the CMIP6 ensemble.

Two figures, replacing the two densest tables:

  fig3_divergence  species divergence and ensemble agreement, by country
  fig4_timing      when the one-month decline arrives, by scenario

Design constraints, in the order they were decided:

  form    Magnitude compared across countries for two named entities, with
          both signs present. That is a dot plot, not bars: bars imply a
          zero-anchored length that reads badly when values straddle zero,
          and a grouped bar chart of ten countries by two species is a
          thicket. Timing is two states of one quantity per country, which
          is a dumbbell.
  colour  Categorical, two slots, assigned to species and held fixed.
          #0072B2 / #D55E00 pass the six checks (worst adjacent pair
          dE 21.9 protan, 31.2 normal-vision, contrast >= 3:1 on white).
  print   The journal prints greyscale. Colour is never the only channel:
          the species differ in marker shape as well as hue, and the two
          horizons in the timing figure differ by fill.
"""
import io, json, sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

AEG, ALB = '#0072B2', '#D55E00'
INK, MUTED, GRID = '#1a1a1a', '#5c5c5c', '#d8d8d8'

MAINLAND = ['Cambodia', 'Thailand', 'Bangladesh', 'Sri Lanka', 'Vietnam', 'India']
MARITIME = ['Indonesia', 'Singapore', 'Philippines', 'Malaysia']
LABEL = {'Vietnam': 'Viet Nam'}

plt.rcParams.update({
    'font.family': 'DejaVu Sans', 'font.size': 8,
    'axes.edgecolor': MUTED, 'axes.labelcolor': INK, 'text.color': INK,
    'xtick.color': MUTED, 'ytick.color': INK,
    'axes.linewidth': 0.6, 'xtick.major.width': 0.6, 'ytick.major.width': 0,
    'figure.dpi': 200,
})


def order_and_ticks(ax):
    """Countries down the y axis, mainland block above maritime, with a
    rule between them rather than a colour change."""
    order = MAINLAND + MARITIME
    ypos = {c: len(order) - 1 - i for i, c in enumerate(order)}
    ax.set_yticks([ypos[c] for c in order])
    ax.set_yticklabels([LABEL.get(c, c) for c in order])
    ax.axhline(len(MARITIME) - 0.5, color=MUTED, lw=0.6, ls=(0, (4, 3)))
    ax.set_ylim(-0.6, len(order) - 0.4)
    for s in ('top', 'right', 'left'):
        ax.spines[s].set_visible(False)
    ax.grid(axis='x', color=GRID, lw=0.5)
    ax.set_axisbelow(True)
    return ypos


rows = json.load(open('decomposition.json'))['rows']


def stat(sp, c):
    v = np.array([r['change'] for r in rows
                  if r['species'] == sp and r['country'] == c])
    return v.mean(), 100.0 * np.mean(v < -0.25)


# ---------------------------------------------------------------- figure 3
fig, (axA, axB) = plt.subplots(1, 2, figsize=(7.2, 3.6), sharey=True,
                               gridspec_kw={'width_ratios': [1.15, 1],
                                            'wspace': 0.08})
ypos = order_and_ticks(axA)
order_and_ticks(axB)

for c in MAINLAND + MARITIME:
    y = ypos[c]
    (ma, aa), (mb, ab) = stat('aegypti', c), stat('albopictus', c)
    axA.plot([ma, mb], [y, y], color=GRID, lw=1.6, zorder=1,
             solid_capstyle='round')
    axA.plot(ma, y, 'o', ms=6, color=AEG, mec='white', mew=0.8, zorder=3)
    axA.plot(mb, y, 's', ms=5.5, color=ALB, mec='white', mew=0.8, zorder=3)
    axB.plot([aa, ab], [y, y], color=GRID, lw=1.6, zorder=1,
             solid_capstyle='round')
    axB.plot(aa, y, 'o', ms=6, color=AEG, mec='white', mew=0.8, zorder=3)
    axB.plot(ab, y, 's', ms=5.5, color=ALB, mec='white', mew=0.8, zorder=3)

axA.axvline(0, color=MUTED, lw=0.8, zorder=2)
axA.set_xlabel('Change in suitable months, 2005–2014 to 2086–2095')
axA.set_xlim(-4.9, 1.1)
axB.axvline(50, color=MUTED, lw=0.8, ls=(0, (2, 2)), zorder=2)
axB.set_xlabel('Ensemble members projecting a decline (%)')
axB.set_xlim(-4, 108)
axB.set_xticks([0, 25, 50, 75, 100])
axB.text(50, len(MAINLAND + MARITIME) - 0.75, 'coin flip', ha='center',
         va='bottom', fontsize=6.5, color=MUTED)

for ax, t in ((axA, 'A  Projected change'), (axB, 'B  Ensemble agreement')):
    ax.set_title(t, loc='left', fontsize=8.5, fontweight='bold', pad=8)

# The mainland/maritime grouping is carried by the rule and the caption.
# In-plot block labels collided with the data at every position tried.

fig.legend(handles=[
    Line2D([], [], marker='o', ls='', ms=6, color=AEG, mec='white',
           label='$\\it{Ae.\\ aegypti}$'),
    Line2D([], [], marker='s', ls='', ms=5.5, color=ALB, mec='white',
           label='$\\it{Ae.\\ albopictus}$')],
    loc='lower center', ncol=2, frameon=False, fontsize=8,
    bbox_to_anchor=(0.5, -0.02))
fig.subplots_adjust(left=0.13, right=0.99, top=0.90, bottom=0.20)
for ext in ('pdf', 'png'):
    fig.savefig(f'fig3_divergence.{ext}', bbox_inches='tight')
plt.close(fig)
print('wrote fig3_divergence.pdf / .png')

# ---------------------------------------------------------------- figure 4
cr = json.load(open('crossing.json'))
SCEN = [('ssp126', 'SSP1-2.6'), ('ssp245', 'SSP2-4.5'), ('ssp585', 'SSP5-8.5')]


def share(c, scen, by_end):
    sub = [r for r in cr if r['species'] == 'albopictus'
           and r['country'] == c and r['scenario'] == scen]
    keys = ('by 2050s', '2050s-2090s') if by_end else ('by 2050s',)
    return 100.0 * sum(r['bin'] in keys for r in sub) / len(sub)


fig, axes = plt.subplots(1, 3, figsize=(7.2, 3.4), sharey=True,
                         gridspec_kw={'wspace': 0.10})
for ax, (key, name) in zip(axes, SCEN):
    ypos = order_and_ticks(ax)
    for c in MAINLAND + MARITIME:
        y = ypos[c]
        a, b = share(c, key, False), share(c, key, True)
        ax.plot([a, b], [y, y], color=ALB, lw=1.6, alpha=0.45, zorder=1,
                solid_capstyle='round')
        ax.plot(b, y, 'o', ms=5.5, color=ALB, mec='white', mew=0.8, zorder=3)
        ax.plot(a, y, 'o', ms=5.5, mfc='white', mec=ALB, mew=1.3, zorder=4)
    ax.set_xlim(-6, 112)
    ax.set_xticks([0, 50, 100])
    ax.set_title(name, loc='left', fontsize=8.5, fontweight='bold', pad=8)

axes[1].set_xlabel('$\\it{Ae.\\ albopictus}$ ensemble members already one '
                   'month below the historical value (%)')

fig.legend(handles=[
    Line2D([], [], marker='o', ls='', ms=5.5, mfc='white', mec=ALB, mew=1.3,
           label='by the 2050s'),
    Line2D([], [], marker='o', ls='', ms=5.5, color=ALB, mec='white',
           label='by the 2090s')],
    loc='lower center', ncol=2, frameon=False, fontsize=8,
    bbox_to_anchor=(0.5, -0.02))
fig.subplots_adjust(left=0.13, right=0.99, top=0.90, bottom=0.22)
for ext in ('pdf', 'png'):
    fig.savefig(f'fig4_timing.{ext}', bbox_inches='tight')
plt.close(fig)
print('wrote fig4_timing.pdf / .png')
