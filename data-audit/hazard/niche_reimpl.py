"""Independent Python reimplementation of the Kaye et al. (2024) ecological
niche for Aedes aegypti, verified against the lookup table published with
that paper.

Equilibrium adult population (from their M.m, decay = 1):

    q0  = (2 / (invg(T) * a(T))) * (1/p(T) + (48/73) * R / gamma(T))
    M*  = (1 - q0) * (73/96) * invg(T) * gamma(T),   clamped at 0

Thermal performance curves:
    a(T), gamma(T)  Briere    c*T*(T-T0)*sqrt(Tm-T)
    invg(T), p(T)   quadratic -c*(T-T0)*(T-Tm)

A location-month is suitable where M* > 0.
"""
import numpy as np, sys
from scipy.io import loadmat
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

THIN = 20  # matches LookupTableCreation.m


def chains():
    out = {}
    for v in ('a', 'gamma', 'invg', 'p'):
        c = loadmat(f'{v}_MCMC_results.mat')['burntchain'][:, ::THIN]
        out[v] = c
    return out


def briere(T, c):
    """c[0]*T*(T-c[1])*sqrt(c[2]-T); MATLAB real() gives 0 above c[2]"""
    T = np.asarray(T, float)[..., None]
    root = np.sqrt(np.clip(c[2] - T, 0, None))
    return np.clip(c[0] * T * (T - c[1]) * root, 0, None)


def quad(T, c):
    """-c[0]*(T-c[1])*(T-c[2])"""
    T = np.asarray(T, float)[..., None]
    return np.clip(-c[0] * (T - c[1]) * (T - c[2]), 0, None)


def Mstar(T, R, ch):
    """M* for scalar/array T and R (broadcast), over all MCMC samples."""
    aT = briere(T, ch['a'])
    gT = briere(T, ch['gamma'])
    iT = quad(T, ch['invg'])
    pT = quad(T, ch['p'])
    R = np.asarray(R, float)[..., None]
    with np.errstate(divide='ignore', invalid='ignore'):
        q0 = (2.0 / (iT * aT)) * ((1.0 / pT) + (48.0 / 73.0) * (R / gT))
        M = (1.0 - q0) * (73.0 / 96.0) * iT * gT
    M = np.where(np.isfinite(M), M, 0.0)
    return np.clip(M, 0, None)


if __name__ == '__main__':
    ch = chains()
    print('MCMC samples after thinning:', ch['a'].shape[1])

    ref = loadmat('MLookupTable.mat')
    T = ref['Temperatures'].ravel()
    R = ref['Rainfalls'].ravel()

    # reproduce the published grid
    mine_med = np.zeros((T.size, R.size))
    mine_mean = np.zeros((T.size, R.size))
    for i, t in enumerate(T):
        M = Mstar(np.full(R.shape, t), R, ch)   # (nR, nSamples)
        mine_med[i] = np.median(M, axis=-1)
        mine_mean[i] = M.mean(axis=-1)

    for name, mine in (('MedianM', mine_med), ('MeanM', mine_mean)):
        theirs = ref[name]
        d = np.abs(mine - theirs)
        both = (mine > 0) == (theirs > 0)
        print(f'\n{name}:')
        print(f'  max |difference|        {d.max():.3e}')
        print(f'  mean |difference|       {d.mean():.3e}')
        print(f'  suitability agreement   {both.mean() * 100:.4f}% of {both.size} cells')
        if not both.all():
            bad = np.argwhere(~both)
            print(f'  disagreeing cells: {len(bad)}  e.g. '
                  f'T={T[bad[0][0]]:.1f} R={R[bad[0][1]]:.1f}')

    np.savez_compressed('niche_python.npz', T=T, R=R,
                        MedianM=mine_med, MeanM=mine_mean)
    print('\nwrote niche_python.npz')
