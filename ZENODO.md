# Zenodo deposit — metadata and procedure

The manuscript's Data sharing statement promises the analysis code and the
derived monthly climate reductions at a registered DOI. This file records
exactly what to enter, so the deposit can be reproduced or a new version cut
without re-deriving any of it.

**Upload by hand. Do not enable Zenodo's GitHub webhook integration.** The
three `.npz` reductions (149 MB) are not in git, so a webhook archive would
deposit code without data — which is not what the Data sharing statement
promises. One record holding both is what is wanted. The same trap defeats
git-lfs: Zenodo's archiver does not fetch LFS objects either, so it would
deposit pointer stubs.

---

## Files to upload

| File | Source | Size |
|---|---|---|
| `dengue-vector-composition-v1.0.0.zip` | `git archive` of the tagged release | ~2 MB |
| `ensemble_monthly.npz` | `C:\dengue-data\` | 63 MB |
| `ensemble_monthly_mid.npz` | `C:\dengue-data\` | 47 MB |
| `wlen_monthly.npz` | `C:\dengue-data\` | 39 MB |

Four files: the code archive and the three derived reductions. That is what
the Data sharing statement promises and all it promises.

Build the code archive from the tag so it matches the release exactly:

```bash
git tag -a v1.0.0 -m "Release accompanying the manuscript"
git push origin v1.0.0
git archive --format=zip --prefix=dengue-vector-composition-v1.0.0/ \
    -o dengue-vector-composition-v1.0.0.zip v1.0.0
```

Well inside Zenodo's 50 GB per-record limit.

---

## Metadata

**Resource type:** Software

> The deposit is predominantly code; the `.npz` files are derived outputs of
> it. "Software" also gives the right citation formatting and the software
> metadata fields. If a reviewer objects that the data should be findable as
> data, the alternative is two linked records — but one record matches what
> the Data sharing statement promises, so prefer this.

**Title**

```
Analysis code and derived data for "Shifting dengue vector composition under
warming in South and Southeast Asia: a change routine surveillance cannot
detect"
```

**Creators** — all five authors of the paper, in manuscript order. Use the
ROR-backed affiliation so it links properly.

| Name | ORCID | Affiliation |
|---|---|---|
| Doeurk, Bros | `0000-0003-3589-1985` | Institut Pasteur du Cambodge (ROR `03ht2dx40`) |
| Ghosh, Archita | `0009-0002-1303-4755` | Northeastern University (ROR `04t5xt781`) |
| Amiji, Mansoor M. | `0000-0001-6170-881X` | Northeastern University (ROR `04t5xt781`) |
| Ganguly, Auroop R. | `0000-0002-4292-4856` | Northeastern University (ROR `04t5xt781`) |
| Sundaram, Ravi | `0000-0001-5657-4298` | Northeastern University (ROR `04t5xt781`) |

All five ORCIDs were checksum-validated (ISO 7064 MOD 11-2). AG's is a
`0009-` prefix, which is simply a recently issued block, not an error. The
Institut Pasteur du Cambodge ROR was taken from the ROR API rather than
recalled; the exact-name record is `03ht2dx40`, and note that Institut Pasteur
du Laos and Institut Pasteur du Maroc are separate records that a loose search
returns alongside it.

**Creators, `CITATION.cff` and `LICENSE` all name the same five.** Keep them
that way: if the list is ever revised, revise all four places at once — this
table, `CITATION.cff`'s `authors`, `CITATION.cff`'s `preferred-citation`, and
`LICENSE` — or the record will contradict itself.

**Description** (Zenodo accepts HTML)

```html
<p>Analysis code and derived climate data supporting a study of how warming
changes the balance between the two dengue vectors in South and Southeast
Asia, and whether routine surveillance could observe that change.</p>

