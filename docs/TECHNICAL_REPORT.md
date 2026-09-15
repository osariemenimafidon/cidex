% CIDEX — The Compression-Ignition Engine Certification Panel
% Harmonization pipeline, validation, and provenance
% Imafidon, Osariemen · ORCID 0009-0006-3069-4674 · Independent Researcher · Version 1.0.0 · 2026-09-15

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

CIDEX v1.0.0 covers the two current EPA certification files: heavy-duty highway
gasoline and diesel engines from model year 2015, and nonroad
compression-ignition engines from model year 2011. EPA's archive
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
| Model years | 2015–2026 | 2011–2027 |
| Source rows | 7,804 | 10,214 |
| Unique families | 702 | 7,925 |
| Manufacturers | 27 | 86 |

The highway workbook carries three sheets — `Family Info`, `Model Info` and a
630,000-row `Parts Info`. CIDEX v1.0.0 uses `Family Info` only; the other two are
noted as candidate extensions in §10. The nonroad workbook carries `Family Info` and a
`Model Info` sheet of 80,719 rows, likewise unused.

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

## 3. The harmonization problem

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
10 distinct values. The same row is simultaneously *wide* on test type:
transient and steady-state results occupy separate column blocks side by side.

The **nonroad** file is the reverse. One row carries every pollutant as a separate column,
arranged in four groups beneath a two-level header:

- **Certification Level Steady-State Discrete Modal** — pollutant columns
- **Certification Level Transient Test Results** — pollutant columns
- **FEL** — three limit columns
- **Smoke Opacity** — three opacity measures

Family attributes appear both *before* the measurement block (columns 0–16) and *after*
it (columns 39–45), which defeats any approach that assumes attributes and measurements
occupy contiguous regions.

Reconciling these two orientations into one schema is the substance of the pipeline. The
target is a single long form keyed on
**(panel, model year, engine family, pollutant, test type)**.

### 3.3 The engine family name is a true key

In both panels, the count of distinct engine family names equals exactly the count of
distinct (model year, family) pairs — 702 and
7,925 respectively.

This is not a coincidence. EPA engine family names encode the model year in their first
character, so a family name is unique across years by construction. `TCPXL18.1NYS` and
`CCPXL18.1NYS` differ in the first character and are the
same underlying family in different years.

The practical consequence is that no surrogate key is needed and a name collision across
model years is impossible. CIDEX records the family name as the key and does not
synthesise an identifier, which keeps every row traceable to EPA's own record by a value
a reader can look up directly.

### 3.4 Families and configurations are different things

A single engine family may be certified across several configurations. In the nonroad
source, **1,487 of 7,925 families occupy more than one row** —
up to **34 rows for a single family** — differing by engine code, engine model,
displacement, certification fuel, engine operation or test procedure.

Placing those attributes in a family-level table would force an arbitrary row to win and
silently discard the rest. CIDEX separates them:

- attributes **constant** within a family go to the family table;
- attributes that **vary** within a family go to a configuration table.

The split is not asserted. The build **tests** it and aborts if any attribute remaining in
the family table varies within a family. Before the split,
7 nonroad attributes varied
(`engine_model`, `engine_code`, `displacement_l`, `certification_fuel`, `engine_operation`, `test_procedure`, `test_procedure_type`); after it,
0 do.

The highway panel needed no such correction: 0 of its
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
fuel, test date — into the configuration table, yielding 875
configurations against 702 families.

The pollutant name is mapped through a controlled vocabulary (Appendix C). **If any source
value fails to map, the script raises.** It does not drop the row. A silently discarded
pollutant is precisely the class of error this pipeline exists to prevent, and a pipeline
that quietly ignores what it does not understand is worse than one that stops. In this
build 0 values failed to map.

The test-type block is then unpivoted. Each source row yields one record per test type.
Records with no value in any measurement column are removed, as they are artefacts of the
unpivot rather than facts about an engine: 15,608 candidate rows,
2,184 dropped, **13,424 retained**.

### 4.3 Nonroad harmonization

The two-level header is resolved without hard-coding column positions, because positional
assumptions break the moment EPA inserts a column.

The group row is forward-filled across the measurement block, then a column is classified
as a measurement **only if** its row-2 sub-name is one the group actually contains. This
test is what keeps `Engine Model` — which sits immediately after the FEL block and so
inherits the forward-filled label `FEL (g/kW-hr)` — classified as an attribute rather than
as a pollutant. A pure forward-fill would misclassify all seven trailing attribute columns.

The classifier found **22 measurement columns** and
**24 attribute columns**, with
0 attributes unmapped.

Wide-to-long expansion produces 224,708 candidate records, of which
141,657 are empty cells in a sparse layout — most families report
only a few of the 8 possible pollutants — leaving
**81,445**.

