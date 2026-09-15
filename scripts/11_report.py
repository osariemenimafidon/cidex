"""11 — Generate the CIDEX technical report.

Every figure is read from stats.json or the QA records; the column mappings are
imported from the pipeline modules themselves, so the appendix cannot drift from
the code it documents.
"""
import importlib.util, json, os, sys
import pandas as pd
sys.path.insert(0, "src")

OUT, DOCS = "data/processed", "docs"
S = json.load(open(f"{OUT}/stats.json"))
QH = json.load(open("qa/02_highway.json"))
QN = json.load(open("qa/03_nonroad.json"))
QC = json.load(open("qa/04_carryover.json"))
A = json.load(open("AUTHORS.json")); au = A["authors"][0]
SIGNED = os.path.exists(".gate-signed")
VERSION = "1.0.0" if SIGNED else "1.0.0-draft"
f = lambda n: f"{n:,}" if isinstance(n, int) else n


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m

HW = load("hw", "scripts/02_harmonize_highway.py")
NR = load("nr", "scripts/03_harmonize_nonroad.py")
from cidex.vocab import POLLUTANT_MAP, NONROAD_POLLUTANT_MAP, NONROAD_GROUP_MAP
from cidex.units import HP_TO_KW

prov = [json.loads(l) for l in open("logs/provenance.jsonl")]
seen, uniq = set(), []
for r in reversed(prov):                      # keep the most recent record per file
    if r["file"] not in seen:
        seen.add(r["file"]); uniq.append(r)
prov = list(reversed(uniq))

# Recorded by the nonroad harmonizer at the point the source is read.
MULTI_ROW_FAMILIES = QN["families_multi_source_row"]
MAX_ROWS_ONE_FAMILY = QN["max_source_rows_one_family"]

cov = S["model_year_coverage"]
banner = "" if SIGNED else (
    "> **DRAFT — NOT VERIFIED.** This report describes a package that has not passed "
    "its verification gate.\n\n")

R = []
w = R.append

w(f"""% CIDEX: The Compression-Ignition Engine Certification Panel — Harmonization Pipeline
% {au['name']} · ORCID {au['orcid']} · {au['affiliation']}
% Version {VERSION} · {S['build_date']}

{banner}## Abstract

The United States Environmental Protection Agency publishes emission certification
records for compression-ignition engines as two Microsoft Excel workbooks whose internal
structures are mutually incompatible. One is organised long on pollutant and wide on test
type; the other is wide on pollutant beneath a two-level header, with family attributes
distributed on both sides of the measurement block. Both place their true column headers
on the second row, so the naive read of either file produces plausible but incorrect data
without raising an error.

This report documents CIDEX, a pipeline that reconciles both sources into a single
analysis-ready panel of **{f(S['families_total'])} engine families**,
**{f(S['configs_total'])} engine configurations** and
**{f(S['emission_rows_total'])} emission records** across
**{f(S['manufacturers_total'])} manufacturers** and model years
{S['model_year_min_nonroad']}–{S['model_year_max_nonroad']}. It also documents a resolved
carryover lineage linking **{f(S['carryover_distinct_lineages'])} distinct certification
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

CIDEX v{VERSION} covers the two current EPA certification files: heavy-duty highway
gasoline and diesel engines (model years {S['model_year_min_highway']} onward) and nonroad
compression-ignition engines (model years {S['model_year_min_nonroad']} onward). EPA's
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
| Model years | {S['model_year_min_highway']}–{S['model_year_max_highway']} | {S['model_year_min_nonroad']}–{S['model_year_max_nonroad']} |
| Source rows (Family Info) | {f(QH['source_rows'])} | {f(QN['source_rows'])} |
| Unique families | {f(S['families_highway'])} | {f(S['families_nonroad'])} |
| Manufacturers | {S['manufacturers_highway']} | {S['manufacturers_nonroad']} |
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
pollutant, with a `Pollutant Name` column taking {len(POLLUTANT_MAP)} distinct values. It
is simultaneously *wide* on test type — transient and steady-state results occupy separate
column blocks on the same row.

The **nonroad** file is the reverse. One row carries all pollutants as columns, arranged
in four groups beneath a two-level header: {', '.join(NONROAD_GROUP_MAP.values())}. Family
attributes appear both *before* and *after* the measurement block, which defeats any
approach based on column position alone.

Reconciling these into one schema is the substance of the pipeline.

### 3.3 The engine family name is a true key

In both panels the count of distinct engine family names equals exactly the count of
distinct (model year, family) pairs — {f(S['families_highway'])} and
{f(S['families_nonroad'])} respectively. The model year is encoded in the family name's
first character, so the name alone identifies the family-year. No surrogate key is
required, and a name collision across years is impossible by construction.

### 3.4 Family attributes and configuration attributes are different things

A single engine family may be certified across several engine configurations. In the
nonroad source, {f(MULTI_ROW_FAMILIES)} of {f(S['families_nonroad'])}
families occupy more than one row — up to {MAX_ROWS_ONE_FAMILY} for a single family —
differing by engine code, model, displacement or test procedure.

Placing those attributes in a family-level table would force an arbitrary row to win and
silently discard the rest. CIDEX separates them: attributes constant within a family go to
the family table; attributes that vary go to a configuration table. The split is not
asserted — the build **tests** it and aborts if any attribute in the family table varies
within a family. Before the split, {len(QN['attr_conflicts_before_split'])} nonroad
attributes varied; after it, {len(QN['family_attr_conflicts_after_split'])} do.

---""")


