"""C. Publication figures.

Form choices:
  Fig 1 - a region in temperature-rainfall space with three NESTED parametric
          variants. Ordered set, so an ORDINAL ramp (one hue, light->dark),
          validated with validate_palette.js --ordinal (all checks pass). The
          ramp is ordered by RESTRICTIVENESS: the widest (97.5th percentile)
          niche takes the lightest step so the large area recedes, and the
          narrowest (2.5th) takes the darkest so the core carries emphasis.
          Observed study-region climate density is overlaid in muted ink as
          chrome, not as a series.
  Fig 2 - 9 countries x 3 niche variants = 27 series. Never cycle hues past 8,
          so countries become SMALL MULTIPLES and only the three ordered
          variants carry colour, reusing Fig 1's encoding so the same colour
          means the same thing in both figures.

Print PDF: no hover layer and no dark mode by design. The table-view twin is
Table 4 in the manuscript plus the CSVs under data-audit/.
"""
import json, sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
from scipy.io import loadmat
from netCDF4 import Dataset
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

SURFACE, INK, INK_2 = '#fcfcfb', '#0b0b0b', '#52514e'
MUTED, GRID, AXIS = '#898781', '#e1e0d9', '#c3c2b7'
STEP = ['#86b6ef', '#2a78d6', '#104281']        # ordinal 250 / 450 / 650
# index 0 = widest/least restrictive .. 2 = narrowest/most restrictive
COL = {'97.5th pct': STEP[0], 'median': STEP[1], '2.5th pct': STEP[2]}
LAB = {'97.5th pct': '97.5th percentile', 'median': 'median',
       '2.5th pct': '2.5th percentile'}
LEGEND_ORDER = ['97.5th pct', 'median', '2.5th pct']

plt.rcParams.update({
    'font.family': 'DejaVu Sans', 'font.size': 8,
    'figure.facecolor': SURFACE, 'axes.facecolor': SURFACE,
    'savefig.facecolor': SURFACE,
    'axes.edgecolor': AXIS, 'axes.linewidth': 0.6,
    'axes.labelcolor': INK_2, 'text.color': INK,
    'xtick.color': MUTED, 'ytick.color': MUTED,
    'xtick.labelcolor': INK_2, 'ytick.labelcolor': INK_2,
    'xtick.major.width': 0.6, 'ytick.major.width': 0.6,
    'grid.color': GRID, 'grid.linewidth': 0.5, 'grid.linestyle': '-',
    'legend.frameon': False, 'pdf.fonttype': 42,
})

lk = loadmat('MLookupTable.mat')
T, R = lk['Temperatures'].ravel(), lk['Rainfalls'].ravel()
GRIDS = {'2.5th pct': lk['SmallestM'], 'median': lk['MedianM'],
         '97.5th pct': lk['BiggestM']}

# ===================== FIGURE 1 =====================
fig, ax = plt.subplots(figsize=(5.4, 4.0))
ax.set_axisbelow(True)
ax.grid(True)

DAYS = np.array([31, 28.25, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])
a = Dataset('air.mon.v501.ltm.1981-2010.nc'); p = Dataset('precip.mon.v501.ltm.1981-2010.nc')
lat = a.variables['lat'][:].astype(float); lon = a.variables['lon'][:].astype(float)
Tm = np.ma.filled(a.variables['air'][:].astype(float), np.nan)
Pm = np.ma.filled(p.variables['precip'][:].astype(float), np.nan)
Rm = (Pm * 10.0) / DAYS[:, None, None]
lo180 = np.where(lon > 180, lon - 360, lon)
m1 = (lo180 >= 66) & (lo180 <= 142); m2 = (lat >= -12) & (lat <= 38)
tt = Tm[:, m2][:, :, m1].ravel(); rr = Rm[:, m2][:, :, m1].ravel()
ok = np.isfinite(tt) & np.isfinite(rr)
H, xe, ye = np.histogram2d(tt[ok], rr[ok], bins=[80, 60], range=[[0, 40], [0, 30]])

