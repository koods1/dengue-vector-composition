# Third-party notices

## Ecological niche model — Kaye et al.

The mechanistic niche implementation in `data-audit/hazard/niche_reimpl.py`
and `data-audit/niche/niche.py` is derived from:

- Repository: `github.com/KayeARK/Climate_Change_NCV_Ae_Aegypti`
- Commit: `1af467e`
- Licence: MIT

Two validation location sets distributed with that repository are
redistributed here under the same licence:

- `data-audit/nichevalid/KraemerMosquitoLocations.csv`
- `data-audit/nichevalid/LiuDengueOutbreakLocations.csv`

The MIT licence requires that the original copyright notice and permission
notice be retained in redistributions. The text below is reproduced verbatim
from `LICENSE` in that repository at commit `1af467e`, retrieved 15 August
2026.

```
MIT License

Copyright (c) 2023 Alexander Kaye

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

The persistence condition itself was re-derived for this work rather than
copied, and verified symbolically
(`data-audit/hazard/persistence_check.py`); the implementation reproduces the
published lookup table to machine precision across all 120,701
temperature–rainfall combinations.

## Alternative parameterisations

Thermal suitability bounds for both vectors are taken from published work
and used as parameters, not as code:

- Mordecai et al., temperature-dependent trait fits.
- Ryan et al., $R_0$-based suitability bounds.
- Liu-Helmersson et al., alternative mechanistic parameterisation, as
  distributed with the Kaye repository.

Full citations are in the manuscript.

## Data sources

Not redistributed here; retrieved by the fetch scripts. Each carries its own
terms, all permitting research use:

| Source | Terms |
|---|---|
| NEX-GDDP-CMIP6 v2.0 (NASA, doi:10.7917/OFSG3345) | US Government work, unrestricted |
| University of Delaware air temperature and precipitation v5.01 (NOAA PSL) | Public domain |
| GHCN-Daily (NOAA NCEI) | Public domain |
| Natural Earth 1:10m / 1:110m | Public domain |
| Kraemer et al. *Ae. aegypti* occurrence, Dryad doi:10.5061/dryad.47v3c | CC0 |
| WHO Global Health Observatory, IHR SPAR capacities C01 and C05 | WHO terms of use, attribution required |
| Gridded population projections, doi:10.6084/m9.figshare.19609356.v3 | CC-BY-4.0 |

The Asia Dengue Policy Working Group policy mapping report is cited as
published literature and **no part of it is reproduced** in this repository.

## Copyright holder

Settled: copyright vests in the authors, and the `LICENSE` file names the
four of them. Checked against Northeastern University policy, 15 August 2026.
No institutional copyright line is required and none should be added.
