"""Is M* linear in rainfall? If so, the only source of monthly-averaging
bias is the clamp at zero, and its direction is determined by Jensen's
inequality rather than by anything empirical."""
import numpy as np, sys
sys.path.insert(0, '.')
from scipy.io import loadmat
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

THIN = 20
ch = {v: loadmat(f'{v}_MCMC_results.mat')['burntchain'][:, ::THIN]
      for v in ('a', 'gamma', 'invg', 'p')}

def briere(T, c):
    T = np.asarray(T, float)[..., None]
    return np.clip(c[0] * T * (T - c[1]) * np.sqrt(np.clip(c[2] - T, 0, None)), 0, None)

def quad(T, c):
    T = np.asarray(T, float)[..., None]
    return np.clip(-c[0] * (T - c[1]) * (T - c[2]), 0, None)

def Mstar_raw(T, R):
    """M* WITHOUT the clamp at zero"""
    aT, gT = briere(T, ch['a']), briere(T, ch['gamma'])
    iT, pT = quad(T, ch['invg']), quad(T, ch['p'])
    R = np.asarray(R, float)[..., None]
    with np.errstate(divide='ignore', invalid='ignore'):
        q0 = (2.0 / (iT * aT)) * ((1.0 / pT) + (48.0 / 73.0) * (R / gT))
        return (1.0 - q0) * (73.0 / 96.0) * iT * gT

T0 = 28.0
Rs = np.linspace(0, 40, 9)
M = np.array([np.median(Mstar_raw(np.array([T0]), np.array([r]))[0]) for r in Rs])
print(f'Unclamped median M* at T = {T0} C:')
for r, m in zip(Rs, M):
    print(f'  R = {r:5.1f} mm/day   M* = {m:+8.4f}')
d = np.diff(M) / np.diff(Rs)
print(f'\nfirst differences dM*/dR: min {d.min():.6f}  max {d.max():.6f}  '
      f'spread {d.max() - d.min():.2e}')
print('=> M* is LINEAR in R (pre-clamp)' if np.ptp(d) < 1e-9 else '=> not linear')

print('\nConsequence. Since the clamp max(0, .) is convex, for any within-month')
print('rainfall distribution:   mean_days[ max(0, M*(R_d)) ]  >=  max(0, M*(mean R))')
print('so forcing with monthly-mean rainfall can only UNDERSTATE suitability,')
print('never overstate it. The bias has a fixed sign; only its size is empirical.')

# how large, for a simple illustrative within-month distribution
print('\nIllustration: month of mean 20 mm/day, varying share of dry days')
for wet_frac in (1.0, 0.7, 0.5, 0.3):
    mean_R = 20.0
    wet_R = mean_R / wet_frac
    Rd = np.concatenate([np.full(int(100 * wet_frac), wet_R),
                         np.zeros(100 - int(100 * wet_frac))])
    daily = np.clip(Mstar_raw(np.full(Rd.shape, T0), Rd), 0, None)
    daily_med = np.median(daily, axis=-1)
    monthly = max(0.0, np.median(Mstar_raw(np.array([T0]), np.array([mean_R]))[0]))
    print(f'  {int(wet_frac*100):>3}% wet days at {wet_R:5.1f} mm/day: '
          f'daily-mean M* = {daily_med.mean():.4f}   monthly-mean M* = {monthly:.4f}   '
          f'suitable days = {(daily_med > 0).mean() * 100:.0f}%')
