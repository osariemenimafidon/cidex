# CIDEX Build Spec — v1.0

**Compression-Ignition Engine Certification Panel**

Author: Osariemen Imafidon (ORCID 0009-0006-3069-4674), Independent Researcher
Drafted: 2026-09-14 · Status: **DRAFT — awaiting author approval before any pipeline code**

---

## 1. The question this answers

EPA publishes engine certification data for compression-ignition engines as two
separate Excel workbooks with incompatible internal structures. Answering even a
simple cross-cutting question — *how have certified NOx levels moved across
heavy-duty highway and nonroad engine families since Tier 4 / GHG Phase 1?* —
currently requires every researcher to independently reverse-engineer two
different layouts, reconcile two different pollutant encodings, and guess at the
engine-family naming convention.

CIDEX does that reconciliation once, publicly, with provenance, so the next
person starts from a analysis-ready panel instead of a spreadsheet.

## 2. Sources

| Source | Vintage | Retrieved | SHA-256 (first 16) |
|---|---|---|---|
| EPA Heavy-Duty Highway Gasoline & Diesel Certification Data, MY2015–present | 2026-03 file drop | 2026-09-14 | `3edfe15deef23182` |
| EPA Nonroad Compression-Ignition (NRCI) Certification Data, MY2011–present | 2026-03 file drop | 2026-09-14 | `9e78cf00ca4f9308` |

Both are US Government works, publicly downloadable without authentication, no
licence restriction on reuse. Updated quarterly by EPA — which is what makes the
annual-versioning commitment feasible.

Archives exist (highway 1982–2016; nonroad 1996–2011) and are **out of scope for
v1.0**, noted in the roadmap as a candidate v2.0 extension.

## 3. What profiling found

Three structural facts, each of which shapes the build:

**(a) Headers are on row 2, not row 1.** Both workbooks carry a merged group
header in row 1. The nonroad file uses a genuine two-level header: row 1 groups
(`Certification Level Steady-State Discrete Modal`, `Certification Level
Transient Test Results`, `FEL`, `Smoke Opacity`) and row 2 names the pollutant
within the group. A naive `read_excel` on either file produces silent garbage.
This alone is a reason the dataset is worth publishing.

**(b) The two panels have opposite shapes.** This is the core harmonization
problem and the substance of the data descriptor.

| | Highway | Nonroad |
|---|---|---|
| Shape | **Long** — one row per family × engine config × pollutant | **Wide** — one row per family, pollutants as columns |
| Pollutant encoding | `Pollutant Name` column (10 distinct values) | ~24 columns across 4 measurement groups |
| Rows | 7,804 | 10,214 |
| Unique engine families | 702 | 7,925 |
| Manufacturers | 27 | 86 |
| Model years | 2015–2026 | 2011–2027 |

**(c) The engine family name encodes the model year.** In both panels,
`nunique(Engine Family) == nunique(Model Year, Engine Family)` exactly. The
family name is therefore a true primary key, which confirms the premise of the
planned `enginefamily` parser and means no synthetic key is needed.

**(d) Nonroad carries a carryover lineage.** 7,530 of 10,214 rows name a
`Carryover Engine Family Name`. These chain, so a family's certification history
can be traced across model years. Nothing in the plan anticipated this, and it
is the most citable thing in the dataset — see §8.

## 4. Unit of analysis

One row per **(model year, engine family, pollutant, test type)**.

This is the lowest common denominator of the two source shapes. Highway rows
unpivot on test type (transient / steady-state); nonroad rows unpivot from wide
to long across measurement group. Family-level attributes (manufacturer, useful
life, aftertreatment, power category, tier, service class) move to a separate
family dimension table, joined on the family key.

Output is therefore **three tables**, not one:

- `cidex_family.csv` — one row per (MY, family): attributes, ~8,600 rows
- `cidex_emissions.csv` — one row per (MY, family, pollutant, test type): the long panel
- `cidex_carryover.csv` — resolved nonroad lineage edges

## 5. Measures and how each is computed

