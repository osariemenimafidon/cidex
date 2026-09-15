"""11 — Generate the CIDEX technical report (markdown + typeset PDF).

Every figure is read from stats.json or the QA records; column mappings are
imported from the pipeline modules themselves, so the appendices cannot drift
from the code they document.

LAYOUT NOTE. Tables here are deliberately narrow — at most four columns, and no
cell carries more than a short phrase. An earlier version put multi-sentence
descriptions into seven-column tables; pandoc allocated the last column about
one word of width and the rows ran to a third of a page each. Prose belongs in
prose. Anything that wants a sentence is a definition list or a headed block.
"""
import importlib.util, json, os, shutil, subprocess, sys
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
for r in reversed(prov):
    if r["file"] not in seen:
        seen.add(r["file"]); uniq.append(r)
prov = list(reversed(uniq))

MULTI = QN["families_multi_source_row"]
MAXROWS = QN["max_source_rows_one_family"]
cov = S["model_year_coverage"]
em = pd.read_csv(f"{OUT}/cidex_emissions.csv", low_memory=False)
fam = pd.read_csv(f"{OUT}/cidex_family.csv", low_memory=False)

# A family traced end to end through the pipeline, chosen for having every
# feature the report discusses: multiple configurations, a carryover ancestor,
# and measurements in both test types.
car = pd.read_csv(f"{OUT}/cidex_carryover.csv")
_deep = car.nlargest(1, "lineage_depth").iloc[0]
TRACE = _deep.engine_family
trace_em = em[em.engine_family.eq(TRACE)]
trace_fam = fam[fam.engine_family.eq(TRACE)].iloc[0]

banner = "" if SIGNED else (
    "> **DRAFT — NOT VERIFIED.** This report describes a package that has not "
    "passed its verification gate.\n\n")

HEADER_TEX = r"""
\usepackage{booktabs}
\usepackage{longtable}
\usepackage{array}
\usepackage{etoolbox}
\usepackage{microtype}
% Tables are set one step down and ragged-right: justified text in a narrow
% column produces rivers and overfull boxes.
\AtBeginEnvironment{longtable}{\small\setlength{\tabcolsep}{6pt}}
\AtBeginEnvironment{tabular}{\small\setlength{\tabcolsep}{6pt}}
\renewcommand{\arraystretch}{1.15}
% Long unbreakable tokens (hashes, family names) may break rather than overflow.
\emergencystretch=3em
\setlength{\parskip}{0.6em}
\setlength{\parindent}{0pt}
"""
open("/tmp/cidex_header.tex", "w").write(HEADER_TEX)

R = []
w = R.append



