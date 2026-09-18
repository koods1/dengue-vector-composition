"""Map figure: projected change in suitable months, two species x three
pathways.

Run from the working directory that holds the reductions and the niche
lookup tables, as with decompose.py and figures_results.py. Writes
fig2_change_map.pdf and .png to the current directory; copy them to
figures/ in the manuscript tree.

This deliberately reuses decompose.py's niches, models and months() rather
than reimplementing them, and keeps the per-cell field instead of collapsing
to country means. It then recomputes the country means and prints them, so
the figure can be checked against decomposition_result.txt and cannot drift
from Table 3. All twenty agreed to two decimals when this was written.

No confidence hatching, deliberately. The obvious convention -- stipple
where fewer than two thirds of members agree on the sign -- flags only
3-7% of Ae. albopictus cells, whereas Table 3 reports 48-56% agreement in
the maritime tropics under the paper's stricter definition, a decline
exceeding 0.25 months. Both measures are defensible and they disagree
sharply, so putting one on the map beside the other in the table would read
as a contradiction. Agreement is reported once, in Table 3.
"""
import numpy as np
from scipy.io import loadmat
import geopandas as gpd
from shapely.geometry import Point
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm

CS = ['Malaysia', 'Indonesia', 'Thailand', 'Philippines', 'Vietnam',
      'India', 'Bangladesh', 'Cambodia', 'Sri Lanka', 'Singapore']
NAMEFIX = {'Vietnam': ['Vietnam', 'Viet Nam']}
SCEN = ['ssp126', 'ssp245', 'ssp585']
SCEN_LABEL = {'ssp126': 'SSP1-2.6', 'ssp245': 'SSP2-4.5', 'ssp585': 'SSP5-8.5'}
BOUNDS, BCOL = 'ne10_adm1.geojson', 'admin'

INK, MUTED, GRID = '#1a1a1a', '#5c5c5c', '#d8d8d8'
plt.rcParams.update({
    'font.family': 'DejaVu Sans', 'font.size': 8,
    'axes.edgecolor': MUTED, 'text.color': INK,
    'axes.linewidth': 0.6, 'figure.dpi': 200,
})

z = np.load('ensemble_monthly.npz')
LA, LO = z['lat'], z['lon']
MODELS = sorted({k.split('__')[0] for k in z.files if k not in ('lat', 'lon')})

kaye = loadmat('MLookupTable.mat')
kT, kR = kaye['Temperatures'].ravel(), kaye['Rainfalls'].ravel()
lh = loadmat('niches/LiuHelmersson_MLookupTable.mat')
lT, lR = lh['Temperatures'].ravel(), lh['Rainfalls'].ravel()


def grid_fn(G, Tax, Rax):
    dT, dR = Tax[1] - Tax[0], Rax[1] - Rax[0]

    def f(T, R):
        ok = (T >= Tax[0]) & (T <= Tax[-1]) & (R >= Rax[0]) & (R <= Rax[-1])
        i = np.clip(np.round((np.nan_to_num(T) - Tax[0]) / dT).astype(int),
                    0, Tax.size - 1)
        j = np.clip(np.round((np.nan_to_num(R) - Rax[0]) / dR).astype(int),
                    0, Rax.size - 1)
        return ok & (G[i, j] > 0)
    return f


def band_fn(lo, hi):
    return lambda T, R: np.isfinite(T) & (T >= lo) & (T <= hi)


NICHES = {
    'aegypti': {'Kaye median': grid_fn(kaye['MedianM'], kT, kR),
                'Kaye 97.5th': grid_fn(kaye['BiggestM'], kT, kR),
                'Liu-Helmersson': grid_fn(lh['MedianM'], lT, lR),
                'Mordecai': band_fn(17.8, 34.6),
                'Ryan': band_fn(21.3, 34.0)},
    'albopictus': {'Mordecai': band_fn(16.2, 31.6),
                   'Ryan': band_fn(19.9, 29.4)},
}


def months(model, scen, fn):
    T = z[f'{model}__{scen}__tas'] - 273.15
    R = z[f'{model}__{scen}__pr'] * 86400.0
    sm = np.zeros(T.shape[1:], float)
    for m in range(12):
        sm += fn(T[m], R[m])
    return sm


world = gpd.read_file(BOUNDS)
LOg, LAg = np.meshgrid(LO, LA)
pts = gpd.GeoDataFrame(
    geometry=[Point(x, y) for x, y in zip(LOg.ravel(), LAg.ravel())],
    crs=world.crs)
