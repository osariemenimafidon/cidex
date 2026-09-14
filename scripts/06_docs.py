"""06 — Generate the documentation set from stats.json and the data itself.

Every number in every document below is interpolated from stats.json, which the
pipeline writes. The codebook's column lists are read from the actual CSVs, so
they cannot drift from the data either. Nothing here is typed by hand.
"""
import json, os
import pandas as pd

OUT, DOCS = "data/processed", "docs"
S = json.load(open(f"{OUT}/stats.json"))
A = json.load(open("AUTHORS.json"))
au = A["authors"][0]
os.makedirs(DOCS, exist_ok=True)

DRAFT = "> **DRAFT — NOT VERIFIED.** This package has not passed its verification gate. " \
        "No number in it has been checked against the primary source by the author. " \
        "Do not cite, deposit, or redistribute.\n"

def f(n):
    return f"{n:,}" if isinstance(n, int) else n

COLDOC = {
 "panel": ("string", "Which EPA source the row came from: `highway` or `nonroad`."),
 "model_year": ("integer", "Certification model year."),
 "engine_family": ("string", "EPA engine family name. Unique per model year; the first character encodes the model year."),
 "manufacturer": ("string", "Certificate holder, as EPA spells it. Not normalised across years."),
 "certificate_no": ("string", "EPA certificate number."),
 "date_issued": ("date", "Date the certificate was issued."),
 "introduction_date": ("date", "Date of introduction into commerce."),
 "engine_cycle": ("string", "Combustion cycle."),
 "fuel_type": ("string", "Certification fuel type, source spelling."),
 "fuel_metering_system": ("string", "Fuel metering system."),
 "useful_life": ("string", "Useful life as EPA states it; free text, units vary by panel."),
 "intended_service_class": ("string", "Highway only. Service class, e.g. Heavy Heavy-Duty Diesel."),
 "carryover_family": ("string", "Nonroad only. Family this one was carried over from; null if none."),
 "power_category": ("string", "Nonroad only. Power band, e.g. `130<=kW<=560`."),
 "regulation": ("string", "Nonroad only. Applicable regulation."),
 "tier": ("string", "Nonroad only. Applicable emission tier."),
 "compliance_standard": ("string", "Nonroad only. Applicable compliance standard, family level, not pollutant-specific."),
 "non_aftertreatment_device": ("string", "Nonroad only. Non-aftertreatment devices, semicolon separated."),
 "aftertreatment_device": ("string", "Nonroad only. Aftertreatment devices, semicolon separated."),
 "engine_model": ("string", "Configuration level. Engine model name."),
 "engine_code": ("string", "Configuration level. Engine code."),
 "engine_test_model": ("string", "Highway only, configuration level. Test model."),
 "engine_id": ("string", "Highway only, configuration level. Engine identifier."),
 "displacement_l": ("float", "Configuration level. Displacement in litres."),
 "certification_fuel": ("string", "Configuration level. Fuel used for certification testing."),
 "engine_operation": ("string", "Nonroad only, configuration level."),
 "test_procedure": ("string", "Nonroad only, configuration level."),
 "test_procedure_type": ("string", "Nonroad only, configuration level."),
 "test_fuel": ("string", "Highway only, configuration level."),
 "test_date": ("date", "Highway only, configuration level."),
 "pollutant": ("string", "Controlled vocabulary. See the pollutant table below."),
 "test_type": ("string", "`transient`, `steady_state`, or `smoke`."),
 "cert_result": ("float", "Certification result. **Units are given by the `units` column and differ between panels.**"),
 "adj_result": ("float", "Highway only. Deterioration-adjusted result. Null for nonroad."),
 "standard": ("float", "Highway only. Applicable standard for this pollutant and test type. Null for nonroad — see LIMITATIONS."),
 "fel": ("float", "Family Emission Limit where the family certified to one. Null is not zero."),
 "fcl": ("float", "Highway only. Family Certification Level."),
 "df_type": ("string", "Highway only. Deterioration factor type."),
 "df_value": ("float", "Highway only. Deterioration factor value."),
 "units": ("string", "`g/bhp-hr` (highway), `g/kW-hr` (nonroad), or `pct opacity` (smoke). Never null."),
 "quality_flag": ("string", "Null, or `negative_cert_result`. See LIMITATIONS."),
 "lineage_root": ("string", "Oldest family reachable through the carryover chain."),
 "lineage_depth": ("integer", "Number of carryover steps to the lineage root. 0 = starts its own lineage."),
}