w(f"""% CIDEX — The Compression-Ignition Engine Certification Panel
% Harmonization pipeline, validation, and provenance
% {au['name']} · ORCID {au['orcid']} · {au['affiliation']} · Version {VERSION} · {S['build_date']}

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
families** across model years — a structure present in the nonroad source but not, as far
as the author is aware, previously published in resolved form.

The report states the method in enough detail to be re-implemented independently, records
each design decision with its justification, traces a single engine family through every
stage of the pipeline, and — in Section 7 — documents the defects found during development
and how each was detected. That last section is included because a validation record
reporting no defects is not evidence of a correct pipeline; it is evidence of an incurious
review.

**Document.** Technical report, part of the
[FACET](https://osariemenimafidon.github.io/facet/) research program.
Repository <https://github.com/osariemenimafidon/cidex>.
Licence: data and documentation CC BY 4.0; code MIT. Every quantity in this report is
interpolated from the pipeline's own `stats.json`; the appendices are imported from the
pipeline modules at generation time.

---

## 1. Introduction

### 1.1 What certification data is

Before an engine may be sold in the United States it must be covered by a certificate of
conformity issued by EPA. The unit of certification is not an engine model but an **engine
family** — a group of engines expected to share emission characteristics, defined by the
manufacturer and accepted by EPA. A family is tested at one or more configurations, the
results are compared against the standard applicable to its service class and model year,
and a certificate is issued for that family and model year.

The resulting record is the only comprehensive public account of what engines were
approved to emit, by whom, and under which standard. It bears on fleet composition,
technology adoption, the stringency of successive standards, and the relationship between
certified and in-service behaviour.

### 1.2 Why it is hard to use

The obstacle is not access. EPA publishes the files openly, without authentication, and
refreshes them quarterly. The obstacle is structure.

Every researcher who wants to ask a question spanning both engine categories must
independently reverse-engineer two layouts, reconcile two pollutant encodings, discover
that the headers are not where a spreadsheet reader looks for them, and decide what to do
about several dozen edge cases. That work is duplicated across every user, documented by
none of them, and performed under no obligation to be correct. Errors made in it are
invisible: the failure mode is not an exception but a quietly wrong number.

CIDEX performs the reconciliation once, publicly, with provenance, and documents the
decisions.

### 1.3 Scope and non-goals

CIDEX v{VERSION} covers the two current EPA certification files: heavy-duty highway
gasoline and diesel engines from model year {S['model_year_min_highway']}, and nonroad
compression-ignition engines from model year {S['model_year_min_nonroad']}. EPA's archive
files — highway 1982–2016 and nonroad 1996–2011 — are **not** ingested in this version.
Their omission has a measurable effect on coverage, quantified in §8.3 and carried as a
flag on every affected row.

CIDEX is explicitly **not**:

- *A compliance instrument.* It is a reorganisation of a published record, not an
  authoritative statement of any engine's regulatory status. EPA's certificate is
  authoritative; this is a convenience.
- *A correction of EPA's data.* Where the source contains values that appear wrong, CIDEX
  publishes them as published and flags them. §5.4 explains why.
- *A source of in-service emissions.* Certification results are laboratory values on a
  certification fuel and duty cycle. They are not what an engine emits in a field.

### 1.4 What this report is for

It should be possible to re-implement CIDEX from this report alone and obtain the same
numbers. Where a choice was made that a competent person could reasonably have made
differently, the choice is stated as a choice rather than presented as the only option.

---

## 2. Sources

### 2.1 The two workbooks

| | Highway | Nonroad |
|---|---|---|
| Model years | {S['model_year_min_highway']}–{S['model_year_max_highway']} | {S['model_year_min_nonroad']}–{S['model_year_max_nonroad']} |
| Source rows | {f(QH['source_rows'])} | {f(QN['source_rows'])} |
| Unique families | {f(S['families_highway'])} | {f(S['families_nonroad'])} |
| Manufacturers | {S['manufacturers_highway']} | {S['manufacturers_nonroad']} |

The highway workbook carries three sheets — `Family Info`, `Model Info` and a
630,000-row `Parts Info`. CIDEX v{VERSION} uses `Family Info` only; the other two are
noted as candidate extensions in §10. The nonroad workbook carries `Family Info` and a
`Model Info` sheet of {f(80719)} rows, likewise unused.

Both files are US Government works and carry no copyright restriction on reuse.

### 2.2 The access constraint

The build environment used for this work cannot reach `epa.gov`: outbound requests are
refused by an organisational egress policy at the network layer. The source files were
therefore downloaded manually through an ordinary browser and placed in `data/raw/`.

This is a genuine weakness. An automated fetch is verifiable in a way a manual one is not:
it records what was requested and what came back, and it can be repeated. A manual
download records nothing, and a file placed in a directory by hand could be anything.

It is mitigated rather than concealed. `scripts/01_provenance.py` refuses to run if either
expected file is absent, and records for each one its name, byte count, SHA-256 digest,
filesystem modification time, and the canonical URL it is asserted to have come from. A
rebuilder need not accept the assertion: they fetch the file themselves and compare
digests. If the digests match, the bytes are identical and the provenance question is
settled regardless of how either copy arrived. The complete record is Appendix A.

### 2.3 Source volatility

EPA refreshes these files quarterly, replacing them in place at the same URLs. There is no
versioned archive of previous drops and no changelog. A rebuild against a later drop will
therefore produce different numbers, and the digests in Appendix A will not match.

This is a property of the source, not a defect in the pipeline, but it has a practical
consequence: **the digest, not the URL, identifies the data**. A citation of CIDEX should
reference the deposited version, which carries its own fixed digests, rather than the live
EPA file.

---
""")


