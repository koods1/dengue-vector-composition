"""Add Ae. albopictus, using the thermal niches distributed with Kaye et al.

These niches are TEMPERATURE-ONLY thresholds derived from R0-based thermal
suitability models, not mechanistic equilibrium niches like Kaye's. They
therefore have no rainfall washout term. Species are compared WITHIN source
(Mordecai vs Mordecai, Ryan vs Ryan) so the comparison isolates species and
not model structure.

  Mordecai  Ae. aegypti     17.8 - 34.6 C
  Mordecai  Ae. albopictus  16.2 - 31.6 C
  Ryan      Ae. aegypti     21.3 - 34.0 C
  Ryan      Ae. albopictus  19.9 - 29.4 C
"""
import sys, json, csv
import numpy as np
from netCDF4 import Dataset
import geopandas as gpd
from shapely.geometry import Point
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

NICHE = {
    ('Mordecai', 'aegypti'):    (17.8, 34.6),
    ('Mordecai', 'albopictus'): (16.2, 31.6),
    ('Ryan', 'aegypti'):        (21.3, 34.0),
    ('Ryan', 'albopictus'):     (19.9, 29.4),
}
COUNTRIES = ['Malaysia', 'Indonesia', 'Thailand', 'Philippines', 'Vietnam',
             'India', 'Bangladesh', 'Cambodia', 'Sri Lanka']
NAMEFIX = {'Vietnam': ['Vietnam', 'Viet Nam']}

a = Dataset('air.mon.v501.ltm.1981-2010.nc')
lat = a.variables['lat'][:].astype(float); lon = a.variables['lon'][:].astype(float)
T = np.ma.filled(a.variables['air'][:].astype(float), np.nan)
lo180 = np.where(lon > 180, lon - 360, lon)
m1 = (lo180 >= 66) & (lo180 <= 142); m2 = (lat >= -12) & (lat <= 38)
T = T[:, m2][:, :, m1]
la, lo = lat[m2], lo180[m1]
land = np.isfinite(T[0])
print(f'region grid {T.shape}, {land.sum():,} land cells')

world = gpd.read_file('ne110.geojson')
LO, LA = np.meshgrid(lo, la)
pts = gpd.GeoDataFrame(geometry=[Point(x, y) for x, y in zip(LO.ravel(), LA.ravel())],
                       crs=world.crs)
j = gpd.sjoin(pts, world[['NAME', 'geometry']], how='left', predicate='within')
j = j[~j.index.duplicated(keep='first')]
cname = j['NAME'].values.reshape(LO.shape)

deltas = [0, 1, 2, 3, 4, 5]
res = {}
for (src, sp), (lo_t, hi_t) in NICHE.items():
    res[f'{src}_{sp}'] = {}
    for d in deltas:
        sm = np.zeros(T.shape[1:], float)
        for m in range(12):
            t = T[m] + d
            sm += (np.isfinite(t) & (t >= lo_t) & (t <= hi_t))
        sm[~land] = np.nan
        for c in COUNTRIES:
            msk = np.isin(cname, NAMEFIX.get(c, [c])) & land
            res[f'{src}_{sp}'].setdefault(c, []).append(
                float(np.nanmean(sm[msk])) if msk.sum() else np.nan)

for src in ('Mordecai', 'Ryan'):
    print(f'\n=== {src} thermal niches: suitable months per year ===')
    hdr = (f"{'country':<12}" + ''.join(f'{"+" + str(d):>7}' for d in deltas)
           + f"{'change':>8}")
    for sp in ('aegypti', 'albopictus'):
        print(f'  Ae. {sp}')
        print('  ' + hdr); print('  ' + '-' * (len(hdr)))
        for c in COUNTRIES:
            row = res[f'{src}_{sp}'][c]
            print(f'  {c:<12}' + ''.join(f'{v:>7.2f}' for v in row)
                  + f'{row[-1] - row[0]:>8.2f}')

print('\n=== species difference (albopictus minus aegypti), same source ===')
print(f"{'country':<12}{'Mordecai +0':>13}{'Mordecai +5':>13}"
      f"{'Ryan +0':>10}{'Ryan +5':>10}")
print('-' * 60)
for c in COUNTRIES:
    m0 = res['Mordecai_albopictus'][c][0] - res['Mordecai_aegypti'][c][0]
    m5 = res['Mordecai_albopictus'][c][-1] - res['Mordecai_aegypti'][c][-1]
    r0 = res['Ryan_albopictus'][c][0] - res['Ryan_aegypti'][c][0]
    r5 = res['Ryan_albopictus'][c][-1] - res['Ryan_aegypti'][c][-1]
    print(f'{c:<12}{m0:>13.2f}{m5:>13.2f}{r0:>10.2f}{r5:>10.2f}')

# does either species validate against the outbreak locations?
print('\n=== thermal niches vs the dengue-outbreak locations (n=48) ===')
rows = []
for r in csv.DictReader(open('niches/LiuDengueOutbreakLocations.csv', encoding='utf8')):
    try: rows.append(float(r['T']))
    except (KeyError, ValueError, TypeError): pass
Tl = np.array(rows)
for (src, sp), (lo_t, hi_t) in NICHE.items():
    ins = (Tl >= lo_t) & (Tl <= hi_t)
    print(f'  {src:<9} Ae. {sp:<11} {100 * ins.mean():>5.1f}% admitted')

json.dump(res, open('albopictus.json', 'w'), indent=1)
print('\nwrote albopictus.json')