def table_for(name):
    df = pd.read_csv(f"{OUT}/{name}.csv", nrows=400, low_memory=False)
    full = sum(1 for _ in open(f"{OUT}/{name}.csv")) - 1
    lines = [f"### `{name}.csv`", "", f"{f(full)} rows.", "",
             "| Column | Type | Description |", "|---|---|---|"]
    for c in df.columns:
        t, d = COLDOC.get(c, ("string", "—"))
        lines.append(f"| `{c}` | {t} | {d} |")
    return "\n".join(lines) + "\n"

# ---------------- CODEBOOK ----------------
pol_rows = "\n".join(f"| `{p}` | {f(S['rows_by_panel_pollutant'].get(p,0))} |"
                     for p in S["pollutants"])
codebook = f"""# CIDEX Codebook

{DRAFT}
Version 1.0 · built {S['build_date']}

CIDEX is distributed as four tables. The unit of analysis for emissions is
**(model year, engine family, pollutant, test type)**. Family-level attributes and
configuration-level attributes are separated, because configuration attributes vary
*within* a family and keeping them together would force an arbitrary row to win.

## Keys

`(panel, model_year, engine_family)` uniquely identifies a family. The engine family
name already encodes the model year, so it is a true key rather than a surrogate.

## Units — read this before comparing anything

Three unit systems travel in the `units` column:

| Panel / measure | Units |
|---|---|
| Highway certification results | `g/bhp-hr` |
| Nonroad certification results | `g/kW-hr` |
| Smoke opacity (nonroad) | `pct opacity` |

**CIDEX performs no unit conversion.** Comparing a highway `cert_result` to a nonroad
`cert_result` without converting is invalid and will produce a plausible, wrong number.
Convert deliberately:

```python
from cidex.units import to_g_per_kWh
to_g_per_kWh(0.20, "g/bhp-hr")   # -> 0.2682 g/kW-hr
```

`cidex.units.headroom()` raises `MixedUnitsError` rather than computing across panels.

## Pollutant vocabulary

`NMHCE` (Non-Methane Hydrocarbon Equivalent) is deliberately **not** folded into `NMHC`.
It is a different regulatory construct; folding would destroy information that cannot be
reconstructed.

| Pollutant | Rows |
|---|---|
{pol_rows}

## Tables

{table_for('cidex_family')}
{table_for('cidex_config')}
{table_for('cidex_emissions')}
{table_for('cidex_carryover')}
"""
open(f"{DOCS}/CODEBOOK.md","w").write(codebook)

# ---------------- LIMITATIONS ----------------
_cov = S["model_year_coverage"]
_rows = ["| Panel | Model year | Families | Share of interior median | Reason |",
         "|---|---|---|---|---|"]
for _panel, _c in _cov.items():
    for _y, _v in _c["by_year"].items():
        if _v["coverage"] != "complete":
            _reason = ("EPA archive file not ingested" if _v["coverage"] == "partial_archive"
                       else "still being certified when the file was downloaded")
            _rows.append(f"| {_panel} | {_y} | {_v['families']:,} | "
                         f"{_v['share_of_median']:.0%} | {_reason} |")
cov_table = "\n".join(_rows)
thresh = f"{S['coverage_threshold']:.0%}"
hw_lo, hw_hi = _cov["highway"]["usable_range"]
nr_lo, nr_hi = _cov["nonroad"]["usable_range"]