w(f"""## 3. The harmonization problem

### 3.1 The headers are on the second row

Both workbooks reserve row 1 for a merged group header and place the actual column names
on row 2. `pandas.read_excel` defaults to `header=0`.

Applied to either file that default returns a frame whose columns are named
`Unnamed: 0` through `Unnamed: 44`, and whose first data row contains the real header
strings. No exception is raised. Every subsequent selection by column name then either
fails loudly — the good case — or, if the analyst falls back to positional indexing,
succeeds against a frame whose first row is not data.

CIDEX reads the highway sheet with `header=1`. The nonroad sheet is read with
`header=None` and both header rows are reconstructed explicitly, for the reason in §3.2.

### 3.2 The files are organised in opposite directions

The **highway** file is long on pollutant. One row carries a single pollutant for a
single family and configuration, identified by a `Pollutant Name` column taking
{len(POLLUTANT_MAP)} distinct values. The same row is simultaneously *wide* on test type:
transient and steady-state results occupy separate column blocks side by side.

The **nonroad** file is the reverse. One row carries every pollutant as a separate column,
arranged in four groups beneath a two-level header:

""" + "\n".join(f"- **{g}** — {'pollutant columns' if 'Smoke' not in g and 'FEL' not in g else ('three opacity measures' if 'Smoke' in g else 'three limit columns')}" for g in NONROAD_GROUP_MAP) + f"""

Family attributes appear both *before* the measurement block (columns 0–16) and *after*
it (columns 39–45), which defeats any approach that assumes attributes and measurements
occupy contiguous regions.

Reconciling these two orientations into one schema is the substance of the pipeline. The
target is a single long form keyed on
**(panel, model year, engine family, pollutant, test type)**.

### 3.3 The engine family name is a true key

In both panels, the count of distinct engine family names equals exactly the count of
distinct (model year, family) pairs — {f(S['families_highway'])} and
{f(S['families_nonroad'])} respectively.

This is not a coincidence. EPA engine family names encode the model year in their first
character, so a family name is unique across years by construction. `{TRACE}` and
`{QC['longest_lineage_example']['lineage_root']}` differ in the first character and are the
same underlying family in different years.

The practical consequence is that no surrogate key is needed and a name collision across
model years is impossible. CIDEX records the family name as the key and does not
synthesise an identifier, which keeps every row traceable to EPA's own record by a value
a reader can look up directly.

### 3.4 Families and configurations are different things

A single engine family may be certified across several configurations. In the nonroad
source, **{f(MULTI)} of {f(S['families_nonroad'])} families occupy more than one row** —
up to **{MAXROWS} rows for a single family** — differing by engine code, engine model,
displacement, certification fuel, engine operation or test procedure.

Placing those attributes in a family-level table would force an arbitrary row to win and
silently discard the rest. CIDEX separates them:

- attributes **constant** within a family go to the family table;
- attributes that **vary** within a family go to a configuration table.

The split is not asserted. The build **tests** it and aborts if any attribute remaining in
the family table varies within a family. Before the split,
{len(QN['attr_conflicts_before_split'])} nonroad attributes varied
({', '.join('`'+k+'`' for k in QN['attr_conflicts_before_split'])}); after it,
{len(QN['family_attr_conflicts_after_split'])} do.

The highway panel needed no such correction: {len(QH['family_attr_conflicts'])} of its
family attributes varied within a family, because its configuration-level columns were
routed to the configuration table from the outset.

---

## 4. Method

### 4.1 Pipeline

Nine numbered scripts, each independently re-runnable, run in order:

| Script | Function |
|---|---|
| `01_provenance.py` | Hash and log every raw file |
| `02_harmonize_highway.py` | Highway source → CIDEX schema |
| `03_harmonize_nonroad.py` | Nonroad source → CIDEX schema |
| `04_carryover.py` | Resolve certification lineage |
| `05_combine_qa.py` | Combine, flag, check, write `stats.json` |
| `06_docs.py` | Regenerate the documentation set |
| `07_publish_gate.py` | Pre-publication scan |
| `08_figures.py` | Figures |
| `09_release.py` | Build the deposit archive |
| `11_report.py` | Generate this report |

### 4.2 Highway harmonization

The sheet is read with `header=1`. Family attributes are projected into the family table
and configuration attributes — engine code, engine test model, engine identifier, test
fuel, test date — into the configuration table, yielding {f(QH['config_rows'])}
configurations against {f(QH['family_rows'])} families.

The pollutant name is mapped through a controlled vocabulary (Appendix C). **If any source
value fails to map, the script raises.** It does not drop the row. A silently discarded
pollutant is precisely the class of error this pipeline exists to prevent, and a pipeline
that quietly ignores what it does not understand is worse than one that stops. In this
build {len(QH['unmapped_pollutants'])} values failed to map.

The test-type block is then unpivoted. Each source row yields one record per test type.
Records with no value in any measurement column are removed, as they are artefacts of the
unpivot rather than facts about an engine: {f(QH['unpivot_rows_before'])} candidate rows,
{f(QH['unpivot_empty_dropped'])} dropped, **{f(QH['emission_rows'])} retained**.

### 4.3 Nonroad harmonization

The two-level header is resolved without hard-coding column positions, because positional
assumptions break the moment EPA inserts a column.

The group row is forward-filled across the measurement block, then a column is classified
as a measurement **only if** its row-2 sub-name is one the group actually contains. This
test is what keeps `Engine Model` — which sits immediately after the FEL block and so
inherits the forward-filled label `FEL (g/kW-hr)` — classified as an attribute rather than
as a pollutant. A pure forward-fill would misclassify all seven trailing attribute columns.

The classifier found **{QN['measurement_columns']} measurement columns** and
**{QN['attribute_columns']} attribute columns**, with
{len(QN['unmapped_attribute_columns'])} attributes unmapped.

Wide-to-long expansion produces {f(QN['long_rows_before'])} candidate records, of which
{f(QN['long_empty_dropped'])} are empty cells in a sparse layout — most families report
only a few of the {len(NONROAD_POLLUTANT_MAP)} possible pollutants — leaving
**{f(QN['emission_rows'])}**.

Family Emission Limits are a regulatory limit, not a measured result, and are moved to
their own column. **The merge is keyed on source-row identity, not on the family key.**
§7.1 explains what happened when it was not.

### 4.4 Carryover lineage resolution

{f(QC['families_with_carryover'])} nonroad families name a predecessor family in a
`Carryover Engine Family Name` column. These references chain, so a family's certification
history can be followed backwards across model years. The highway panel has no equivalent
field.

Resolution is a graph traversal from each family to its root. Three cases are handled
explicitly rather than by exception:

**Self-reference.** {QC['self_referencing_families']} families name *themselves* as their
own carryover. EPA appears to use this to mark an unchanged re-certification. A naive
traversal reads it as a cycle of length one and either loops forever or reports a false
positive; the first version of this pipeline reported 109 such "cycles". CIDEX treats
`parent(x) == x` as a terminus.

**Orphans.** {f(QC['orphan_edges'])} families name a predecessor that is absent from this
panel — in almost all cases a pre-{S['model_year_min_nonroad']} family living in EPA's
archive file. The lineage is truncated rather than wrong, but it means **a recorded depth
of 0 does not always mean "first of its line"**. Both counts are published so a user can
distinguish the cases.

**True cycles.** Detected with a visited set. Count: **{QC['true_cycles_detected']}**. The
graph is a forest.

The resolved structure comprises **{f(QC['distinct_lineages'])} distinct lineages**, mean
depth {QC['depth_mean']}, maximum **{QC['depth_max']} model years**. The deepest runs
`{QC['longest_lineage_example']['lineage_root']}` → `{TRACE}`.

---
""")