jn = gpd.sjoin(pts, world[[BCOL, 'geometry']], how='left', predicate='within')
jn = jn[~jn.index.duplicated(keep='first')]
cname = jn[BCOL].values.reshape(LOg.shape)
land = np.isfinite(z[f'{MODELS[0]}__historical__tas'][0])
MASK = {c: (np.isin(cname, NAMEFIX.get(c, [c])) & land) for c in CS}
STUDY = np.zeros_like(land)
for m in MASK.values():
    STUDY |= m
print(f'{len(MODELS)} models, {int(STUDY.sum())} study cells')

fields = {}
for sp, ns in NICHES.items():
    hist = {(n, m): months(m, 'historical', fn)
            for n, fn in ns.items() for m in MODELS}
    for s in SCEN:
        stack = np.stack([months(m, s, fn) - hist[(n, m)]
                          for n, fn in ns.items() for m in MODELS])
        fields[(sp, s)] = stack.mean(0)
    print(f'  Ae. {sp}: {stack.shape[0]} members per pathway')

W = np.cos(np.deg2rad(LA))[:, None] * np.ones((1, LO.size))
print('\nCountry mean change over the three pathways -- must match the '
      '"mean chg"\ncolumn of decomposition_result.txt')
for sp in ('aegypti', 'albopictus'):
    print(f'  Ae. {sp}')
    for c in CS:
        m = MASK[c]
        v = np.mean([np.average(fields[(sp, s)][m], weights=W[m])
                     for s in SCEN])
        print(f'    {c:<12}{v:>8.2f}')

rows = np.where(STUDY.any(axis=1))[0]
cols = np.where(STUDY.any(axis=0))[0]
pad = 4
r0, r1 = max(rows[0] - pad, 0), min(rows[-1] + pad + 1, LA.size)
c0, c1 = max(cols[0] - pad, 0), min(cols[-1] + pad + 1, LO.size)
extent = [LO[c0], LO[c1 - 1], LA[r0], LA[r1 - 1]]

study_names = [n for c in CS for n in NAMEFIX.get(c, [c])]
# Simplify before drawing. The 1:10m admin-1 file carries far more vertices
# than a 40 mm panel can show, and the outline is drawn six times: at full
# resolution the PDF came out at 21 MB. A 0.05 degree tolerance is about
# 5 km. At a 85 mm panel spanning 75 degrees one degree is about 1.1 mm, so
# that is well under print resolution. The simplification
# is cosmetic only -- the country masks above are built from the unsimplified
# geometry, so no cell is reassigned.
study_geom = world[world[BCOL].isin(study_names)].dissolve()
other_geom = world[~world[BCOL].isin(study_names)].dissolve()
study_geom['geometry'] = study_geom.simplify(0.05, preserve_topology=True)
other_geom['geometry'] = other_geom.simplify(0.12, preserve_topology=True)

# Diverging, symmetric about zero, one hue each side with a light neutral
# midpoint. Symmetric even though the positive tail reaches only about +3,
# because unequal arms would make a +1 cell look as strong as a -2 cell.
norm = TwoSlopeNorm(vmin=-6.0, vcenter=0.0, vmax=6.0)
cmap = plt.get_cmap('BrBG')

fig, axes = plt.subplots(3, 2, figsize=(7.1, 6.4), constrained_layout=True)
for j, sp in enumerate(('aegypti', 'albopictus')):
    for i, s in enumerate(SCEN):
        ax = axes[i, j]
        fld = np.where(STUDY, fields[(sp, s)], np.nan)[r0:r1, c0:c1]
        other_geom.plot(ax=ax, color='#f0f0f0', edgecolor='none', zorder=0)
        im = ax.imshow(fld, origin='lower', extent=extent, cmap=cmap,
                       norm=norm, interpolation='nearest', zorder=1,
                       rasterized=True)
        study_geom.boundary.plot(ax=ax, color=MUTED, linewidth=0.35, zorder=2)
        ax.set_xlim(extent[0], extent[1])
        ax.set_ylim(extent[2], extent[3])
        ax.set_aspect('equal')
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_edgecolor(GRID)
        if i == 0:
            ax.set_title(f'Ae. {sp}', fontsize=9, pad=4, style='italic')
        if j == 0:
            ax.text(-0.03, 0.5, SCEN_LABEL[s], transform=ax.transAxes,
                    rotation=90, va='center', ha='right', fontsize=8.5)

cb = fig.colorbar(im, ax=axes, orientation='horizontal', fraction=0.045,
                  pad=0.01, aspect=45, extend='both')
cb.set_label('Change in annual suitable months, 2005–2014 to '
             '2086–2095', fontsize=8)
cb.outline.set_edgecolor(MUTED)
cb.outline.set_linewidth(0.4)

fig.savefig('fig2_change_map.pdf', bbox_inches='tight', dpi=300)
fig.savefig('fig2_change_map.png', dpi=220, bbox_inches='tight')
print('\nwrote fig2_change_map.pdf and .png')