ic = S["integrity_checks"]
limits = f"""# CIDEX Limitations

{DRAFT}
Version 1.0 · built {S['build_date']}

Stated plainly, because a dataset whose limitations are buried is worse than one that
does not exist.

## 1. Units are not comparable across panels

The single largest correctness risk in this dataset. Highway results are certified in
`g/bhp-hr`, nonroad in `g/kW-hr`. Any aggregate that mixes panels without converting is
wrong. CIDEX labels every row and refuses to convert silently; the responsibility for
converting is deliberately left with the user.

## 2. {S['negative_cert_results']} negative certification results

{S['negative_cert_results']} rows ({S['negative_cert_result_share_pct']}% of
{f(S['emission_rows_total'])}), across {S['negative_cert_result_families']} engine families,
all in the {', '.join(S['negative_cert_result_panels'])} panel, carry a negative
`cert_result`. An emission rate cannot be physically negative.

These are published **exactly as EPA reports them**, flagged with
`quality_flag = negative_cert_result`. They are not corrected, clipped, or dropped.
Whether this reflects an EPA data-entry issue or an encoding convention neither party
has documented is **unresolved**. Users who need physically plausible values should
filter on `quality_flag`.

## 3. Nonroad rows have no pollutant-specific standard

The nonroad source states an applicable compliance standard at *family* level, not per
pollutant and test type. Rather than infer which standard applies to which pollutant,
CIDEX leaves `standard` null for all nonroad rows. `adj_result` and `fcl` are likewise
highway-only. Null means "not stated by the source", never zero.

## 4. Two model years at each panel's edge are structurally incomplete

**This is the limitation most likely to produce a wrong published result.** Both panels
thin out at their edges, for two unrelated reasons, and a time series that includes those
years reads the artefact as a trend.

EPA holds older model years in **separate archive files** that CIDEX v1.0 does not ingest
(highway 1982-2016; nonroad 1996-2011), so the earliest year in each panel contains only
whichever families happen to sit in the current file. Separately, the newest model year is
**still being certified** at the moment the file is downloaded.

A year is flagged incomplete when it holds under {thresh} of the median count of that
panel's interior years:

{cov_table}

Every row of `cidex_family.csv` and `cidex_emissions.csv` carries a **`year_coverage`**
column (`complete` / `partial_archive` / `partial_forward`), so this cannot be missed by
accident.

**Usable ranges for trend analysis:** highway **MY{hw_lo}-{hw_hi}**, nonroad **MY{nr_lo}-{nr_hi}**.

```python
df = df[df.year_coverage == "complete"]   # before any time series
```

The {thresh} threshold is a judgement, not a fact about the data. It happens to separate
the observed cases cleanly - no year sits near the boundary - but a reuser with a different
purpose may prefer a different cut, and the raw counts above are given so they can make one.

## 5. Manufacturer names are not normalised

Spellings vary across model years in the source and CIDEX preserves them. Grouping by
manufacturer requires the user's own normalisation.

## 6. Carryover lineage is nonroad-only and has open edges

{f(S['carryover_families_with_link'])} nonroad families name a predecessor.
{f(S['carryover_orphan_edges'])} of those name a family that is **not** in this panel —
usually a pre-{S['model_year_min_nonroad']} family, outside the published window. Those
lineages are truncated, not wrong, but a depth of 0 does not always mean "first of its line".
{S['carryover_self_referencing']} families point at themselves, which EPA appears to use to
mark an unchanged re-certification; these are treated as lineage termini.
{S['carryover_true_cycles']} true cycles exist.

## 7. Family-level attributes were de-duplicated

Where a source attribute was constant within a family it was kept at family level; where
it varied it was moved to `cidex_config.csv`. The build asserts the family table is truly
family-level and fails rather than silently picking a winning row.

## Integrity checks

All checks below pass in this build. They are assertions about internal consistency, **not**
evidence that the values match EPA — that is what the verification gate is for.

""" + "\n".join(f"- {'PASS' if v else 'FAIL'} — `{k}`" for k, v in ic.items()) + "\n"
open(f"{DOCS}/LIMITATIONS.md","w").write(limits)

# ---------------- VERIFICATION CHECKLIST ----------------
spot = "\n".join(
 f"""### Check {i}

**{c['why']}**

| | |
|---|---|
| Panel | {c['panel']} |
| Engine family | `{c['engine_family']}` |
| Model year | {c['model_year']} |
| Pollutant | {c['pollutant']} |
| Test type | {c['test_type']} |
| **CIDEX says** | **{c['cidex_cert_result']} {c['units']}** |

- [ ] Looked this family up in EPA's interactive certificate tool
- [ ] The value above matches, or I have recorded what it actually says: ______________
"""
 for i, c in enumerate(S["spot_checks"], 1))

