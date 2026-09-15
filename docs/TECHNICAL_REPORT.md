% CIDEX: The Compression-Ignition Engine Certification Panel — Harmonization Pipeline
% Imafidon, Osariemen · ORCID 0009-0006-3069-4674 · Independent Researcher
% Version 1.0.0 · 2026-09-15

## Abstract

The United States Environmental Protection Agency publishes emission certification
records for compression-ignition engines as two Microsoft Excel workbooks whose internal
structures are mutually incompatible. One is organised long on pollutant and wide on test
type; the other is wide on pollutant beneath a two-level header, with family attributes
distributed on both sides of the measurement block. Both place their true column headers
on the second row, so the naive read of either file produces plausible but incorrect data
without raising an error.

This report documents CIDEX, a pipeline that reconciles both sources into a single
analysis-ready panel of **8,627 engine families**,
**9,794 engine configurations** and
**94,869 emission records** across
**108 manufacturers** and model years
2011–2027. It also documents a resolved
carryover lineage linking **2,541 distinct certification
families** across model years, a structure present in the nonroad source but not, as far
as the author is aware, previously published in resolved form.

The report states the method in enough detail to be re-implemented independently, records
every design decision with its justification, and — in Section 6 — documents the defects
found in the pipeline during development and how each was detected. That section is
included because a validation record that reports no defects is not evidence of a correct
pipeline; it is evidence of an incurious one.