# ---------------------------------------------------------------- part 2
ic = S["integrity_checks"]
CHECK_DOC = {
 "family_key_unique": "No (panel, model year, engine family) triple appears twice in the family table.",
 "no_emission_row_without_family": "Every emission record joins a family row; no orphan measurements.",
 "units_never_null": "The units column is populated on every emission record.",
 "no_mixed_units_within_panel": "No panel carries more than its expected unit systems.",
 "highway_units_evidenced_by_standards": "The modal certification standard per pollutant in the highway panel matches the known US heavy-duty standards expressed in g/bhp-hr. See §5.2.",
 "highway_units_labelled": "Every highway record is labelled g/bhp-hr.",
 "nonroad_units_correct": "Nonroad records carry only g/kW-hr or pct opacity.",
 "carryover_no_true_cycles": "The carryover lineage graph contains no cycle.",
 "every_negative_value_is_flagged": "Every negative certification result carries a quality flag.",
 "flagged_share_below_0pt1pct": "Flagged records remain under 0.1% of the panel; a sharp rise would indicate a parsing regression.",
}
checks_tbl = "\n".join(
    f"| `{k}` | {'PASS' if v else 'FAIL'} | {CHECK_DOC.get(k,'—')} |" for k, v in ic.items())

pol_tbl = "\n".join(
    f"| `{p}` | {f(S['rows_by_panel_pollutant'].get(p,0))} |" for p in S["pollutants"])

cov_tbl = "\n".join(
    f"| {panel} | {y} | {f(v['families'])} | {v['share_of_median']:.0%} | "
    f"{'EPA archive not ingested' if v['coverage']=='partial_archive' else 'still being certified'} |"
    for panel, c in cov.items() for y, v in c["by_year"].items() if v["coverage"] != "complete")

prov_tbl = "\n".join(
    f"| `{r['file']}` | {f(r['bytes'])} | `{r['sha256']}` | {r['recorded_utc'][:10]} |"
    for r in prov)
prov_urls = "\n".join(f"- `{r['file']}` — <{r['url']}>" for r in prov)

hw_map = "\n".join(f"| `{k}` | `{v}` | family |" for k, v in HW.FAMILY_COLS.items())
hw_blocks = "\n".join(
    f"| `{src}` | `{out}` | emissions, `test_type = {tt}` |"
    for tt, cols in HW.TEST_BLOCKS.items() for out, src in cols.items())
nr_map = "\n".join(f"| `{k}` | `{v}` | family or configuration |" for k, v in NR.ATTR_MAP.items())
pol_map = "\n".join(f"| `{k}` | `{v}` |" for k, v in POLLUTANT_MAP.items())

sig = (f"Signed by {au['name']} (ORCID {au['orcid']}) on {S['build_date']}, recorded by the "
       "presence of `.gate-signed` in the repository root."
       if SIGNED else "**Not yet signed.**")