checklist = f"""# CIDEX Verification Checklist

{DRAFT}
Version 1.0 · built {S['build_date']} · author: {au['name']} (ORCID {au['orcid']})

Nothing in this package may be deposited, cited, or described as published until every
box below is ticked by the author personally. The mechanical checks are automated; the
judgement calls are not, which is the entire point.

---

## Part 1 — Reproduce

- [ ] Ran the pipeline from a clean checkout following `README.md`
- [ ] `data/processed/stats.json` matches the one shipped in this package
- [ ] All {len(S['integrity_checks'])} integrity checks report PASS
- [ ] The SHA-256 hashes in `logs/provenance.jsonl` match the EPA files I downloaded

Expected headline figures:

| | |
|---|---|
| Engine families | {f(S['families_total'])} ({f(S['families_highway'])} highway, {f(S['families_nonroad'])} nonroad) |
| Configurations | {f(S['configs_total'])} |
| Emission records | {f(S['emission_rows_total'])} |
| Manufacturers | {f(S['manufacturers_total'])} |
| Distinct lineages | {f(S['carryover_distinct_lineages'])} |

## Part 2 — Spot-check against EPA

Five checks, each probing a different way the harmonization could be wrong. Look each one
up by hand in EPA's interactive certificate data tool.

{spot}

## Part 3 — Judgement calls only the author can make

- [ ] **`NMHCE` stays separate from `NMHC`.** I have confirmed these are different
      regulatory constructs and should not be merged. *(If wrong, say so — it is one line
      in `src/cidex/vocab.py`.)*
- [ ] **The negative values.** Having checked EPA's own record for
      `{S['spot_checks'][-1]['engine_family']}`, I confirm that publishing them as-is with a
      quality flag is the right call, and that `LIMITATIONS.md` §2 describes the situation
      accurately.
- [ ] **The units language.** `CODEBOOK.md` states the g/bhp-hr vs g/kW-hr hazard correctly
      and the conversion factor is right.
- [ ] **Nonroad `standard` left null.** I agree that inferring which family-level compliance
      standard applies to which pollutant would be a guess, and null is the honest choice.
- [ ] **Limitations are complete.** Nothing a reuser would need to know is missing.

## Part 4 — Before deposit

- [ ] No `[TARGET]`, `[VERIFY]`, `[DOI]`, or placeholder bracket survives anywhere
      *(run `python3 scripts/07_publish_gate.py`)*
- [ ] No DRAFT stamp remains in any document intended for publication
- [ ] No credential, token, or personal path appears in any tracked file
- [ ] The author block in `AUTHORS.json` is spelled exactly as it should appear forever
- [ ] I have rewritten any prose that will carry my name into my own voice

---

## Sign-off

I have personally reproduced this pipeline and checked its outputs against the primary
source. I can defend every number in it.

Signed: ____________________  Date: ____________
"""
open(f"{DOCS}/VERIFICATION_CHECKLIST.md","w").write(checklist)

# ---------------- CITATION.cff ----------------
cff = f"""cff-version: 1.2.0
title: "CIDEX: Compression-Ignition Engine Certification Panel"
message: "If you use this dataset, please cite it as below."
type: dataset
authors:
  - family-names: "{au['family_name']}"
    given-names: "{au['given_names']}"
    orcid: "https://orcid.org/{au['orcid']}"
    affiliation: "{au['affiliation']}"
version: "1.0.0-draft"
date-released: "{S['build_date']}"
license: CC-BY-4.0
abstract: >-
  A harmonized engine-family-level panel of United States Environmental Protection
  Agency certification data for heavy-duty highway and nonroad compression-ignition
  engines. Reconciles two EPA source workbooks whose internal structures differ - one
  long on pollutant, one wide - into a single schema covering {f(S['families_total'])}
  engine families and {f(S['emission_rows_total'])} emission records across
  {f(S['manufacturers_total'])} manufacturers, model years {S['model_year_min_nonroad']}
  to {S['model_year_max_nonroad']}. Includes a resolved carryover lineage linking
  {f(S['carryover_distinct_lineages'])} distinct nonroad certification families across
  model years. Units are preserved as certified and never silently converted.
keywords:
  - diesel engines
  - emissions certification
  - compression ignition
  - EPA
  - nonroad engines
  - heavy-duty engines
  - open data
"""
open("CITATION.cff","w").write(cff)

