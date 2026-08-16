"""Data-quality check on the population raster. nodata is declared as
255.0 on a float32 grid, which would collide with legitimate population
values if taken literally."""
import numpy as np, rasterio, sys
from rasterio.windows import from_bounds
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with rasterio.open('pop/SSP2_2050.tif') as ds:
    win = from_bounds(66, -12, 142, 38, ds.transform)
    a = ds.read(1, window=win)
    print('declared nodata:', ds.nodata, '| dtype', ds.dtypes[0])

fin = np.isfinite(a)
print(f'cells in window        {a.size:,}')
print(f'non-finite (NaN/inf)   {(~fin).sum():,}')
v = a[fin].astype('float64')
print(f'min {v.min():.4g}   max {v.max():.4g}   sum {v.sum()/1e6:,.1f} M')
print(f'negative values        {(v < 0).sum():,}')
print(f'exactly 255.0          {(v == 255.0).sum():,}')
print(f'in (254.5, 255.5)      {((v > 254.5) & (v < 255.5)).sum():,}')
print(f'in (250, 260)          {((v > 250) & (v < 260)).sum():,}')
tot_all = v[v > 0].sum()
tot_ex255 = v[(v > 0) & (v != 255.0)].sum()
print(f'\npopulation if 255.0 kept    {tot_all/1e6:,.2f} M')
print(f'population if 255.0 zeroed  {tot_ex255/1e6:,.2f} M')
print(f'difference                  {(tot_all-tot_ex255)/1e6:,.4f} M '
      f'({100*(tot_all-tot_ex255)/tot_all:.4f}%)')
# neighbours of 255-valued cells: if truly nodata they should cluster in ocean
i, j = np.where(fin & (a == 255.0))
if i.size:
    print(f'\n255.0 cells: {i.size:,}. Sample neighbourhood sums (3x3, excl centre):')
    for k in range(min(5, i.size)):
        r, c = i[k], j[k]
        blk = a[max(0,r-1):r+2, max(0,c-1):c+2].astype('float64')
        s = np.nansum(blk) - 255.0
        print(f'   at row {r}, col {c}: neighbours sum {s:.2f}')