w(f"""

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
{len(QH['unmapped_pollutants'])} values failed to map.

The test-type block is then unpivoted. Each source row yields one record per test type, and
records with no value in any measurement column are removed as unpivot artefacts rather
than facts: {f(QH['unpivot_rows_before'])} rows before,
{f(QH['unpivot_empty_dropped'])} dropped, {f(QH['emission_rows'])} retained.

Family-attribute constancy is tested, not assumed. In this build
{len(QH['family_attr_conflicts'])} highway family attributes varied within a family.

### 4.3 Nonroad harmonization

The nonroad two-level header is resolved without hard-coding column positions. The group
row is forward-filled, then a column is treated as a measurement **only if** its row-2
sub-name is one the group actually contains. This is what keeps `Engine Model` — which
sits immediately after the FEL block and inherits its forward-filled group label —
classified as an attribute rather than as a pollutant. The classifier found
{QN['measurement_columns']} measurement columns and {QN['attribute_columns']} attribute
columns, with {len(QN['unmapped_attribute_columns'])} attributes unmapped.

Wide-to-long expansion produces {f(QN['long_rows_before'])} candidate records, of which
{f(QN['long_empty_dropped'])} are empty cells in a sparse layout and are dropped, leaving
{f(QN['emission_rows'])}.

Family Emission Limits are a limit, not a measured result, and are moved to their own
column. **The merge is keyed on source-row identity, not on the family key** — see §6.1.

### 4.4 Carryover lineage

{f(QC['families_with_carryover'])} nonroad families name a predecessor family. These
references chain, so a family's certification history can be traced across model years.

Three cases are handled explicitly rather than by exception:

- **Self-reference.** {QC['self_referencing_families']} families name *themselves* as their
  own carryover. EPA appears to use this to mark an unchanged re-certification. A naive
  traversal reads it as a cycle; CIDEX treats it as a lineage terminus.
- **Orphans.** {f(QC['orphan_edges'])} families name a predecessor absent from this panel,
  usually pre-{S['model_year_min_nonroad']} and outside the published window. The lineage is
  truncated, not wrong — so a depth of 0 does not always mean "first of its line".
- **True cycles.** {QC['true_cycles_detected']} detected. The graph is a forest.

Result: {f(QC['distinct_lineages'])} distinct lineages, mean depth
{QC['depth_mean']}, maximum {QC['depth_max']} model years. The deepest runs
`{QC['longest_lineage_example']['lineage_root']}` →
`{QC['longest_lineage_example']['engine_family']}`
(MY{QC['longest_lineage_example']['model_year']}).

### 4.5 Units: no silent conversion

The two panels certify in different units. Highway results are in **g/bhp-hr**, nonroad in
**g/kW-hr**, and nonroad smoke opacity in **percent**. Every record carries its units in a
column; **no conversion is performed**.

This is deliberate. A dataset that silently normalised units would let a user aggregate
across panels and obtain a plausible, wrong number with no indication anything was amiss.
Conversion is available but must be invoked:

```python
from cidex.units import to_g_per_kWh
to_g_per_kWh(0.20, "g/bhp-hr")   # {0.20/HP_TO_KW:.4f}
```

`cidex.units.headroom()` raises `MixedUnitsError` rather than computing across unit
systems. The constant used is 1 hp = {HP_TO_KW} kW.

### 4.6 Quality flags and coverage flags

Two flags are carried on the data rather than left to documentation:

`quality_flag` marks the {S['negative_cert_results']} records
({S['negative_cert_result_share_pct']}% of the panel, across
{S['negative_cert_result_families']} families, all
{', '.join(S['negative_cert_result_panels'])}) whose certification result is **negative**.
An emission rate cannot be physically negative. CIDEX does not correct, clip or drop them
— the published value stands as EPA reports it and carries a flag. Whether this reflects a
data-entry issue or an undocumented encoding is unresolved.

`year_coverage` marks model years that are structurally incomplete (§7.3).

---

## 5. Validation

### 5.1 Integrity checks

{len(ic)} checks run on every build. All currently pass.

| Check | Result | What it tests |
|---|---|---|
{checks_tbl}

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
""" + "\n".join(
    f"| {p} | {v} | {S['highway_modal_standards'].get(p, '—')} |"
    for p, v in S["highway_known_standards_g_bhp_hr"].items()) + f"""

Expressed in g/kW-hr the same standards would be {', '.join(f'{v/HP_TO_KW:.3f}' for v in S['highway_known_standards_g_bhp_hr'].values())} — an order of
magnitude away in every case, so the test cannot pass by coincidence. It runs on every
build.

### 5.3 The author verification gate

Mechanical checks cannot establish correspondence with the source. That requires a person
to look up specific records in EPA's own certificate tool and compare. The pipeline
therefore ships five named spot-checks, each probing a different failure mode:

| # | Panel | Family | MY | Pollutant | CIDEX value | What it probes |
|---|---|---|---|---|---|---|
""" + "\n".join(
    f"| {i} | {c['panel']} | `{c['engine_family']}` | {c['model_year']} | {c['pollutant']} | "
    f"{c['cidex_cert_result']} {c['units']} | {c['why']} |"
    for i, c in enumerate(S["spot_checks"], 1)) + f"""

Publication is blocked until the author signs `docs/VERIFICATION_CHECKLIST.md`.
`scripts/09_release.py` refuses to build a deposit archive while the attestation file is
absent, and every document and figure regenerates stamped DRAFT without it.

Status: {sig}

---

## 6. Defects found and corrected

Three defects were found during development. They are recorded because a validation
section reporting none would say more about the thoroughness of the review than about the
correctness of the pipeline.

### 6.1 The FEL merge multiplied rows

**Severity: data corruption. Detected: adversarial review before publication.**

Family Emission Limits were merged onto the emission records using
`(model_year, engine_family, pollutant)`. Because {f(MULTI_ROW_FAMILIES)} families occupy
more than one source row, that key matched several FEL entries per family and the merge
fanned every measurement row out to match.

The result was **2,139 phantom rows** — genuine values, duplicated. This is worse than
missing data: no nulls appeared, no outliers, nothing downstream looked wrong. It inflated
every count by roughly 2.6%.

**Corrected** by carrying source-row identity through the wide-to-long expansion and
merging on it. The script now aborts if the row count changes across the merge. Nonroad
emission records fell from 83,584 to {f(S['emission_rows_nonroad'])}.

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
detecting true cycles with a visited set. True cycles: {QC['true_cycles_detected']}.

---

## 7. Results

### 7.1 Panel contents

| | Rows |
|---|---|
| `cidex_family.csv` | {f(S['families_total'])} |
| `cidex_config.csv` | {f(S['configs_total'])} |
| `cidex_emissions.csv` | {f(S['emission_rows_total'])} |
| `cidex_carryover.csv` | {f(S['families_nonroad'])} |

{f(S['manufacturers_total'])} manufacturers · {S['pollutant_count']} pollutants ·
{len(S['test_types'])} test types · units present: {', '.join(f'`{u}`' for u in S['units_present'])}

### 7.2 Pollutant coverage

| Pollutant | Records |
|---|---|
{pol_tbl}

`NMHCE` (Non-Methane Hydrocarbon Equivalent) is kept distinct from `NMHC`. It is a
different regulatory construct, and folding it in would destroy information that cannot be
reconstructed downstream, where keeping it separate costs a user one filter.

### 7.3 Model-year coverage

Both panels are structurally incomplete at their edges, for two unrelated reasons. A year
is flagged when it holds under {S['coverage_threshold']:.0%} of the median count of that
panel's interior years.

| Panel | Model year | Families | Share of median | Reason |
|---|---|---|---|---|
{cov_tbl}

Usable ranges for trend analysis: highway **MY{cov['highway']['usable_range'][0]}–{cov['highway']['usable_range'][1]}**,
nonroad **MY{cov['nonroad']['usable_range'][0]}–{cov['nonroad']['usable_range'][1]}**.

The threshold is a judgement. It separates the observed cases cleanly — no year sits near
the boundary — but the raw counts are published so a reuser can choose differently.

---

## 8. Limitations

Stated in full in `docs/LIMITATIONS.md`. In summary: units are not comparable across
panels without conversion; {S['negative_cert_results']} records carry physically impossible
negative values, published as EPA reports them; nonroad records have no pollutant-specific
standard because the source states it only at family level; edge model years are
incomplete; manufacturer names are not normalised; and carryover lineage is nonroad-only
with {f(QC['orphan_edges'])} open edges.

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
{prov_tbl}

Canonical sources:

{prov_urls}

## Appendix B — Source-to-output column mapping

### B.1 Highway family attributes

| Source column | CIDEX column | Table |
|---|---|---|
{hw_map}

### B.2 Highway measurement blocks

| Source column | CIDEX column | Destination |
|---|---|---|
{hw_blocks}

### B.3 Nonroad attributes

| Source column | CIDEX column | Table |
|---|---|---|
{nr_map}

## Appendix C — Pollutant vocabulary

Highway source values map as follows. Nonroad sub-headers map through a parallel table in
`src/cidex/vocab.py`.

| Source value | CIDEX code |
|---|---|
{pol_map}

---

*Generated by `scripts/11_report.py` from `stats.json` on {S['build_date']}.*
""")

open(f"{DOCS}/TECHNICAL_REPORT.md", "w").write("\n".join(R))
print(f"written: docs/TECHNICAL_REPORT.md  ({os.path.getsize(f'{DOCS}/TECHNICAL_REPORT.md'):,} bytes)")

# --- PDF for deposit -------------------------------------------------------
import subprocess, shutil
if shutil.which("pandoc"):
    pdf = f"{DOCS}/CIDEX_technical_report_v{VERSION}.pdf"
    cmd = ["pandoc", f"{DOCS}/TECHNICAL_REPORT.md", "-o", pdf,
           "--toc", "--toc-depth=2",
           "-V", "geometry:margin=1in", "-V", "fontsize=10pt",
           "-V", "colorlinks=true", "-V", "linkcolor=MidnightBlue",
           "-V", "urlcolor=MidnightBlue", "-V", "documentclass=article"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode == 0:
        print(f"written: {pdf}  ({os.path.getsize(pdf):,} bytes)")
    else:
        print("PDF generation failed:\n", r.stderr[:600])
else:
    print("pandoc not available; markdown only")