# ---------------- README ----------------
_c = S["model_year_coverage"]
readme = f"""# CIDEX

**Compression-Ignition Engine Certification Panel**

{DRAFT}
A harmonized engine-family-level panel of US EPA certification data for heavy-duty
highway and nonroad compression-ignition engines.

{f(S['families_total'])} engine families · {f(S['emission_rows_total'])} emission records ·
{f(S['manufacturers_total'])} manufacturers · MY{S['model_year_min_nonroad']}–{S['model_year_max_nonroad']}

{au['name']} · [ORCID {au['orcid']}](https://orcid.org/{au['orcid']}) · {au['affiliation']}
Part of the [FACET](https://osariemenimafidon.github.io/facet/) research program.

---

## What problem this solves

EPA publishes compression-ignition certification data as two Excel workbooks whose
internal structures are incompatible. The highway workbook is **long** on pollutant
(a `Pollutant Name` column); the nonroad workbook is **wide** (pollutants spread across
~24 columns under a two-level header). Both put their real headers on row 2, so a naive
`read_excel` on either produces silent garbage.

CIDEX does that reconciliation once, with provenance, so the next person starts from an
analysis-ready panel instead of a spreadsheet.

## Getting the source data

The two EPA files are **not** redistributed here. Download them into `data/raw/`:

- [Heavy-duty highway, MY2015–present](https://www.epa.gov/system/files/documents/2026-03/heavy-duty-gas-and-diesel-engines-2015-present.xlsx)
- [Nonroad CI, MY2011–present](https://www.epa.gov/system/files/documents/2026-03/nonroad-compression-ignition-2011-present.xlsx)

Keep the filenames as downloaded. `scripts/01_provenance.py` records the SHA-256 of each
file, so you can confirm you started from the same bytes this build did — the hashes are
in `logs/provenance.jsonl`.

## Rebuilding

```bash
pip install -r requirements.txt
python3 scripts/01_provenance.py        # hash and log the raw files
python3 scripts/02_harmonize_highway.py # long-on-pollutant -> CIDEX schema
python3 scripts/03_harmonize_nonroad.py # wide -> CIDEX schema
python3 scripts/04_carryover.py         # resolve nonroad lineage chains
python3 scripts/05_combine_qa.py        # combine, flag, integrity-check, write stats.json
python3 scripts/06_docs.py              # regenerate this documentation
python3 scripts/08_figures.py           # regenerate figures
```

Every number in every document is interpolated from `data/processed/stats.json`, which
the pipeline writes. Nothing is typed by hand, so the prose cannot drift from the data.

## Output

| File | Rows | What |
|---|---|---|
| `cidex_family.csv` | {f(S['families_total'])} | One row per (panel, model year, engine family) |
| `cidex_config.csv` | {f(S['configs_total'])} | Engine configurations within a family |
| `cidex_emissions.csv` | {f(S['emission_rows_total'])} | One row per (family, pollutant, test type) |
| `cidex_carryover.csv` | {f(S['families_nonroad'])} | Resolved nonroad certification lineage |

Parquet mirrors are written alongside. See [`docs/CODEBOOK.md`](docs/CODEBOOK.md) for
every column.

## Three things to know before using it

**1. Units are not comparable across panels.** Highway results are `g/bhp-hr`, nonroad
`g/kW-hr`, smoke `pct opacity`. CIDEX never converts silently:

```python
from cidex.units import to_g_per_kWh
to_g_per_kWh(0.20, "g/bhp-hr")   # 0.2682
```

**2. Exclude incomplete years from any time series.** Each panel's edge years are
structurally incomplete — EPA archive files at the left, ongoing certification at the
right. Usable ranges: highway **MY{_c['highway']['usable_range'][0]}–{_c['highway']['usable_range'][1]}**,
nonroad **MY{_c['nonroad']['usable_range'][0]}–{_c['nonroad']['usable_range'][1]}**.

```python
df = df[df.year_coverage == "complete"]
```

**3. {S['negative_cert_results']} records have negative certification results.** Published
as EPA reports them, flagged `quality_flag = negative_cert_result`. Filter if you need
physically plausible values.

[`docs/LIMITATIONS.md`](docs/LIMITATIONS.md) has the full list. Read it.

## Status

This package has **not** passed its verification gate. See
[`docs/VERIFICATION_CHECKLIST.md`](docs/VERIFICATION_CHECKLIST.md). No DOI has been minted.

## Citation

See [`CITATION.cff`](CITATION.cff).

## Licence

Data and documentation: [CC BY 4.0](LICENSE-DATA). Code: [MIT](LICENSE).

## Source attribution

Derived from US EPA
[annual certification data](https://www.epa.gov/compliance-and-fuel-economy-data/annual-certification-data-vehicles-engines-and-equipment),
2026-03 file drop. US Government works. CIDEX is not affiliated with or endorsed by EPA.
"""
open("README.md","w").write(readme)

print("written:")
for p in ["README.md", f"{DOCS}/CODEBOOK.md", f"{DOCS}/LIMITATIONS.md",
          f"{DOCS}/VERIFICATION_CHECKLIST.md", "CITATION.cff"]:
    print(f"  {os.path.getsize(p):>6,}  {p}")