| Measure | Computation | Judgment call |
|---|---|---|
| `pollutant_std` | Source pollutant names mapped to a controlled vocabulary (NOx, NMHC, CO, PM, CO2, CH4, N2O, HCHO, NH3, NMHC+NOx) | **[VERIFY]** Highway `Non-Methane Hydrocarbon Equivalent` (13 rows) — fold into NMHC or keep distinct? Domain call. |
| `cert_result` | Highway: `TR Cert Result` / `SS Cert Result`. Nonroad: the group-header cell value. | Units differ by panel — see below |
| `standard` | Highway: `Transient Standard` / `SS Standard`. Nonroad: `Applicable Compliance Standard` | |
| `fel` | Family Emission Limit where certified to one | Null ≠ zero; encoded as null |
| `headroom` | `standard - cert_result`, only where both are non-null and same units | **[VERIFY]** Derived, not source. Author must confirm this is a defensible construct before it ships. |
| `units` | Recorded explicitly per row | **[VERIFY]** Highway is g/bhp-hr, nonroad is g/kW-hr. **No conversion is performed in v1.0.** Cross-panel numeric comparison without conversion is invalid, and the codebook will say so in those words. |
| `carryover_root` | Transitive closure over the carryover chain | **[VERIFY]** Cycle/orphan handling — QA reports both counts |

**The units question is the single largest correctness risk in this project.**
Converting silently would be worse than not converting. v1.0 ships both units
labelled, with a documented conversion factor offered as a helper function the
user must call deliberately.

## 6. Outputs

- Three CSVs above, plus a Parquet mirror
- `stats.json` — every number that appears in any document, written by the
  pipeline. No figure in this repo is typed by hand.
- Figures (built under the `dataviz` skill): families certified per model year by
  panel; pollutant coverage matrix; nonroad tier migration 2011→2027;
  carryover-chain depth distribution
- Documentation set: README, codebook, limitations, verification checklist,
  LICENSE, CITATION.cff
- Technical report: the harmonization pipeline with provenance appendix

## 7. Venues

- **Dataset**: Zenodo, versioned, CC BY 4.0
- **Data descriptor**: *Scientific Data* or *Data in Brief* — the long/wide
  harmonization plus the carryover lineage is the novel contribution
- **Code**: GitHub, MIT; `certdata` to PyPI once genuinely tested

## 8. Scope decision required from the author

The plan treats the nonroad panel as contingent on a later scoping decision.
Profiling argues for pulling it forward and **building both panels in v1.0**:

- Harmonizing *one* workbook is a cleaned spreadsheet. Harmonizing two
  structurally opposite workbooks into one schema is a methods contribution, and
  it is what a data descriptor referee will want to see.
- The nonroad panel is the larger and richer of the two (7,925 families, 86
  manufacturers, tier / power category / aftertreatment stratification).
- The carryover lineage exists only in the nonroad file.
- It is already downloaded and profiled. The marginal cost is now hours, not weeks.

Cost: v1.0 takes longer, and the descriptor must carry the units caveat prominently.

**Author decision required before §9 begins.**

## 9. Verification points (the gate)

Nothing publishes until the author personally:

1. Re-runs the pipeline from the README and reproduces `stats.json` byte-identically
2. Spot-checks **5 named engine families** against the EPA interactive certificate tool — the QA report names which five
3. Rules on every **[VERIFY]** call in §5
4. Confirms the units language in the codebook is technically correct
5. Confirms no `[TARGET]` line from the planning CV has leaked into any document
6. Revises the descriptor abstract into their own voice

## 10. Licence

- Data and documentation: **CC BY 4.0**
- Code: **MIT**
- Attribution: Imafidon, O. (2026). CIDEX: … Zenodo. [DOI pending]

---

## 11. Decisions taken 2026-09-14

The author delegated these. Each is a build decision, not a correctness
judgment — §9 still gates publication.

**D1 — Scope: both panels in v1.0.** Reasoning in §8. The harmonization of two
structurally opposite sources is the contribution; one panel alone is data
cleaning.

**D2 — Units: no conversion in v1.0.** Highway ships g/bhp-hr, nonroad ships
g/kW-hr, each row labelled in a `units` column. `cidex.units.to_g_per_kWh()` is
provided and must be called deliberately. The codebook states in plain language
that cross-panel numeric comparison without conversion is invalid.

**D3 — `Non-Methane Hydrocarbon Equivalent` stays distinct** from NMHC rather
than being folded into it. It is a different regulatory construct, and folding
destroys information that cannot be reconstructed downstream, whereas keeping it
separate costs a user one `isin()` call. General principle for this repo:
never destroy information the user can collapse themselves.

**D4 — `headroom` is NOT shipped as a column.** This reverses the draft §5.
A derived margin column sitting beside two incompatible unit systems is exactly
the footgun D2 exists to prevent; a user filtering across panels would produce
a plausible, wrong number with no warning. It ships as
`cidex.units.headroom(df)`, which raises on mixed units. Trivial for a user to
compute deliberately, impossible to compute accidentally.

**D5 — Carryover cycles and orphans are resolved transitively and reported,
never silently dropped.** QA emits both counts; any cycle is listed by family
name in the QA report for author inspection.