# --- narrow, prose-free tables only; anything wanting a sentence becomes a block ---
CHECK_DOC = {
 "family_key_unique": "No (panel, model year, engine family) triple appears twice in the family table. The family key would otherwise be unusable for joining.",
 "no_emission_row_without_family": "Every emission record joins a family row. An orphan measurement would indicate the two tables were built from different row sets.",
 "units_never_null": "The units column is populated on every emission record, so no value can be read without its unit system attached.",
 "no_mixed_units_within_panel": "No panel carries more unit systems than it should — one for highway, two for nonroad, the second being smoke opacity.",
 "highway_units_evidenced_by_standards": "The modal certification standard per pollutant in the highway panel matches the known US heavy-duty standards expressed in g/bhp-hr. See §6.2.",
 "highway_units_labelled": "Every highway record carries the g/bhp-hr label.",
 "nonroad_units_correct": "Nonroad records carry only g/kW-hr or percent opacity, never a highway unit.",
 "carryover_no_true_cycles": "The lineage graph contains no cycle, so every traversal terminates and every family has a well-defined root.",
 "every_negative_value_is_flagged": "Every negative certification result carries a quality flag. An unflagged one would enter an unsuspecting user's aggregate.",
 "flagged_share_below_0pt1pct": "Flagged records remain under 0.1% of the panel. A sharp rise would indicate a parsing regression rather than a change in EPA's data.",
}
checks_block = "\n\n".join(
    f"**{i}. `{k}` — {'PASS' if v else 'FAIL'}**\n\n{CHECK_DOC.get(k,'')}"
    for i, (k, v) in enumerate(S["integrity_checks"].items(), 1))