# widest first so narrower regions sit on top; surface-coloured edge = the gap
for key in LEGEND_ORDER:
    Z = (GRIDS[key] > 0).T.astype(float)
    ax.contourf(T, R, Z, levels=[0.5, 1.5], colors=[COL[key]])
    ax.contour(T, R, Z, levels=[0.5], colors=[SURFACE], linewidths=1.6)

ax.contour(0.5 * (xe[1:] + xe[:-1]), 0.5 * (ye[1:] + ye[:-1]), H.T,
           levels=[30, 300], colors=[MUTED], linewidths=0.7, alpha=0.75)

ax.set_xlim(12, 38); ax.set_ylim(0, 26)
ax.set_xlabel('Monthly mean temperature (°C)')
ax.set_ylabel('Mean daily rainfall (mm/day)')
ax.set_title('Conditions permitting $\\it{Aedes\\ aegypti}$ persistence',
             color=INK, fontsize=9.5, pad=8, loc='left')
handles = [Patch(facecolor=COL[k], edgecolor='none', label=LAB[k]) for k in LEGEND_ORDER]
handles.append(Line2D([0], [0], color=MUTED, lw=0.7, label='study-region climate'))
ax.legend(handles=handles, loc='upper center', bbox_to_anchor=(0.5, -0.16),
          ncol=4, fontsize=7, labelcolor=INK_2, handlelength=1.5,
          columnspacing=1.4)
for s in ('top', 'right'):
    ax.spines[s].set_visible(False)
fig.tight_layout(rect=[0, 0.03, 1, 1])
fig.savefig('fig1_niche.pdf'); fig.savefig('fig1_niche.png', dpi=200)
print('wrote fig1_niche.pdf / .png')

# ===================== FIGURE 2 =====================
D = json.load(open('param_uncert.json'))
deltas = [0, 1, 2, 3, 4, 5]
order = sorted(D['median'], key=lambda c: D['median'][c][-1] - D['median'][c][0])
CONSISTENT = {'India', 'Bangladesh', 'Vietnam'}

fig, axes = plt.subplots(3, 3, figsize=(6.8, 5.6), sharex=True, sharey=True)
for ax, c in zip(axes.ravel(), order):
    ax.set_axisbelow(True); ax.grid(True, axis='y')
    for key in LEGEND_ORDER:
        z = 3 if key == '2.5th pct' else (2 if key == 'median' else 1)
        ax.plot(deltas, D[key][c], color=COL[key], lw=1.6, marker='o', ms=3.4,
                mec=SURFACE, mew=0.9, zorder=z)
    ax.set_title(c + ('  •' if c in CONSISTENT else ''), fontsize=8.5,
                 color=INK, loc='left', pad=4)
    ax.set_ylim(0, 12.6); ax.set_yticks([0, 4, 8, 12]); ax.set_xticks(deltas)
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)
axes[2, 1].set_xlabel('warming above present (°C)')
axes[1, 0].set_ylabel('suitable months per year')
handles = [Line2D([0], [0], color=COL[k], lw=1.6, marker='o', ms=3.4,
                  mec=SURFACE, mew=0.9, label=LAB[k]) for k in LEGEND_ORDER]
fig.legend(handles=handles, loc='lower center', ncol=3, fontsize=7.5,
           labelcolor=INK_2, bbox_to_anchor=(0.5, 0.002), handlelength=1.8)
fig.suptitle('Projected suitability depends on the ecological parameterisation',
             x=0.01, ha='left', fontsize=9.5, color=INK)
fig.text(0.01, 0.932, '• direction of change is the same under all three variants',
         fontsize=7, color=MUTED, ha='left')
fig.tight_layout(rect=[0, 0.05, 1, 0.925])
fig.savefig('fig2_variants.pdf'); fig.savefig('fig2_variants.png', dpi=200)
print('wrote fig2_variants.pdf / .png')
print('panel order:', ', '.join(order))
