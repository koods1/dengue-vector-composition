# Shifting dengue vector composition under warming in South and Southeast Asia

Analysis code and derived data for:

> Doeurk B, Ghosh A, Amiji MM, Ganguly AR, Sundaram R. *Shifting dengue
> vector composition under warming in South and Southeast Asia: a change
> routine surveillance cannot detect.* Manuscript in submission, 2026.

Bros Doeurk and Archita Ghosh contributed equally and are joint first authors.

**Archived release:** [doi:10.5281/zenodo.22834784](https://doi.org/10.5281/zenodo.22834784)
— the concept DOI, which always resolves to the newest version. Cite this
one rather than a version DOI.

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
anything. They were produced in a single working directory (see
[Reproducing](#reproducing)) and copied back here.

| Path | Contents |
|---|---|
| `data-audit/pipeline/` | Hazard pipeline: daily fields → monthly means → niche evaluation → country aggregation, with its end-to-end verification |
| `data-audit/reduction/` | The CMIP6 ensemble: download and reduction, variance decomposition, crossing windows, leave-one-model-out, single-niche and window-length sensitivities, the *Ae. albopictus* upper-bound sweep |
| `data-audit/hazard/` | Niche reimplementation, symbolic verification of the persistence condition, contraction-mechanism attribution, thermal headroom |
| `data-audit/niche/`, `nichevalid/`, `validation/`, `validrange/` | Niche characterisation and validation against occurrence and outbreak location sets |
| `data-audit/albopictus/`, `consensus/` | Second-vector thermal bands; agreement across the niche ensemble |
| `data-audit/forcing/` | Monthly versus daily rainfall forcing, against GHCN-Daily stations |
| `data-audit/surveillance/`, `gho/` | National surveillance output; WHO IHR self-assessment comparator |
| `data-audit/exposure/`, `zonal/` | Population exposure and zonal aggregation |
| `data-audit/figures/` | Figure generation |
| `figures/` | Figures as they appear in the manuscript |

## Reproducing

### Environment

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

Prefer the versions pinned in `requirements.txt`. Newer releases leave the
numbers unchanged but can change how figures are drawn: geopandas 1.2, for
example, adds axis labels to the map panels of Fig. 2.

### Run every script from one working directory

Every script reads its inputs from, and writes its outputs to, the
**current working directory**. Paths are built into the scripts: none reads
an environment variable, and the only two that accept arguments
(`exposure/zipcd.py` and `exposure/zipget.py`) default to the values that
were used. The exceptions are `data-audit/gho_pull.py` and
`data-audit/spar_vs_output.py`, which use `data-audit/gho/` beside
themselves.

So make one working directory, put the files listed below in it, and run
every script from there:

```bash
mkdir work && cd work
# put the inputs listed below here, then, for example:
python ../data-audit/reduction/decompose.py
```

That is how the analysis was run. A re-run writes its output into the
working directory, not beside the script. Two committed result files,
`reduction/sensitivity_result.txt` and `reduction/window_length_result.txt`,
begin with `RuntimeWarning` lines: they are the original run's standard
error, captured with its output.

**Checked on 2 November 2026** from a clean copy of this repository and the
inputs below. Eleven scripts reproduce their committed outputs exactly:
`decompose.py`, `crossing.py`, `sensitivity.py`, `verify_mid.py`,
`albo_upper_bound.py`, `window_compare.py`, `asymmetry.py`, `figure_map.py`
and `figures_results.py` in `reduction/`; `hazard/contraction_mechanism.py`;
and `figures/figures.py`. With geopandas at its pinned version, all four
figures regenerate pixel for pixel.

### What goes in the working directory

**The three derived reductions**, `ensemble_monthly.npz` (historical and
end-century), `ensemble_monthly_mid.npz` (mid-century) and
`wlen_monthly.npz` (GFDL-ESM4 per year, for the window-length test), ~149 MB
together. They are **not in this repository**: download them from the
archived record (the DOI above). Most scripts in `reduction/` need one or
more of them, as does `hazard/contraction_mechanism.py`.

**Third-party inputs**, not redistributed here. Use the file names in the
first column, renaming on download where the source's name differs.

| File in the working directory | Source | Used by |
|---|---|---|
| `MLookupTable.mat` | Kaye et al. model repository, [KayeARK/Climate_Change_NCV_Ae_Aegypti](https://github.com/KayeARK/Climate_Change_NCV_Ae_Aegypti) at commit `1af467e`: `Figures/Figure1/EcologicalNicheGeneration/MLookupTable.mat` | most scripts that evaluate the niche |
| `niches/LiuHelmersson_MLookupTable.mat` | same repository: `Figures/Figure4/LiuHelmersson_Aegypti/MLookupTable.mat`, renamed | `reduction/decompose.py`, `crossing.py`, `figure_map.py`; `consensus/`; `nichevalid/` |
| `a_MCMC_results.mat`, `gamma_MCMC_results.mat`, `invg_MCMC_results.mat`, `p_MCMC_results.mat` | same repository: `Figures/FigureS2toS6/MCMC/Results/` | `hazard/niche_reimpl.py`, `forcing/linearity.py` |
| `air.mon.v501.ltm.1981-2010.nc`, `precip.mon.v501.ltm.1981-2010.nc` | University of Delaware v5.01 long-term monthly means, NOAA PSL: `downloads.psl.noaa.gov/Datasets/udel.airt.precip/` | baseline climatology in `pipeline/`, `hazard/`, `validation/`, `zonal/`, `exposure/`, `albopictus/`, `consensus/`, `figures/`, and `reduction/sensitivity.py` |
| `ne10_adm1.geojson` | Natural Earth v5.1.2 `ne_10m_admin_1_states_provinces.geojson`, from the `geojson/` folder of [nvkelso/natural-earth-vector](https://github.com/nvkelso/natural-earth-vector/tree/v5.1.2/geojson), renamed | country masks in `reduction/`, `pipeline/`, `zonal/`, `exposure/` |
| `ne110.geojson` | Natural Earth v5.1.2 `ne_110m_admin_0_countries.geojson`, same place, renamed | `albopictus/`, `consensus/`, `hazard/headroom.py`, `validation/param_uncert.py` |
| `ghcnd-stations.txt`, `ghcnd-inventory.txt` | NOAA GHCN-Daily station lists: `ncei.noaa.gov/pub/data/ghcn/daily/` | `forcing/pick_stations.py` only |
| `Spatial_extract_V1_3.csv` | OpenDengue V1.3 spatial extract | `data-audit/od_coverage.py`, `od_years.py` |

**Files from this repository, or made by its scripts.** Copy them in from
the directory named, or regenerate them with the script named.

| File in the working directory | Copy from | Or made by | Used by |
|---|---|---|---|
| `niches/KraemerMosquitoLocations.csv`, `niches/LiuDengueOutbreakLocations.csv` | `data-audit/nichevalid/` (from the Kaye repository's `Figures/FigureS7/`) | | `nichevalid/`, `albopictus/` |
| `niche_python.npz` | `data-audit/hazard/` | `hazard/niche_reimpl.py` | `hazard/`, `forcing/` |
| `stations_selected.txt` | `data-audit/forcing/` | `forcing/pick_stations.py` | `forcing/` |
| `decomposition.json`, `crossing.json` | `data-audit/reduction/` | `reduction/decompose.py`, `crossing.py` | `reduction/asymmetry.py`, `sensitivity.py`, `figures_results.py` |
| `param_uncert.json` | `data-audit/validation/` | `validation/param_uncert.py` | `figures/figures.py`, `validrange/validated_range.py` |
| `ghcn/` | | `forcing/fetch_daily.py` (NOAA NCEI) | `forcing/daily_vs_monthly.py`, `diagnose.py` |
| `aegypti_occ_region.csv` | | `validation/fetch_occ2.py`: the Kraemer et al. compendium (doi:10.5061/dryad.47v3c), from its GBIF copy (doi:10.15468/bgmqmr) | `validation/validate.py` |
| `pop/SSP2_2050.tif` | | `exposure/zipcd.py`, then `zipget.py` (figshare, doi:10.6084/m9.figshare.19609356.v3) | `exposure/` (development only; not reported in the paper) |
| `nex/` | | `pipeline/fetch_nex.py` (a pipeline test: one model, two years) | `pipeline/hazard_pipeline.py`, `verify_hist.py` |

WHO Global Health Observatory IHR SPAR scores are fetched by
`data-audit/gho_pull.py` into `data-audit/gho/`.

### Rebuilding the reductions from raw NEX-GDDP-CMIP6

The three `.npz` files can be rebuilt from NEX-GDDP-CMIP6 v2.0 daily fields
(doi:10.7917/OFSG3345), working in the same directory:

1. `reduction/fetch_ensemble.py` downloads the 640 files of the main
   ensemble (eight models; historical 2005–2014 and SSP1-2.6, SSP2-4.5 and
   SSP5-8.5 2086–2095; `tas` and `pr`) into `ens/`, about 258 GB.
   `reduction/reduce.py` then writes `ensemble_monthly.npz`.
2. `reduction/fetch_midcentury.py` adds the 2046–2055 files to `ens/`, and
   `reduction/reduce_mid.py` writes `ensemble_monthly_mid.npz`.
3. `reduction/window_length.py` downloads GFDL-ESM4 alone (about 9 GB) into
   `wlen/` and writes `wlen_monthly.npz`.

Each reduction works on files already downloaded, so the raw files must be
kept until it finishes; delete them afterwards. Only ten years per window
were ever retrieved, which is why the window-length sensitivity splits each
decade into halves rather than comparing twenty-year windows.
`fetch_ensemble.py` was missing from versions 1.0.0 and 1.0.1 of the
archived record; it was added, as it was run, in 1.0.2.

### Figures

The figure scripts write PDFs and PNGs into the working directory. The
manuscript uses the PDFs in `figures/`, which the scripts regenerate exactly.
The PNGs in `figures/` are 300 dpi; `figure_map.py` and `figures_results.py`
write theirs at 220 and 200 dpi, so those two PNGs come out smaller than the
ones here.

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