<p>Eight published ecological parameterisations for <em>Aedes aegypti</em>
and <em>Aedes albopictus</em> are tested against 48 recorded dengue outbreak
locations; the seven admitting at least 95% are retained as an ensemble, and
the Kaye 2.5th-percentile variant is refuted and excluded. That ensemble is
driven by eight CMIP6 models under three emissions pathways across ten
countries, giving 1,680 country-level estimates of the change in annual
suitable months between 2005&ndash;2014 and 2086&ndash;2095, with a
mid-century window added to date the crossing.</p>

<p>The deposit contains the analysis scripts together with the result files
they produced, so a reported number can be checked against its output
without re-running anything, plus the derived monthly climate reductions
(<code>ensemble_monthly.npz</code>, <code>ensemble_monthly_mid.npz</code>,
<code>wlen_monthly.npz</code>). Third-party inputs are not redistributed;
the fetch scripts retrieve them, and they are itemised with their terms in
<code>THIRD-PARTY-NOTICES.md</code>.</p>

<p>Development repository:
<a href="https://github.com/koods1/dengue-vector-composition">github.com/koods1/dengue-vector-composition</a></p>
```

**Licence:** MIT for the code. The derived `.npz` data files are CC-BY-4.0.
Add both if the Licences field accepts more than one; if it takes only one,
set MIT and state the data licence in the description.

**Version:** `v1.0.0`

**Language:** English

**Keywords:** dengue; *Aedes aegypti*; *Aedes albopictus*; climate change;
ecological niche modelling; vector composition; entomological surveillance;
CMIP6; Southeast Asia; South Asia

**Funding:** two sources, both named in the manuscript.

1. US National Science Foundation, award **2146502** —
   *D-ISN/Collaborative Research: Financial and Network Disruptions in
   Counterfeit and Illegal Medicines Trade* (to MMA and RS; also supported
   AG). Zenodo's grants field is backed by OpenAIRE, so search the award
   number rather than typing the funder free-text.
2. **AI for Climate and Sustainability (AI4CaS) Research Grant**, Office of
   the Provost, **Northeastern University** (to ARG). An internal
   institutional award, so OpenAIRE will almost certainly not have it — enter
   it as free-text under the funder Northeastern University (ROR
   `04t5xt781`), and do not spend time hunting for a grant record.

Resolved 16 August 2026; ARG's award was the open question here.

**Related identifiers**

| Relation | Identifier |
|---|---|
| is supplement to | *the journal article DOI — add on acceptance* |
| is derived from | `https://github.com/KayeARK/Climate_Change_NCV_Ae_Aegypti` |
| references | `10.7917/OFSG3345` — NEX-GDDP-CMIP6 v2.0 |
| references | `10.5061/dryad.47v3c` — Kraemer et al. occurrence compendium |
| references | `10.6084/m9.figshare.19609356.v3` — gridded population projections |
| is supplemented by | `https://github.com/koods1/dengue-vector-composition` |

---

## Before publishing

Zenodo records cannot be withdrawn by their owner. Settle these first:

1. **Read the generated files.** `README.md`, `LICENSE`,
   `THIRD-PARTY-NOTICES.md` and this file were drafted, not author-reviewed.

Three questions that were open are now closed, and should not be reopened:

- **AG's ORCID.** `0009-0002-1303-4755`, supplied 16 August 2026 and entered
  in the Creators table above and in `CITATION.cff`.

- **Third-party rights.** The Kaye et al. MIT notice is reproduced verbatim
  from commit `1af467e`, fetched through the GitHub API rather than
  transcribed.
- **Copyright holder.** Vests in the authors; `LICENSE` names all five. The
  Northeastern policy check of 15 August 2026 covers the Northeastern authors;
  the fifth is named by the authors' own agreement. No institutional line is
  required for either institution.

## After publishing

Cite the **concept DOI** — labelled "Cite all versions" on the record page,
and usually the lower of the two numbers — in `main.tex`, `CITATION.cff` and
`README.md`. Never a version DOI. Published files are immutable, but issuing
a new version re-points the concept DOI, so the identifier printed in the
journal never goes stale.

If the DOI is needed at submission before the record is ready, reserve one on
the draft rather than publishing early.