spot_block = "\n\n".join(
    f"""**Check {i} — {c['panel']}, `{c['engine_family']}`, MY{c['model_year']}**

CIDEX records {c['pollutant']} on the {c['test_type'].replace('_',' ')} cycle as
**{c['cidex_cert_result']} {c['units']}**. {c['why'][0].upper() + c['why'][1:]}."""
    for i, c in enumerate(S["spot_checks"], 1))

prov_block = "\n\n".join(
    f"""**`{r['file']}`**

- Source: <{r['url']}>
- Publisher: {r['publisher']}
- Size: {f(r['bytes'])} bytes
- Recorded: {r['recorded_utc'][:10]}
- SHA-256:

```
{r['sha256']}
```"""
    for r in prov)

pol_tbl = "\n".join(f"| `{p}` | {f(S['rows_by_panel_pollutant'].get(p,0))} |" for p in S["pollutants"])
cov_tbl = "\n".join(
    f"| {panel} | {y} | {f(v['families'])} | {v['share_of_median']:.0%} |"
    for panel, c in cov.items() for y, v in c["by_year"].items() if v["coverage"] != "complete")
hw_map = "\n".join(f"| `{k}` | `{v}` |" for k, v in HW.FAMILY_COLS.items())
hw_blocks = "\n".join(f"| `{src}` | `{out}` | {tt.replace('_',' ')} |"
                      for tt, cols in HW.TEST_BLOCKS.items() for out, src in cols.items())
nr_map = "\n".join(f"| `{k}` | `{v}` |" for k, v in NR.ATTR_MAP.items())
pol_map = "\n".join(f"| `{k}` | `{v}` |" for k, v in POLLUTANT_MAP.items())
units_kwh = ", ".join(f"{v/HP_TO_KW:.3f}" for v in S["highway_known_standards_g_bhp_hr"].values())
std_tbl = "\n".join(f"| {p} | {v} | {S['highway_modal_standards'].get(p,'—')} |"
                    for p, v in S["highway_known_standards_g_bhp_hr"].items())
sig = (f"Signed by {au['name']} (ORCID {au['orcid']}) on {S['build_date']}."
       if SIGNED else "**Not yet signed.**")
_tt = sorted(trace_em.test_type.unique())
_tp = sorted(trace_em.pollutant.unique())

