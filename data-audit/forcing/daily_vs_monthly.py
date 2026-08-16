"""Does forcing the ecological niche with monthly-mean rainfall change
suitability, relative to evaluating it on daily rainfall?

Kaye et al. convert monthly mean rainfall to an average daily value and
evaluate the niche once per month. Because M* is linear in rainfall for
any given parameter draw, and the only nonlinearity is the clamp at
zero, monthly averaging can only understate suitability. This quantifies
by how much, using GHCN-Daily station records 2005-2024.
"""
import csv, sys, collections
import numpy as np
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

nz = np.load('niche_python.npz')
nT, nR, MED = nz['T'], nz['R'], nz['MedianM']
dT, dR = nT[1] - nT[0], nR[1] - nR[0]

def suit(T, R):
    T = np.asarray(T, float); R = np.asarray(R, float)
    ok = (T >= nT[0]) & (T <= nT[-1]) & (R >= nR[0]) & (R <= nR[-1])
    i = np.clip(np.round((np.nan_to_num(T) - nT[0]) / dT).astype(int), 0, nT.size - 1)
    j = np.clip(np.round((np.nan_to_num(R) - nR[0]) / dR).astype(int), 0, nR.size - 1)
    return ok & (MED[i, j] > 0)

stations = [l.rstrip('\n').split('\t') for l in open('stations_selected.txt', encoding='utf8')]
by_country = collections.defaultdict(list)

for sid, country, name, lat, lon, y0, y1 in stations:
    recs = collections.defaultdict(list)      # (year,month) -> [(tavg, prcp)]
    try:
        rd = list(csv.DictReader(open(f'ghcn/{sid}.csv', encoding='utf8')))
    except FileNotFoundError:
        continue
    for r in rd:
        d = r.get('DATE', '')
        if len(d) < 10:
            continue
        try:
            pr = float(r['PRCP']) if r.get('PRCP') not in (None, '') else None
        except ValueError:
            pr = None
        t = None
        if r.get('TAVG'):
            try: t = float(r['TAVG'])
            except ValueError: pass
        if t is None and r.get('TMAX') and r.get('TMIN'):
            try: t = (float(r['TMAX']) + float(r['TMIN'])) / 2
            except ValueError: pass
        if pr is None or t is None:
            continue
        recs[(int(d[:4]), int(d[5:7]))].append((t, pr))

    mono = daily = nmon = 0
    flips = 0
    for (yr, mo), v in recs.items():
        if len(v) < 25:            # require a near-complete month
            continue
        arr = np.array(v, float)
        Tm = arr[:, 0].mean()
        Rm = arr[:, 1].mean()      # mm/day, monthly mean
        s_month = bool(suit(Tm, Rm))
        s_daily = suit(np.full(arr.shape[0], Tm), arr[:, 1]).mean()   # fraction of days
        mono += s_month
        daily += s_daily
        nmon += 1
        if (not s_month) and s_daily > 0.5:
            flips += 1
    if nmon >= 60:
        by_country[country].append(
            dict(sid=sid, name=name, n=nmon,
                 monthly=12 * mono / nmon, daily=12 * daily / nmon,
                 flips=12 * flips / nmon))

print('Suitable months per year: monthly-mean rainfall forcing vs daily rainfall')
print('(temperature held at the monthly mean in both, to isolate the rainfall effect)\n')
print('WARNING: the two columns are NOT like for like and their difference is')
print('NOT an estimate of forcing bias. "monthly" counts each month as wholly')
print('suitable or wholly not; "daily" is the mean FRACTION of suitable days.')
print('A month with 80% suitable days scores 1.00 under the first and 0.80')
print('under the second, so "daily" reads lower almost by construction. The')
print('like-for-like comparison is the classification-flip count reported')
print('below, which is what Section sec:forcing of the paper cites.\n')
print(f"{'country':<13}{'station':<24}{'months':>7}{'monthly':>9}{'daily':>8}{'diff':>7}")
print('-' * 68)
tot_m = tot_d = 0.0
n = 0
for c in sorted(by_country):
    for s in by_country[c]:
        print(f"{c:<13}{s['name'][:23]:<24}{s['n']:>7}{s['monthly']:>9.2f}"
              f"{s['daily']:>8.2f}{s['daily'] - s['monthly']:>+7.2f}")
        tot_m += s['monthly']; tot_d += s['daily']; n += 1
print('-' * 68)
print(f"{'MEAN':<13}{'':<24}{'':>7}{tot_m / n:>9.2f}{tot_d / n:>8.2f}"
      f"{(tot_d - tot_m) / n:>+7.2f}")

print('\nBy country (station mean):')
print(f"{'country':<13}{'monthly':>9}{'daily':>8}{'diff':>7}")
for c in sorted(by_country):
    m = np.mean([s['monthly'] for s in by_country[c]])
    d = np.mean([s['daily'] for s in by_country[c]])
    print(f'{c:<13}{m:>9.2f}{d:>8.2f}{d - m:>+7.2f}')
