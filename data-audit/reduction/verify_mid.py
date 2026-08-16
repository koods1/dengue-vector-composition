"""Verify the mid-century reduction before anything is allowed to use it.

Attempt 2 of this reduction produced complete, correctly-shaped, plausible-
looking output that was wrong: np.nansum turned all-NaN ocean cells into 0 and
destroyed the land mask. Every check below exists because a silent bug of that
kind would otherwise reach the paper.
"""
import sys, numpy as np
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

zh = np.load('ensemble_monthly.npz')      # verified good
zm = np.load('ensemble_monthly_mid.npz')  # under test
fail = []

def check(ok, label, detail=''):
    print(f'  {"PASS" if ok else "FAIL"}  {label}{"  " + detail if detail else ""}')
    if not ok:
        fail.append(label)

print('1. grid identity with the verified historical reduction')
# If the mid grid differs from the historical grid by even one row, every
# country mask built from zh silently addresses the wrong cells in zm.
check(np.array_equal(zh['lat'], zm['lat']), 'lat axis identical',
      f"{zm['lat'].size} rows, {zm['lat'][0]:.2f}..{zm['lat'][-1]:.2f}")
check(np.array_equal(zh['lon'], zm['lon']), 'lon axis identical',
      f"{zm['lon'].size} cols, {zm['lon'][0]:.2f}..{zm['lon'][-1]:.2f}")

print('\n2. completeness')
keys = [k for k in zm.files if k not in ('lat', 'lon')]
models = sorted({k.split('__')[0] for k in keys})
scens = sorted({k.split('__')[1] for k in keys})
varis = sorted({k.split('__')[2] for k in keys})
check(len(keys) == 48, 'all 48 model x scenario x variable combinations',
      f'{len(models)} models x {len(scens)} scenarios x {len(varis)} vars = {len(keys)}')
check(sorted(models) == sorted({k.split('__')[0] for k in zh.files
                                if k not in ('lat', 'lon')}),
      'same 8 models as historical reduction')
check(scens == ['ssp126', 'ssp245', 'ssp585'], 'three scenarios, no historical')

print('\n3. the land mask survived (this is what attempt 2 destroyed)')
ref = zm['CanESM5__ssp245__tas']
nn = int(np.isnan(ref).sum())
nz = int((ref == 0).sum())
check(abs(nn - 432240) < 12000, 'CanESM5 ssp245 tas NaN count ~432,240', f'got {nn:,}')
check(nz == 0, 'no exact zeros in a temperature field', f'got {nz:,}')
# the NaN pattern must be identical across every field: ocean is ocean
pat = np.isnan(ref)
same = all(np.array_equal(np.isnan(zm[k]), pat) for k in keys if k.endswith('tas'))
check(same, 'identical NaN footprint across all tas fields')

print('\n4. physical plausibility')
mt = float(np.nanmean(ref)) - 273.15
check(15 < mt < 30, 'CanESM5 ssp245 regional mean T in 15-30 C', f'{mt:.2f} C')
hist_mt = float(np.nanmean(zh['CanESM5__historical__tas'])) - 273.15
end_mt = float(np.nanmean(zh['CanESM5__ssp245__tas'])) - 273.15
print(f'      historical {hist_mt:.2f} C  ->  mid {mt:.2f} C  ->  end {end_mt:.2f} C')
check(hist_mt < mt < end_mt, 'mid-century warming falls between hist and end')

print('\n5. all fields, coarse ranges')
for k in sorted(keys):
    a = zm[k]
    lo, hi = float(np.nanmin(a)), float(np.nanmax(a))
    if k.endswith('tas'):
        bad = not (220 < lo and hi < 340)
    else:
        bad = not (lo >= 0 and hi < 0.01)     # pr in kg m-2 s-1
    if bad:
        check(False, f'{k} out of range', f'{lo:.4g} .. {hi:.4g}')
n_ok = sum(1 for k in keys if not np.all(np.isnan(zm[k])))
check(n_ok == len(keys), 'no all-NaN fields', f'{n_ok}/{len(keys)} populated')

print('\n' + ('ALL CHECKS PASSED - safe to use' if not fail
              else f'{len(fail)} CHECK(S) FAILED: ' + '; '.join(fail)))
sys.exit(1 if fail else 0)