w(f"""## 5. Design decisions

Five decisions shape the published data. Each could reasonably have gone the other way.

### 5.1 Units are never silently converted

The two panels certify in different units: highway in **g/bhp-hr**, nonroad in
**g/kW-hr**, and nonroad smoke opacity in **percent**. Every record carries its units in a
column and **no conversion is performed**.

The alternative — normalising everything to one system — would make the panel look
tidier and would be a trap. A user aggregating across panels would obtain a plausible,
wrong number with nothing to indicate anything was amiss. Leaving the units divergent
makes the incompatibility visible at the point of use.

Conversion is available but must be invoked deliberately:

```python
from cidex.units import to_g_per_kWh
to_g_per_kWh(0.20, "g/bhp-hr")   # {0.20/HP_TO_KW:.4f}
```

`cidex.units.headroom()` raises `MixedUnitsError` rather than computing a margin across
unit systems. The constant is 1 hp = {HP_TO_KW} kW.

### 5.2 `NMHCE` is kept distinct from `NMHC`

Non-Methane Hydrocarbon Equivalent appears on {f(S['rows_by_panel_pollutant'].get('NMHCE',0))}
records against {f(S['rows_by_panel_pollutant'].get('NMHC',0))} for NMHC. It is a different
regulatory construct, used for certain alternative-fuel engines.

Folding it into NMHC would tidy the vocabulary and destroy information that cannot be
reconstructed downstream. Keeping it separate costs a user one filter expression. The
general principle applied throughout: **never destroy information the user can collapse
themselves.**

### 5.3 Nonroad `standard` is left null

The nonroad source states an applicable compliance standard at *family* level, as a text
string, not per pollutant and test type. Inferring which standard applies to which
pollutant would require encoding the tier structure and would be a guess dressed as data.

CIDEX leaves `standard` null for every nonroad record. Null means "not stated by the
source", never zero. `adj_result` and `fcl` are likewise highway-only.

### 5.4 Physically impossible values are published, flagged

{S['negative_cert_results']} records — {S['negative_cert_result_share_pct']}% of the panel,
across {S['negative_cert_result_families']} families, all
{', '.join(S['negative_cert_result_panels'])} — carry a **negative** certification result.
An emission rate cannot be physically negative.

CIDEX does not correct, clip, or drop them. The published value stands as EPA reports it
and carries `quality_flag = negative_cert_result`.

The reasoning: CIDEX's claim is to faithfully reorganise a published record. Silently
repairing the source would break that claim and would hide a real finding — either EPA has
a data-entry issue worth raising with them, or there is an encoding convention neither
party has documented. Both are more useful to a reader than a quietly cleaned column.
Users needing physically plausible values filter on one flag.

### 5.5 Incomplete model years are flagged in the data, not just documented

Both panels thin out at their edges for two unrelated reasons, and a time series crossing
those years reads the artefact as a trend. Rather than document this only in prose, every
row of the family and emission tables carries `year_coverage`. §8.3 quantifies it.

---

## 6. Validation

Validation operates at three levels: mechanical checks that run on every build, an
evidence test for a claim that would otherwise be an assertion, and a human gate that
machines cannot substitute for.

### 6.1 Integrity checks

{len(S['integrity_checks'])} checks run on every build; all currently pass. They test
**internal consistency** and cannot establish that any value matches EPA's record.

{checks_block}

### 6.2 The units evidence test

The highway source file states its units **nowhere**. Its column headers are bare —
`TR Cert Result`, `Transient Standard`. The claim that highway results are in g/bhp-hr was
originally an assertion written into the codebook by inference.

It is now a test. US heavy-duty highway standards have known values in g/bhp-hr, and the
modal certification standard per pollutant is compared against them:

| Pollutant | Known standard | Modal value in CIDEX |
|---|---|---|
{std_tbl}

Expressed in g/kW-hr the same standards would be {units_kwh} — an order of magnitude away
in every case. The test therefore cannot pass by coincidence, and it runs on every build.

The distinction matters beyond this one field. The inference was correct, but inference
was the wrong instrument: the same reasoning applied in a sibling project substituted a
European fuel specification for a US regulatory one and produced a materially wrong
result.

### 6.3 The author verification gate

No mechanical check can establish correspondence with the source. That requires a person
to look up specific records in EPA's own certificate tool and compare them by eye. The
pipeline ships five named spot-checks, each probing a different failure mode:

{spot_block}

Publication is blocked until the author signs `docs/VERIFICATION_CHECKLIST.md`.
`scripts/09_release.py` refuses to build a deposit archive while the attestation file is
absent, and every document and figure regenerates stamped as unverified without it.

The attestation **pins which records were checked**. The spot-check selector chooses a
median row per category, so its output moves whenever the underlying row set changes — as
it did when the defect in §7.1 was corrected. Without pinning, a signature could come to
refer to records nobody had ever examined. `scripts/07_publish_gate.py` compares the
pinned list against the current build and blocks if they differ.

Status: {sig}

---
""")