Family Emission Limits are a regulatory limit, not a measured result, and are moved to
their own column. **The merge is keyed on source-row identity, not on the family key.**
§7.1 explains what happened when it was not.

### 4.4 Carryover lineage resolution

5,982 nonroad families name a predecessor family in a
`Carryover Engine Family Name` column. These references chain, so a family's certification
history can be followed backwards across model years. The highway panel has no equivalent
field.

Resolution is a graph traversal from each family to its root. Three cases are handled
explicitly rather than by exception:

**Self-reference.** 30 families name *themselves* as their
own carryover. EPA appears to use this to mark an unchanged re-certification. A naive
traversal reads it as a cycle of length one and either loops forever or reports a false
positive; the first version of this pipeline reported 109 such "cycles". CIDEX treats
`parent(x) == x` as a terminus.

**Orphans.** 568 families name a predecessor that is absent from this
panel — in almost all cases a pre-2011 family living in EPA's
archive file. The lineage is truncated rather than wrong, but it means **a recorded depth
of 0 does not always mean "first of its line"**. Both counts are published so a user can
distinguish the cases.

**True cycles.** Detected with a visited set. Count: **0**. The
graph is a forest.

The resolved structure comprises **2,541 distinct lineages**, mean
depth 1.382, maximum **14 model years**. The deepest runs
`CCPXL18.1NYS` → `TCPXL18.1NYS`.

---