**Document.** Technical report, part of the
[FACET](https://osariemenimafidon.github.io/facet/) research program.
Repository <https://github.com/osariemenimafidon/cidex>.
Licence: data and documentation CC BY 4.0; code MIT.
Every figure in this report is interpolated from the pipeline's own `stats.json`.

---

## 1. Introduction

### 1.1 Motivation

Certification data is the only comprehensive public record of what engines were approved
to emit, by whom, and under which standard. It underpins questions about fleet
composition, technology adoption, regulatory stringency over time, and the relationship
between certified and in-service behaviour.

In practice the data is difficult to use. The obstacle is not access — EPA publishes the
files openly and without authentication — but structure. Every researcher who wants to ask
a cross-cutting question must independently reverse-engineer two different layouts,
reconcile two pollutant encodings, and work out that the file's headers are not where a
spreadsheet reader will look for them. That work is duplicated, undocumented, and
performed under no obligation to get it right.

CIDEX performs that reconciliation once, publicly, with provenance.

### 1.2 Scope

CIDEX v1.0.0 covers the two current EPA certification files: heavy-duty highway
gasoline and diesel engines (model years 2015 onward) and nonroad
compression-ignition engines (model years 2011 onward). EPA's
archive files — highway 1982–2016 and nonroad 1996–2011 — are **not** ingested in this
version; their omission has a measurable effect on coverage which is quantified in
Section 7.3 and carried as a flag in the data.

### 1.3 What this report is for

It should be possible to re-implement CIDEX from this report alone and obtain the same
numbers. Where a choice was made that a competent person could reasonably have made
differently, the choice is stated as a choice rather than presented as the only option.

---

## 2. Sources

### 2.1 The two workbooks

| | Highway | Nonroad |
|---|---|---|
| Coverage | Heavy-duty highway gasoline and diesel | Nonroad compression-ignition |
| Model years | 2015–2026 | 2011–2027 |
| Source rows (Family Info) | 7,804 | 10,214 |
| Unique families | 702 | 7,925 |
| Manufacturers | 27 | 86 |
| Orientation | Long on pollutant, wide on test type | Wide on pollutant, two-level header |

Both are US Government works and carry no copyright restriction on reuse.

### 2.2 Access constraint and the provenance record

The build environment used for this work cannot reach `epa.gov`: outbound requests are
refused by an organisational egress policy. The source files were therefore downloaded
manually and placed in `data/raw/`.

This is a weakness — an automated fetch is verifiable in a way a manual one is not — and
it is mitigated rather than hidden. `scripts/01_provenance.py` records, for every raw
file, its name, byte count, SHA-256 digest, modification time, and the canonical URL it is
asserted to have come from. A rebuilder does not have to accept the assertion: they
download the file themselves and compare digests. The full record is Appendix A.

---

## 3. The harmonization problem

### 3.1 Headers are on the second row

Both workbooks reserve row 1 for a merged group header and place actual column names on
row 2. `pandas.read_excel` defaults to `header=0`. Applied to either file it returns a
frame whose column names are `Unnamed: 0 … Unnamed: 44` and whose first data row contains
the real headers. Nothing raises. Any subsequent selection by column name fails or, worse,
succeeds against the wrong column.

### 3.2 The two files are organised in opposite directions

The **highway** file is long on pollutant: one row per family, engine configuration and
pollutant, with a `Pollutant Name` column taking 10 distinct values. It
is simultaneously *wide* on test type — transient and steady-state results occupy separate
column blocks on the same row.

The **nonroad** file is the reverse. One row carries all pollutants as columns, arranged
in four groups beneath a two-level header: steady_state, transient, fel, smoke. Family
attributes appear both *before* and *after* the measurement block, which defeats any
approach based on column position alone.

Reconciling these into one schema is the substance of the pipeline.

### 3.3 The engine family name is a true key

In both panels the count of distinct engine family names equals exactly the count of
distinct (model year, family) pairs — 702 and
7,925 respectively. The model year is encoded in the family name's
first character, so the name alone identifies the family-year. No surrogate key is
required, and a name collision across years is impossible by construction.

### 3.4 Family attributes and configuration attributes are different things

A single engine family may be certified across several engine configurations. In the
nonroad source, 1,487 of 7,925
families occupy more than one row — up to 34 for a single family —
differing by engine code, model, displacement or test procedure.

Placing those attributes in a family-level table would force an arbitrary row to win and
silently discard the rest. CIDEX separates them: attributes constant within a family go to
the family table; attributes that vary go to a configuration table. The split is not
asserted — the build **tests** it and aborts if any attribute in the family table varies
within a family. Before the split, 7 nonroad
attributes varied; after it, 0 do.

---


## 4. Method

### 4.1 Pipeline overview

| Script | Function |
|---|---|
| `01_provenance.py` | Hash and log every raw file before use |
| `02_harmonize_highway.py` | Highway source → CIDEX schema |
| `03_harmonize_nonroad.py` | Nonroad source → CIDEX schema |
| `04_carryover.py` | Resolve nonroad certification lineage |
| `05_combine_qa.py` | Combine, flag, check, write `stats.json` |
| `06_docs.py` | Regenerate the documentation set |
| `07_publish_gate.py` | Pre-publication scan |
| `08_figures.py` | Figures |
| `09_release.py` | Build the deposit archive |
| `11_report.py` | Generate this report |

Scripts are numbered in run order and each is independently re-runnable.

### 4.2 Highway harmonization

The highway source is read with `header=1` — the second row. Family-level attributes are
projected into a family table; configuration attributes (engine code, test model, engine
identifier, test fuel, test date) into a configuration table.

The pollutant name is mapped through a controlled vocabulary. If any source value fails to
map, the script **raises** rather than dropping the row: a silently discarded pollutant is
exactly the failure mode this pipeline exists to prevent. In this build,
0 values failed to map.

The test-type block is then unpivoted. Each source row yields one record per test type, and
records with no value in any measurement column are removed as unpivot artefacts rather
than facts: 15,608 rows before,
2,184 dropped, 13,424 retained.

Family-attribute constancy is tested, not assumed. In this build
0 highway family attributes varied within a family.

### 4.3 Nonroad harmonization

The nonroad two-level header is resolved without hard-coding column positions. The group
row is forward-filled, then a column is treated as a measurement **only if** its row-2
sub-name is one the group actually contains. This is what keeps `Engine Model` — which
sits immediately after the FEL block and inherits its forward-filled group label —
classified as an attribute rather than as a pollutant. The classifier found
22 measurement columns and 24 attribute
columns, with 0 attributes unmapped.

Wide-to-long expansion produces 224,708 candidate records, of which
141,657 are empty cells in a sparse layout and are dropped, leaving
81,445.

Family Emission Limits are a limit, not a measured result, and are moved to their own
column. **The merge is keyed on source-row identity, not on the family key** — see §6.1.

### 4.4 Carryover lineage

5,982 nonroad families name a predecessor family. These
references chain, so a family's certification history can be traced across model years.

Three cases are handled explicitly rather than by exception:

- **Self-reference.** 30 families name *themselves* as their
  own carryover. EPA appears to use this to mark an unchanged re-certification. A naive
  traversal reads it as a cycle; CIDEX treats it as a lineage terminus.
- **Orphans.** 568 families name a predecessor absent from this panel,
  usually pre-2011 and outside the published window. The lineage is
  truncated, not wrong — so a depth of 0 does not always mean "first of its line".
- **True cycles.** 0 detected. The graph is a forest.

Result: 2,541 distinct lineages, mean depth
1.382, maximum 14 model years. The deepest runs
`CCPXL18.1NYS` →
`TCPXL18.1NYS`
(MY2026).

### 4.5 Units: no silent conversion

The two panels certify in different units. Highway results are in **g/bhp-hr**, nonroad in
**g/kW-hr**, and nonroad smoke opacity in **percent**. Every record carries its units in a
column; **no conversion is performed**.

This is deliberate. A dataset that silently normalised units would let a user aggregate
across panels and obtain a plausible, wrong number with no indication anything was amiss.
Conversion is available but must be invoked:

```python
from cidex.units import to_g_per_kWh
to_g_per_kWh(0.20, "g/bhp-hr")   # 0.2682
```

`cidex.units.headroom()` raises `MixedUnitsError` rather than computing across unit
systems. The constant used is 1 hp = 0.7456998716 kW.

### 4.6 Quality flags and coverage flags

Two flags are carried on the data rather than left to documentation:

`quality_flag` marks the 50 records
(0.0527% of the panel, across
18 families, all
nonroad) whose certification result is **negative**.
An emission rate cannot be physically negative. CIDEX does not correct, clip or drop them
— the published value stands as EPA reports it and carries a flag. Whether this reflects a
data-entry issue or an undocumented encoding is unresolved.

`year_coverage` marks model years that are structurally incomplete (§7.3).

---

## 5. Validation

### 5.1 Integrity checks

10 checks run on every build. All currently pass.

| Check | Result | What it tests |
|---|---|---|
| `family_key_unique` | PASS | No (panel, model year, engine family) triple appears twice in the family table. |
| `no_emission_row_without_family` | PASS | Every emission record joins a family row; no orphan measurements. |
| `units_never_null` | PASS | The units column is populated on every emission record. |
| `no_mixed_units_within_panel` | PASS | No panel carries more than its expected unit systems. |
| `highway_units_evidenced_by_standards` | PASS | The modal certification standard per pollutant in the highway panel matches the known US heavy-duty standards expressed in g/bhp-hr. See §5.2. |
| `highway_units_labelled` | PASS | Every highway record is labelled g/bhp-hr. |
| `nonroad_units_correct` | PASS | Nonroad records carry only g/kW-hr or pct opacity. |
| `carryover_no_true_cycles` | PASS | The carryover lineage graph contains no cycle. |
| `every_negative_value_is_flagged` | PASS | Every negative certification result carries a quality flag. |
| `flagged_share_below_0pt1pct` | PASS | Flagged records remain under 0.1% of the panel; a sharp rise would indicate a parsing regression. |

These test **internal consistency**. They cannot establish that a value matches EPA's
record; that is what §5.3 is for.

### 5.2 The units evidence test

The highway source file states its units **nowhere**. Its headers are bare —
`TR Cert Result`, `Transient Standard`. The claim that highway results are in g/bhp-hr was
originally an assertion in the documentation.

It is now a test. US heavy-duty highway standards have known values in g/bhp-hr, and the
modal certification standard per pollutant in the panel is compared against them:

| Pollutant | Known standard (g/bhp-hr) | Modal value in CIDEX |
|---|---|---|
| NOx | 0.2 | 0.2 |
| PM | 0.01 | 0.01 |
| NMHC | 0.14 | 0.14 |
| CO | 15.5 | 15.5 |

Expressed in g/kW-hr the same standards would be 0.268, 0.013, 0.188, 20.786 — an order of
magnitude away in every case, so the test cannot pass by coincidence. It runs on every
build.

### 5.3 The author verification gate

Mechanical checks cannot establish correspondence with the source. That requires a person
to look up specific records in EPA's own certificate tool and compare. The pipeline
therefore ships five named spot-checks, each probing a different failure mode:

| # | Panel | Family | MY | Pollutant | CIDEX value | What it probes |
|---|---|---|---|---|---|---|
| 1 | highway | `MSZXH05.23FD` | 2021 | NOx | 0.17 g/bhp-hr | highway, transient NOx — the standard case |
| 2 | highway | `FNGCH0466AEA` | 2015 | PM | 0.01 g/bhp-hr | highway, earliest model year present — tests the MY2015-16 archive boundary |
| 3 | nonroad | `LCEXL60.0AAB` | 2020 | NOx | 0.48 g/kW-hr | nonroad, steady-state NOx — tests the wide-to-long unpivot |
| 4 | nonroad | `TCPXL32.1NZS` | 2026 | NMHC | 0.08 g/kW-hr | deepest carryover lineage (depth 14, root CCPXL32.0NZS) — tests lineage resolution |
| 5 | nonroad | `CDICL05.8HTA` | 2012 | NOx | -1.0 g/kW-hr | a flagged negative value — is this real in EPA's own record? |

Publication is blocked until the author signs `docs/VERIFICATION_CHECKLIST.md`.
`scripts/09_release.py` refuses to build a deposit archive while the attestation file is
absent, and every document and figure regenerates stamped DRAFT without it.

Status: Signed by Imafidon, Osariemen (ORCID 0009-0006-3069-4674) on 2026-09-15, recorded by the presence of `.gate-signed` in the repository root.

---

## 6. Defects found and corrected

Three defects were found during development. They are recorded because a validation
section reporting none would say more about the thoroughness of the review than about the
correctness of the pipeline.

### 6.1 The FEL merge multiplied rows

**Severity: data corruption. Detected: adversarial review before publication.**

Family Emission Limits were merged onto the emission records using
`(model_year, engine_family, pollutant)`. Because 1,487 families occupy
more than one source row, that key matched several FEL entries per family and the merge
fanned every measurement row out to match.

The result was **2,139 phantom rows** — genuine values, duplicated. This is worse than
missing data: no nulls appeared, no outliers, nothing downstream looked wrong. It inflated
every count by roughly 2.6%.

**Corrected** by carrying source-row identity through the wide-to-long expansion and
merging on it. The script now aborts if the row count changes across the merge. Nonroad
emission records fell from 83,584 to 81,445.

### 6.2 The units claim was asserted, not evidenced

**Severity: unverified claim in published documentation. Detected: same review.**

g/bhp-hr appeared in the codebook as fact, having been inferred rather than read. The
inference was correct, but the reasoning was not sound — the same reasoning, applied to a
sibling project, substituted a European fuel standard for a US regulatory one and produced
a wrong result. Corrected as described in §5.2.

### 6.3 Carryover self-references counted as cycles

**Severity: incorrect summary statistic. Detected: inspecting the output.**

The first lineage traversal reported 109 cycles. Every one was a family naming itself —
a terminus, not a loop. Corrected by treating self-reference as a stopping condition and
detecting true cycles with a visited set. True cycles: 0.

---

## 7. Results

### 7.1 Panel contents

| | Rows |
|---|---|
| `cidex_family.csv` | 8,627 |
| `cidex_config.csv` | 9,794 |
| `cidex_emissions.csv` | 94,869 |
| `cidex_carryover.csv` | 7,925 |

108 manufacturers · 14 pollutants ·
3 test types · units present: `g/bhp-hr`, `g/kW-hr`, `pct opacity`

### 7.2 Pollutant coverage

| Pollutant | Records |
|---|---|
| `CH4` | 7,456 |
| `CO` | 14,238 |
| `CO2` | 13,196 |
| `HCHO` | 503 |
| `N2O` | 4,700 |
| `NH3` | 3 |
| `NMHC` | 14,219 |
| `NMHCE` | 13 |
| `NMHC_NOx` | 6,712 |
| `NOx` | 14,238 |
| `PM` | 14,190 |
| `smoke_accel` | 1,853 |
| `smoke_lug` | 1,763 |
| `smoke_peak` | 1,785 |

`NMHCE` (Non-Methane Hydrocarbon Equivalent) is kept distinct from `NMHC`. It is a
different regulatory construct, and folding it in would destroy information that cannot be
reconstructed downstream, where keeping it separate costs a user one filter.

### 7.3 Model-year coverage

Both panels are structurally incomplete at their edges, for two unrelated reasons. A year
is flagged when it holds under 50% of the median count of that
panel's interior years.

| Panel | Model year | Families | Share of median | Reason |
|---|---|---|---|---|
| highway | 2015 | 3 | 5% | EPA archive not ingested |
| highway | 2016 | 29 | 45% | EPA archive not ingested |
| nonroad | 2011 | 66 | 12% | EPA archive not ingested |
| nonroad | 2027 | 8 | 2% | still being certified |

Usable ranges for trend analysis: highway **MY2017–2026**,
nonroad **MY2012–2026**.

The threshold is a judgement. It separates the observed cases cleanly — no year sits near
the boundary — but the raw counts are published so a reuser can choose differently.

---

## 8. Limitations

Stated in full in `docs/LIMITATIONS.md`. In summary: units are not comparable across
panels without conversion; 50 records carry physically impossible
negative values, published as EPA reports them; nonroad records have no pollutant-specific
standard because the source states it only at family level; edge model years are
incomplete; manufacturer names are not normalised; and carryover lineage is nonroad-only
with 568 open edges.

## 9. Reproducibility

```bash
pip install -r requirements.txt
./verify.sh
```

`verify.sh` rebuilds from `data/raw/` and diffs every value against the shipped
`docs/stats_reference.json`, excluding only the build date. A mismatch is a finding.

Every number in every CIDEX document — including this report — is interpolated from
`data/processed/stats.json`, which the pipeline writes. The column mappings in Appendix B
are imported from the pipeline modules at generation time, so they cannot drift from the
code they document.

---

## Appendix A — Provenance record

| File | Bytes | SHA-256 | Recorded |
|---|---|---|---|
| `heavy-duty-gas-and-diesel-engines-2015-present.xlsx` | 22,908,765 | `3edfe15deef231828e26173f2a4dfe68ade0e96eb8dfe044b32cc4e63db640cf` | 2026-09-15 |
| `nonroad-compression-ignition-2011-present.xlsx` | 13,994,645 | `9e78cf00ca4f930899fed3d66101145f32dade525e8e68d5394b3df56cf5593c` | 2026-09-15 |

Canonical sources:

- `heavy-duty-gas-and-diesel-engines-2015-present.xlsx` — <https://www.epa.gov/system/files/documents/2026-03/heavy-duty-gas-and-diesel-engines-2015-present.xlsx>
- `nonroad-compression-ignition-2011-present.xlsx` — <https://www.epa.gov/system/files/documents/2026-03/nonroad-compression-ignition-2011-present.xlsx>

## Appendix B — Source-to-output column mapping

### B.1 Highway family attributes

| Source column | CIDEX column | Table |
|---|---|---|
| `Manufacturer` | `manufacturer` | family |
| `Model Year` | `model_year` | family |
| `Engine Family` | `engine_family` | family |
| `Certificate No.` | `certificate_no` | family |
| `Date Issued` | `date_issued` | family |
| `Engine Cycle` | `engine_cycle` | family |
| `Fuel Type` | `fuel_type` | family |
| `Fuel Metering System` | `fuel_metering_system` | family |
| `Introduction Date` | `introduction_date` | family |
| `Useful Life` | `useful_life` | family |
| `Intended Service Class` | `intended_service_class` | family |

### B.2 Highway measurement blocks

| Source column | CIDEX column | Destination |
|---|---|---|
| `TR Cert Result` | `cert_result` | emissions, `test_type = transient` |
| `Transient (TR) Comb Adj Result` | `adj_result` | emissions, `test_type = transient` |
| `Transient Standard` | `standard` | emissions, `test_type = transient` |
| `Transient FEL` | `fel` | emissions, `test_type = transient` |
| `Transient FCL` | `fcl` | emissions, `test_type = transient` |
| `SS Cert Result` | `cert_result` | emissions, `test_type = steady_state` |
| `Steady State (SS) Adj Result` | `adj_result` | emissions, `test_type = steady_state` |
| `SS Standard` | `standard` | emissions, `test_type = steady_state` |
| `SS FEL` | `fel` | emissions, `test_type = steady_state` |
| `SS FCL` | `fcl` | emissions, `test_type = steady_state` |

### B.3 Nonroad attributes

| Source column | CIDEX column | Table |
|---|---|---|
| `Model Year` | `model_year` | family or configuration |
| `Engine Family` | `engine_family` | family or configuration |
| `Manufacturer` | `manufacturer` | family or configuration |
| `Certificate #` | `certificate_no` | family or configuration |
| `Issue Date` | `date_issued` | family or configuration |
| `Commerce Introduction Date` | `introduction_date` | family or configuration |
| `Carryover Engine Family Name` | `carryover_family` | family or configuration |
| `Power Category` | `power_category` | family or configuration |
| `Applicatable Regulation` | `regulation` | family or configuration |
| `Applicable Tier` | `tier` | family or configuration |
| `Applicable Compliance Standard` | `compliance_standard` | family or configuration |
| `Fuel` | `fuel_type` | family or configuration |
| `Fuel Meter System` | `fuel_metering_system` | family or configuration |
| `Useful Life of Engine Family` | `useful_life` | family or configuration |
| `Engine Combustion Cycle` | `engine_cycle` | family or configuration |
| `Non Aftertreatment Device Type` | `non_aftertreatment_device` | family or configuration |
| `Aftertreatment Device Type` | `aftertreatment_device` | family or configuration |
| `Engine Model` | `engine_model` | family or configuration |
| `Engine Code` | `engine_code` | family or configuration |
| `Displacement` | `displacement_l` | family or configuration |
| `Certification Fuel` | `certification_fuel` | family or configuration |
| `Engine Operation` | `engine_operation` | family or configuration |
| `Test Procedure` | `test_procedure` | family or configuration |
| `Test Type` | `test_procedure_type` | family or configuration |

## Appendix C — Pollutant vocabulary

Highway source values map as follows. Nonroad sub-headers map through a parallel table in
`src/cidex/vocab.py`.

| Source value | CIDEX code |
|---|---|
| `Nitrogen Oxides` | `NOx` |
| `Carbon Monoxide` | `CO` |
| `Non-Methane Hydrocarbons` | `NMHC` |
| `Non-Methane Hydrocarbon Equivalent` | `NMHCE` |
| `Particulate Matter` | `PM` |
| `Carbon Dioxide` | `CO2` |
| `Methane` | `CH4` |
| `Nitrous Oxide` | `N2O` |
| `Formaldehyde` | `HCHO` |
| `Ammonia` | `NH3` |

---

*Generated by `scripts/11_report.py` from `stats.json` on 2026-09-15.*
