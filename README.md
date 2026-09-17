# Shifting dengue vector composition under warming in South and Southeast Asia

Analysis code and derived data for:

> Doeurk B, Ghosh A, Amiji MM, Ganguly AR, Sundaram R. *Shifting dengue
> vector composition under warming in South and Southeast Asia: a change
> routine surveillance cannot detect.* Submitted to The Lancet Regional Health
> – Southeast Asia, 2026.

Bros Doeurk and Archita Ghosh contributed equally and are joint first authors.

**Archived release and DOI:** _to be added — see `CITATION.cff`._

Every input is publicly available and every result in the paper is
reproducible from them. Nothing proprietary is used, and nothing proprietary
is redistributed here.

---

## What the study does

Eight published ecological parameterisations for the two dengue vectors are
tested against 48 recorded dengue outbreak locations; the seven that admit
at least 95% of them are retained as an ensemble, and the Kaye
2.5th-percentile variant is refuted and excluded. That ensemble is driven by
eight CMIP6 models under three emissions pathways across ten countries —
1,680 country-level estimates — to ask how climatic suitability changes for
each vector separately. *Ae. aegypti* barely moves; the *Ae. albopictus*
season shortens by 1.3–4.3 months, with agreement split between mainland and
maritime Asia. The paper then asks whether routine national surveillance
could observe such a change, and mostly it could not.

## Layout

Paths match those cited in the paper's supplementary material, so a
reference such as `data-audit/reduction/verify_mid.py` resolves here.

Each analysis directory holds its scripts alongside the result files they
produced (`.txt` and `.json`). Those results are committed deliberately: they
are what the manuscript's numbers were read from, so a reader can check a
figure in the paper against the output that produced it without re-running
anything.

| Path | Contents |
|---|---|
| `data-audit/pipeline/` | Hazard pipeline: daily fields → monthly means → niche evaluation → country aggregation, with its end-to-end verification |
| `data-audit/reduction/` | The CMIP6 ensemble: variance decomposition, crossing windows, leave-one-model-out, single-niche and window-length sensitivities, the *Ae. albopictus* upper-bound sweep |
| `data-audit/hazard/` | Niche reimplementation, symbolic verification of the persistence condition, contraction-mechanism attribution, thermal headroom |
| `data-audit/niche/`, `nichevalid/`, `validation/`, `validrange/` | Niche characterisation and validation against occurrence and outbreak location sets |
| `data-audit/albopictus/`, `consensus/` | Second-vector thermal bands; agreement across the niche ensemble |
| `data-audit/forcing/` | Monthly versus daily rainfall forcing, against GHCN-Daily stations |
| `data-audit/surveillance/`, `gho/` | National surveillance output; WHO IHR self-assessment comparator |
| `data-audit/exposure/`, `zonal/` | Population exposure and zonal aggregation |
| `data-audit/figures/` | Figure generation |
| `figures/` | Figures as they appear in the manuscript |

## Reproducing

```bash
python -m venv .venv
.venv/Scripts/activate        # Windows;  source .venv/bin/activate  elsewhere
pip install -r requirements.txt
```

`geopandas` and `rasterio` pull compiled GDAL/GEOS/PROJ stacks. On Windows a
conda environment is materially less painful than pip:

```bash
conda create -n dengue python=3.11 numpy scipy matplotlib netcdf4 geopandas rasterio shapely h5py sympy
```

Then fetch the inputs (see below) and run any script directly; each is
standalone and writes its result beside itself.

## Data

**Derived monthly climate reductions** — `ensemble_monthly.npz` (historical
and end-century), `ensemble_monthly_mid.npz` (mid-century) and
`wlen_monthly.npz` (GFDL-ESM4 per-year, for the window-length test), ~149 MB
together — are **not in this repository**. They exceed what git should carry
and are published as files on the archived record; see `CITATION.cff`.
Download them and set `DENGUE_DATA` to the directory holding them.

**Third-party inputs are not redistributed here.** They are public, and the
fetch scripts retrieve them:

| Source | Retrieved by |
|---|---|
| NEX-GDDP-CMIP6 v2.0 daily fields (doi:10.7917/OFSG3345) | `data-audit/pipeline/fetch_nex.py`, `data-audit/reduction/fetch_midcentury.py` |
| University of Delaware v5.01 climatology | manual — see `data-audit/pipeline/verify_hist.py` |
| Natural Earth 1:10m and 1:110m boundaries | manual |
| GHCN-Daily station records | `data-audit/forcing/fetch_daily.py` |
| Kraemer et al. *Ae. aegypti* occurrence (doi:10.5061/dryad.47v3c) | `data-audit/validation/fetch_occ2.py` |
| WHO Global Health Observatory IHR SPAR scores | `data-audit/gho/`, `data-audit/gho_pull.py` |
| Gridded population projections (doi:10.6084/m9.figshare.19609356.v3) | `data-audit/exposure/zipget.py` |

Note that the raw NEX-GDDP archive is ~258 GB as downloaded; the reduction
to monthly means happens on arrival, per file, so peak storage stays modest.
Only ten years per window were ever retrieved, which is why the window-length
sensitivity splits each decade into halves rather than comparing twenty-year
windows.

## Licence

Code is MIT (`LICENSE`). Derived data files on the archived record are
CC-BY-4.0.

The ecological niche implementation is derived from the openly licensed
source of Kaye and colleagues, and two validation location sets are taken
from it. See `THIRD-PARTY-NOTICES.md` — that attribution is a condition of
the licence, not a courtesy.

## Citing

See `CITATION.cff`. Cite the **concept DOI**, which always resolves to the
newest version, rather than a version DOI.