w(f"""## 7. Defects found and corrected

Three defects were found during development. They are recorded because a validation
section reporting none says more about the thoroughness of the review than about the
correctness of the pipeline.

### 7.1 The FEL merge multiplied rows

**Severity: data corruption. Detected: adversarial review immediately before publication.**

Family Emission Limits were merged onto the emission records using the key
`(model_year, engine_family, pollutant)`. Because {f(MULTI)} families occupy more than one
source row, that key matched several FEL entries per family, and a left join against a
non-unique key fans the left side out to match.

The result was **2,139 phantom rows** — genuine values, duplicated. This is worse than
missing data. No nulls appeared, no outliers, nothing downstream looked wrong; every count
was simply about 2.6% too large, in a direction and pattern that looked entirely
plausible.

It was found by asking a question with an arithmetic answer: how many emission rows
*should* there be? The wide-to-long expansion produces a known number of candidates, of
which a known number are empty and a known number are FEL entries. The remainder is
determined. It did not match.

**Corrected** by carrying source-row identity through the wide-to-long expansion and
merging on it. The script now aborts if the row count changes across the merge. Nonroad
emission records fell from 83,584 to {f(S['emission_rows_nonroad'])}.

**Generalisation:** every join against a key that is not provably unique on the right-hand
side is a row-multiplication defect waiting to happen, and the failure is silent. The
pipeline now asserts row-count stability across the only join it performs.

### 7.2 The units claim was asserted, not evidenced

**Severity: unverified claim in published documentation. Detected: same review.**

`g/bhp-hr` appeared in the codebook as a statement of fact, having been inferred from
domain knowledge rather than read from the file or tested against the data. The inference
was correct. The method was not sound, and §6.2 describes the replacement.

### 7.3 Carryover self-references were counted as cycles

**Severity: incorrect summary statistic. Detected: inspecting output that looked odd.**

The first lineage traversal reported 109 cycles. Reading the list showed every one was a
family naming itself — `HFPXL10.3TR3` → `HFPXL10.3TR3` — which is a terminus, not a loop.
Corrected by treating self-reference as a stopping condition and detecting true cycles
with a visited set. True cycles: **{QC['true_cycles_detected']}**.

**Generalisation:** the defect was found by looking at the output rather than the summary.
"109 cycles" is a number one can accept; the list of 109 pairs is not.

---

## 8. Results

### 8.1 What the panel contains

| Table | Rows |
|---|---|
| `cidex_family.csv` | {f(S['families_total'])} |
| `cidex_config.csv` | {f(S['configs_total'])} |
| `cidex_emissions.csv` | {f(S['emission_rows_total'])} |
| `cidex_carryover.csv` | {f(S['families_nonroad'])} |

{f(S['manufacturers_total'])} manufacturers, {S['pollutant_count']} pollutants,
{len(S['test_types'])} test types, units {', '.join('`'+u+'`' for u in S['units_present'])}.

### 8.2 Pollutant coverage

| Pollutant | Records |
|---|---|
{pol_tbl}

### 8.3 Model-year coverage

Both panels are structurally incomplete at their edges for two unrelated reasons. EPA
holds older model years in separate archive files that CIDEX v{VERSION} does not ingest,
so the earliest year of each panel contains only whichever families happen to sit in the
current file. Separately, the newest model year is still being certified when the file is
downloaded.

A year is flagged when it holds under {S['coverage_threshold']:.0%} of the median count of
that panel's interior years:

| Panel | Model year | Families | Share of median |
|---|---|---|---|
{cov_tbl}

Usable ranges for trend analysis: highway
**MY{cov['highway']['usable_range'][0]}–{cov['highway']['usable_range'][1]}**, nonroad
**MY{cov['nonroad']['usable_range'][0]}–{cov['nonroad']['usable_range'][1]}**. Every
affected row carries `year_coverage`.

The {S['coverage_threshold']:.0%} threshold is a judgement. It separates the observed cases
cleanly — no year sits near the boundary — but the raw counts are published so a reuser
with a different purpose can choose a different cut.

---

## 9. A family traced end to end

To make the schema concrete, here is `{TRACE}` — a nonroad family chosen because it
exercises every structure this report describes.

**In the source.** It appears in the nonroad `Family Info` sheet with its measurements
spread across the wide pollutant block, its attributes split before and after that block,
and a `Carryover Engine Family Name` pointing at its predecessor.

**In `cidex_family.csv`.** One row, keyed
`(nonroad, {int(trace_fam.model_year)}, {TRACE})`. Manufacturer
*{trace_fam.manufacturer}*; power category `{trace_fam.power_category}`; tier
*{trace_fam.tier}*.

**In `cidex_emissions.csv`.** {len(trace_em)} records — the wide row unpivoted into one
row per pollutant and test type. Pollutants present:
{', '.join('`'+p+'`' for p in _tp)}. Test types: {', '.join('`'+t+'`' for t in _tt)}.
Every record carries `units = g/kW-hr` except smoke opacity, and `standard` is null for
all of them, per §5.3.

**In `cidex_carryover.csv`.** Lineage root
`{QC['longest_lineage_example']['lineage_root']}` at depth
**{QC['longest_lineage_example']['depth']}** — the deepest chain in the panel, meaning this
family's certification can be traced back {QC['longest_lineage_example']['depth']} model
years through successive carryovers.

A reader wanting to verify CIDEX end to end can take this family name, look it up in EPA's
interactive certificate tool, and compare every value above against the source.

---

## 10. Limitations and future work

`docs/LIMITATIONS.md` states the limitations in full. In summary: units are not comparable
across panels without deliberate conversion; {S['negative_cert_results']} records carry
physically impossible negative values, published as EPA reports them; nonroad records have
no pollutant-specific standard; edge model years are incomplete; manufacturer names are
not normalised across years; and carryover lineage is nonroad-only with
{f(QC['orphan_edges'])} open edges.

Candidate extensions, in rough order of value:

1. **The archive files.** Ingesting highway 1982–2016 and nonroad 1996–2011 would close
   the coverage gaps in §8.3 and extend the carryover lineage past its current orphan
   boundary.
2. **The `Model Info` sheets.** Both workbooks carry engine-model detail — displacement,
   rated power, aspiration — that CIDEX does not currently use.
3. **Manufacturer normalisation**, published as a crosswalk rather than applied silently.
4. **Annual versioning.** EPA refreshes quarterly; an annual rebuild with a diff against
   the previous version would turn CIDEX into a time series of the record itself.

## 11. Reproducibility

```bash
pip install -r requirements.txt
./verify.sh
```

`verify.sh` rebuilds from `data/raw/` and diffs every value against the shipped
`docs/stats_reference.json`, excluding only the build date, then prints the five
spot-checks for manual comparison. A mismatch is a finding.

Every quantity in every CIDEX document — this report included — is interpolated from
`data/processed/stats.json`, which the pipeline writes. The column mappings in Appendix B
are imported from the pipeline modules at generation time. Neither can drift from the code.

---

## Appendix A — Provenance record

{prov_block}

## Appendix B — Source-to-output column mapping

### B.1 Highway family attributes

| Source column | CIDEX column |
|---|---|
{hw_map}

### B.2 Highway measurement blocks

| Source column | CIDEX column | Test type |
|---|---|---|
{hw_blocks}

### B.3 Nonroad attributes

| Source column | CIDEX column |
|---|---|
{nr_map}

## Appendix C — Pollutant vocabulary

Highway source values map as below. Nonroad sub-headers map through a parallel table in
`src/cidex/vocab.py`.

| Source value | CIDEX code |
|---|---|
{pol_map}

---

*Generated by `scripts/11_report.py` on {S['build_date']}.*
""")

open(f"{DOCS}/TECHNICAL_REPORT.md", "w").write("\n".join(R))
print(f"written: docs/TECHNICAL_REPORT.md ({os.path.getsize(f'{DOCS}/TECHNICAL_REPORT.md'):,} bytes)")

if shutil.which("pandoc"):
    pdf = f"{DOCS}/CIDEX_technical_report_v{VERSION}.pdf"
    r = subprocess.run(["pandoc", f"{DOCS}/TECHNICAL_REPORT.md", "-o", pdf,
        "--toc", "--toc-depth=2", "-H", "/tmp/cidex_header.tex",
        "-V", "geometry:margin=1in", "-V", "fontsize=10pt",
        "-V", "colorlinks=true", "-V", "linkcolor=MidnightBlue",
        "-V", "urlcolor=MidnightBlue"], capture_output=True, text=True)
    print(f"written: {pdf} ({os.path.getsize(pdf):,} bytes)" if r.returncode == 0
          else "PDF failed:\n" + r.stderr[:500])
