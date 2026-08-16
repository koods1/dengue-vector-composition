"""Why does daily forcing give fewer suitable months than monthly forcing,
when the clamp argument predicted the opposite? Decompose the flips."""
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
A = B = both = neither = 0          # A: monthly-suit only; B: daily-majority only
tot = 0
rain_when_A = []
frac_when_A = []
allmonths = []
for sid, country, name, lat, lon, y0, y1 in stations:
    try:
        rd = list(csv.DictReader(open(f'ghcn/{sid}.csv', encoding='utf8')))
    except FileNotFoundError:
        continue
    recs = collections.defaultdict(list)
    for r in rd:
        d = r.get('DATE', '')
        if len(d) < 10: continue
        try: pr = float(r['PRCP']) if r.get('PRCP') not in (None, '') else None
        except ValueError: pr = None
        t = None
        if r.get('TAVG'):
            try: t = float(r['TAVG'])
            except ValueError: pass
        if t is None and r.get('TMAX') and r.get('TMIN'):
            try: t = (float(r['TMAX']) + float(r['TMIN'])) / 2
            except ValueError: pass
        if pr is None or t is None: continue
        recs[(int(d[:4]), int(d[5:7]))].append((t, pr))
    for k, v in recs.items():
        if len(v) < 25: continue
        arr = np.array(v, float)
        Tm, Rm = arr[:, 0].mean(), arr[:, 1].mean()
        sm = bool(suit(Tm, Rm))
        sd = suit(np.full(arr.shape[0], Tm), arr[:, 1]).mean()
        tot += 1
        allmonths.append((Rm, sm, sd, arr[:, 1]))
        if sm and sd <= 0.5: A += 1; rain_when_A.append(Rm); frac_when_A.append(sd)
        elif (not sm) and sd > 0.5: B += 1
        elif sm and sd > 0.5: both += 1
        else: neither += 1

print(f'station-months analysed: {tot}\n')
print(f'  suitable under BOTH conventions            {both:>6}  ({100*both/tot:.1f}%)')
print(f'  unsuitable under BOTH                      {neither:>6}  ({100*neither/tot:.1f}%)')
print(f'  monthly says suitable, daily majority not  {A:>6}  ({100*A/tot:.1f}%)  <- disagreement')
print(f'  monthly says unsuitable, daily majority is {B:>6}  ({100*B/tot:.1f}%)  <- the monsoon case')

print(f'\nThe two disagreements do not cancel: {A} vs {B}.')
if rain_when_A:
    print(f'\nWhere monthly says suitable but most days are not:')
    print(f'  mean monthly rainfall in those months   {np.mean(rain_when_A):.1f} mm/day')
    print(f'  mean fraction of days suitable          {np.mean(frac_when_A):.2f}')

# distributional explanation
R_all = np.concatenate([m[3] for m in allmonths])
print(f'\nDaily rainfall distribution across all station-days (n={R_all.size:,}):')
for q in (50, 75, 90, 95, 99):
    print(f'  p{q:<3} {np.percentile(R_all, q):>7.1f} mm/day')
print(f'  mean {R_all.mean():>6.1f} mm/day')
print(f'  share of days above the ~18.6 mm/day washout ceiling: '
      f'{100 * (R_all > 18.6).mean():.1f}%')
print(f'  share of days with zero rain: {100 * (R_all == 0).mean():.1f}%')