## 5. Design decisions

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
to_g_per_kWh(0.20, "g/bhp-hr")   # 0.2682
```

`cidex.units.headroom()` raises `MixedUnitsError` rather than computing a margin across
unit systems. The constant is 1 hp = 0.7456998716 kW.

### 5.2 `NMHCE` is kept distinct from `NMHC`

Non-Methane Hydrocarbon Equivalent appears on 13
records against 14,219 for NMHC. It is a different
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

50 records — 0.0527% of the panel,
across 18 families, all
nonroad — carry a **negative** certification result.
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

10 checks run on every build; all currently pass. They test
**internal consistency** and cannot establish that any value matches EPA's record.

**1. `family_key_unique` — PASS**

No (panel, model year, engine family) triple appears twice in the family table. The family key would otherwise be unusable for joining.

**2. `no_emission_row_without_family` — PASS**

Every emission record joins a family row. An orphan measurement would indicate the two tables were built from different row sets.

**3. `units_never_null` — PASS**

The units column is populated on every emission record, so no value can be read without its unit system attached.

**4. `no_mixed_units_within_panel` — PASS**

No panel carries more unit systems than it should — one for highway, two for nonroad, the second being smoke opacity.

**5. `highway_units_evidenced_by_standards` — PASS**

The modal certification standard per pollutant in the highway panel matches the known US heavy-duty standards expressed in g/bhp-hr. See §6.2.

**6. `highway_units_labelled` — PASS**

Every highway record carries the g/bhp-hr label.

**7. `nonroad_units_correct` — PASS**

Nonroad records carry only g/kW-hr or percent opacity, never a highway unit.

**8. `carryover_no_true_cycles` — PASS**

The lineage graph contains no cycle, so every traversal terminates and every family has a well-defined root.

**9. `every_negative_value_is_flagged` — PASS**

Every negative certification result carries a quality flag. An unflagged one would enter an unsuspecting user's aggregate.

**10. `flagged_share_below_0pt1pct` — PASS**

Flagged records remain under 0.1% of the panel. A sharp rise would indicate a parsing regression rather than a change in EPA's data.

### 6.2 The units evidence test

The highway source file states its units **nowhere**. Its column headers are bare —
`TR Cert Result`, `Transient Standard`. The claim that highway results are in g/bhp-hr was
originally an assertion written into the codebook by inference.

It is now a test. US heavy-duty highway standards have known values in g/bhp-hr, and the
modal certification standard per pollutant is compared against them:

| Pollutant | Known standard | Modal value in CIDEX |
|---|---|---|
| NOx | 0.2 | 0.2 |
| PM | 0.01 | 0.01 |
| NMHC | 0.14 | 0.14 |
| CO | 15.5 | 15.5 |

Expressed in g/kW-hr the same standards would be 0.268, 0.013, 0.188, 20.786 — an order of magnitude away
in every case. The test therefore cannot pass by coincidence, and it runs on every build.

The distinction matters beyond this one field. The inference was correct, but inference
was the wrong instrument: the same reasoning applied in a sibling project substituted a
European fuel specification for a US regulatory one and produced a materially wrong
result.

### 6.3 The author verification gate

No mechanical check can establish correspondence with the source. That requires a person
to look up specific records in EPA's own certificate tool and compare them by eye. The
pipeline ships five named spot-checks, each probing a different failure mode:

**Check 1 — highway, `MSZXH05.23FD`, MY2021**

CIDEX records NOx on the transient cycle as
**0.17 g/bhp-hr**. Highway, transient NOx — the standard case.

**Check 2 — highway, `FNGCH0466AEA`, MY2015**

CIDEX records PM on the steady state cycle as
**0.01 g/bhp-hr**. Highway, earliest model year present — tests the MY2015-16 archive boundary.

**Check 3 — nonroad, `LCEXL60.0AAB`, MY2020**

CIDEX records NOx on the steady state cycle as
**0.48 g/kW-hr**. Nonroad, steady-state NOx — tests the wide-to-long unpivot.

**Check 4 — nonroad, `TCPXL32.1NZS`, MY2026**

CIDEX records NMHC on the steady state cycle as
**0.08 g/kW-hr**. Deepest carryover lineage (depth 14, root CCPXL32.0NZS) — tests lineage resolution.

**Check 5 — nonroad, `CDICL05.8HTA`, MY2012**

CIDEX records NOx on the steady state cycle as
**-1.0 g/kW-hr**. A flagged negative value — is this real in EPA's own record?.

Publication is blocked until the author signs `docs/VERIFICATION_CHECKLIST.md`.
`scripts/09_release.py` refuses to build a deposit archive while the attestation file is
absent, and every document and figure regenerates stamped as unverified without it.

The attestation **pins which records were checked**. The spot-check selector chooses a
median row per category, so its output moves whenever the underlying row set changes — as
it did when the defect in §7.1 was corrected. Without pinning, a signature could come to
refer to records nobody had ever examined. `scripts/07_publish_gate.py` compares the
pinned list against the current build and blocks if they differ.

Status: Signed by Imafidon, Osariemen (ORCID 0009-0006-3069-4674) on 2026-09-15.

---

## 7. Defects found and corrected

Three defects were found during development. They are recorded because a validation
section reporting none says more about the thoroughness of the review than about the
correctness of the pipeline.

### 7.1 The FEL merge multiplied rows

**Severity: data corruption. Detected: adversarial review immediately before publication.**

Family Emission Limits were merged onto the emission records using the key
`(model_year, engine_family, pollutant)`. Because 1,487 families occupy more than one
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
emission records fell from 83,584 to 81,445.

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
with a visited set. True cycles: **0**.

**Generalisation:** the defect was found by looking at the output rather than the summary.
"109 cycles" is a number one can accept; the list of 109 pairs is not.

---

## 8. Results

### 8.1 What the panel contains

| Table | Rows |
|---|---|
| `cidex_family.csv` | 8,627 |
| `cidex_config.csv` | 9,794 |
| `cidex_emissions.csv` | 94,869 |
| `cidex_carryover.csv` | 7,925 |

108 manufacturers, 14 pollutants,
3 test types, units `g/bhp-hr`, `g/kW-hr`, `pct opacity`.

### 8.2 Pollutant coverage

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

### 8.3 Model-year coverage

Both panels are structurally incomplete at their edges for two unrelated reasons. EPA
holds older model years in separate archive files that CIDEX v1.0.0 does not ingest,
so the earliest year of each panel contains only whichever families happen to sit in the
current file. Separately, the newest model year is still being certified when the file is
downloaded.

A year is flagged when it holds under 50% of the median count of
that panel's interior years:

| Panel | Model year | Families | Share of median |
|---|---|---|---|
| highway | 2015 | 3 | 5% |
| highway | 2016 | 29 | 45% |
| nonroad | 2011 | 66 | 12% |
| nonroad | 2027 | 8 | 2% |

Usable ranges for trend analysis: highway
**MY2017–2026**, nonroad
**MY2012–2026**. Every
affected row carries `year_coverage`.

The 50% threshold is a judgement. It separates the observed cases
cleanly — no year sits near the boundary — but the raw counts are published so a reuser
with a different purpose can choose a different cut.

---

## 9. A family traced end to end

To make the schema concrete, here is `TCPXL18.1NYS` — a nonroad family chosen because it
exercises every structure this report describes.

**In the source.** It appears in the nonroad `Family Info` sheet with its measurements
spread across the wide pollutant block, its attributes split before and after that block,
and a `Carryover Engine Family Name` pointing at its predecessor.

**In `cidex_family.csv`.** One row, keyed
`(nonroad, 2026, TCPXL18.1NYS)`. Manufacturer
*Caterpillar Inc.*; power category `560<kW<=2237`; tier
*Tier 2*.

**In `cidex_emissions.csv`.** 33 records — the wide row unpivoted into one
row per pollutant and test type. Pollutants present:
`CO`, `CO2`, `NMHC`, `NMHC_NOx`, `NOx`, `PM`, `smoke_accel`, `smoke_lug`, `smoke_peak`. Test types: `smoke`, `steady_state`.
Every record carries `units = g/kW-hr` except smoke opacity, and `standard` is null for
all of them, per §5.3.

**In `cidex_carryover.csv`.** Lineage root
`CCPXL18.1NYS` at depth
**14** — the deepest chain in the panel, meaning this
family's certification can be traced back 14 model
years through successive carryovers.

A reader wanting to verify CIDEX end to end can take this family name, look it up in EPA's
interactive certificate tool, and compare every value above against the source.

---

## 10. Limitations and future work

`docs/LIMITATIONS.md` states the limitations in full. In summary: units are not comparable
across panels without deliberate conversion; 50 records carry
physically impossible negative values, published as EPA reports them; nonroad records have
no pollutant-specific standard; edge model years are incomplete; manufacturer names are
not normalised across years; and carryover lineage is nonroad-only with
568 open edges.

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

**`heavy-duty-gas-and-diesel-engines-2015-present.xlsx`**

- Source: <https://www.epa.gov/system/files/documents/2026-03/heavy-duty-gas-and-diesel-engines-2015-present.xlsx>
- Publisher: US EPA Office of Transportation and Air Quality
- Size: 22,908,765 bytes
- Recorded: 2026-09-15
- SHA-256:

```
3edfe15deef231828e26173f2a4dfe68ade0e96eb8dfe044b32cc4e63db640cf
```

**`nonroad-compression-ignition-2011-present.xlsx`**

- Source: <https://www.epa.gov/system/files/documents/2026-03/nonroad-compression-ignition-2011-present.xlsx>
- Publisher: US EPA Office of Transportation and Air Quality
- Size: 13,994,645 bytes
- Recorded: 2026-09-15
- SHA-256:

```
9e78cf00ca4f930899fed3d66101145f32dade525e8e68d5394b3df56cf5593c
```

## Appendix B — Source-to-output column mapping

### B.1 Highway family attributes

| Source column | CIDEX column |
|---|---|
| `Manufacturer` | `manufacturer` |
| `Model Year` | `model_year` |
| `Engine Family` | `engine_family` |
| `Certificate No.` | `certificate_no` |
| `Date Issued` | `date_issued` |
| `Engine Cycle` | `engine_cycle` |
| `Fuel Type` | `fuel_type` |
| `Fuel Metering System` | `fuel_metering_system` |
| `Introduction Date` | `introduction_date` |
| `Useful Life` | `useful_life` |
| `Intended Service Class` | `intended_service_class` |

### B.2 Highway measurement blocks

| Source column | CIDEX column | Test type |
|---|---|---|
| `TR Cert Result` | `cert_result` | transient |
| `Transient (TR) Comb Adj Result` | `adj_result` | transient |
| `Transient Standard` | `standard` | transient |
| `Transient FEL` | `fel` | transient |
| `Transient FCL` | `fcl` | transient |
| `SS Cert Result` | `cert_result` | steady state |
| `Steady State (SS) Adj Result` | `adj_result` | steady state |
| `SS Standard` | `standard` | steady state |
| `SS FEL` | `fel` | steady state |
| `SS FCL` | `fcl` | steady state |

### B.3 Nonroad attributes

| Source column | CIDEX column |
|---|---|
| `Model Year` | `model_year` |
| `Engine Family` | `engine_family` |
| `Manufacturer` | `manufacturer` |
| `Certificate #` | `certificate_no` |
| `Issue Date` | `date_issued` |
| `Commerce Introduction Date` | `introduction_date` |
| `Carryover Engine Family Name` | `carryover_family` |
| `Power Category` | `power_category` |
| `Applicatable Regulation` | `regulation` |
| `Applicable Tier` | `tier` |
| `Applicable Compliance Standard` | `compliance_standard` |
| `Fuel` | `fuel_type` |
| `Fuel Meter System` | `fuel_metering_system` |
| `Useful Life of Engine Family` | `useful_life` |
| `Engine Combustion Cycle` | `engine_cycle` |
| `Non Aftertreatment Device Type` | `non_aftertreatment_device` |
| `Aftertreatment Device Type` | `aftertreatment_device` |
| `Engine Model` | `engine_model` |
| `Engine Code` | `engine_code` |
| `Displacement` | `displacement_l` |
| `Certification Fuel` | `certification_fuel` |
| `Engine Operation` | `engine_operation` |
| `Test Procedure` | `test_procedure` |
| `Test Type` | `test_procedure_type` |

## Appendix C — Pollutant vocabulary

Highway source values map as below. Nonroad sub-headers map through a parallel table in
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

*Generated by `scripts/11_report.py` on 2026-09-15.*
