% A harmonized panel of United States compression-ignition engine certification data, with resolved certification lineage
% Osariemen Imafidon
% 2026-09-15

Independent Researcher. ORCID [0009-0006-3069-4674](https://orcid.org/0009-0006-3069-4674).
Correspondence: odimafid@gmail.com.

**Preprint.** Not peer reviewed. Part of the
[FACET](https://osariemenimafidon.github.io/facet/) research program.

---

## Abstract

The United States Environmental Protection Agency (EPA) publishes emission certification
records for compression-ignition engines, but distributes them as two spreadsheets whose
internal structures are mutually incompatible and whose true column headers are not on the
first row. The result is a public record that is open in principle and costly to use in
practice: every researcher must independently reverse-engineer two layouts, and the
characteristic failure is not an error message but a quietly wrong number.

We present CIDEX, a harmonized engine-family-level panel reconciling both sources into a
single schema: **8,627 engine families**, **9,794
engine configurations** and **94,869 emission records** from
**108 manufacturers**, spanning model years
2011–2027, 14 pollutants and
3 test types.

Beyond reorganisation, we resolve a structure present in the source but not previously
published in usable form: **5,982 nonroad families declare a
predecessor family**, and these declarations chain. Resolving them yields
**2,541 distinct certification lineages** with a maximum depth of
**14 model years** and a mean of 1.382, allowing a family's
regulatory history to be followed across more than a decade. We show the lineage graph is a
forest, and that 30 families use an undocumented
self-reference convention that a naive traversal misreads as cycles.

We further identify 50 records carrying physically impossible
negative certification results, and 4
model years whose apparent decline is an artefact of EPA's archive boundaries rather than a
change in the fleet. Both are published as flagged data rather than silently corrected or
removed, because a cleaned column conceals a finding and a removed row conceals a defect.

CIDEX preserves certification units as issued and performs no silent conversion: highway
results are in g/bhp-hr and nonroad results in g/kW-hr, and we argue that normalising them
would convert a visible incompatibility into an invisible one. The paper documents the
harmonization decisions, the automated and manual validation, and one defect found during
development in which a merge on a non-unique key silently multiplied rows — included
because it is the exact class of error this dataset exists to prevent, and because
recording how it was caught is more useful to a reader than asserting that the result is
correct.

**Keywords:** engine certification; compression-ignition engines; nonroad engines;
emissions; data harmonization; certification lineage; open government data

---


## 1 Background and summary

### 1.1 The record and its unit

No compression-ignition engine may be sold in the United States without a certificate of
conformity. The unit of certification is the **engine family** — a group of engines
expected to share emission characteristics — rather than an individual engine model. A
family is tested at one or more configurations, results are compared against the standard
applicable to its service class and model year, and a certificate is issued.

The accumulated record is the only comprehensive public account of what engines were
approved to emit, by whom, and under which standard. It bears directly on fleet
composition, technology adoption, the realised stringency of successive standards, and the
gap between certified and in-service behaviour. It is also, for a large part of the
economy, the only fine-grained public description of the equipment itself: displacement,
power rating, aftertreatment configuration and test procedure, family by family.

Two properties of the unit shape everything downstream. First, the family is a regulatory
construct rather than a physical one, so counts of families are counts of certificates and
not of engines or of sales. Second, EPA encodes the model year in the first character of
the family name, which makes the name unique within the published window and therefore
usable as a key without inventing a surrogate. Both properties are exploited in the schema
and are stated here so a reader knows what a row of CIDEX is.

### 1.2 Open in principle, costly in practice

EPA publishes this record openly, without authentication, refreshed quarterly. The
difficulty is structural, and it has three parts.

First, **both workbooks place their column headers on the second row**, reserving the first
for a merged group header. The default behaviour of standard spreadsheet readers is to
treat row one as the header, which yields a frame whose columns are named `Unnamed: 0`
onward and whose first data row contains the real headers. No exception is raised. A user
who does not inspect the frame visually proceeds with a dataset that is off by one row and
has lost its column names.

Second, **the two files are organised in opposite directions**. The highway file is long on
pollutant and wide on test type: one row per family and pollutant, with separate columns
for each test type's result. The nonroad file is wide on pollutant beneath a two-level
header, with family attributes distributed on *both* sides of the measurement block. The
two require different, and in places opposite, reshaping operations.

Third, **the two encode pollutants and units differently**. The same pollutant appears
under different spellings; one panel's results are in grams per brake horsepower-hour and
the other's in grams per kilowatt-hour; opacity is a percentage and not a rate at all. Any
cross-cutting question requires a reconciliation that the publisher does not provide and
that no user has an obligation to perform correctly.

### 1.3 Why the failure mode matters

The consequence is that this work is duplicated by every user, documented by none, and its
errors are invisible.

That last property is the argument for this dataset. A malformed file that refuses to open
costs an afternoon. A malformed file that opens cleanly and yields a frame with plausible
column names, plausible row counts and wrong contents costs a published result. Every
defect described in Section 1.2 has the second shape: a header-row error produces a valid
frame, a wide-to-long reshape on a non-unique key produces a larger and still plausible
table, and mixing two unit systems in one column produces numbers that differ by a factor of
1.34 rather than by an order of magnitude, which is well inside the range a
reader would accept as a real effect.

Section 2.6 documents an instance of exactly this, found during development of CIDEX
itself. We include it rather than quietly fixing it because a methods section that claims
care is weaker evidence than one that shows what care caught.

### 1.4 Contributions

1. A harmonized, analysis-ready panel covering both engine categories under one schema,
   with a machine-readable codebook and Parquet mirrors.
2. A resolved **certification lineage**, linking families across model years — present
   in the source as unresolved references, not previously published in usable form —
   together with its depth distribution and an account of the three traversal cases the
   source requires.
3. A characterisation of two defects in the published record: physically impossible values,
   and structural discontinuities at archive boundaries that masquerade as trends. Both are
   flagged in the data rather than described only in prose.
4. A reproducible pipeline with hash-level provenance and a verification procedure that
   blocks publication until an author has checked the output against the source by hand,
   with the checked records pinned by name in the attestation.
5. A worked account of one harmonization defect found and fixed during development,
   offered as a methods contribution rather than an apology.

### 1.5 What CIDEX is not

It is not a new measurement. Every value in it appears in EPA's published files; the
contribution is reorganisation, resolution and validation, not observation.

It is not a complete history. EPA holds older model years in separate archive files that
this version does not ingest, so the panel's early years are bounded by what the current
file happens to contain rather than by when certification began. Section 5.2 quantifies the
boundary and flags every affected row.

It is not a record of in-service emissions. Certification results are laboratory values
obtained on a certification fuel and a specified duty cycle. The relationship between them
and what an engine emits in service is an open question, and one that a companion project
in the same research program takes up from the fuel-specification side; CIDEX supplies the
population that question is asked about, and answers none of it by itself.

---


## 2 Methods

### 2.1 Design principles

Four rules govern every decision in the pipeline, and stating them first makes the
individual choices predictable rather than arbitrary.

**Preserve the source.** CIDEX reorganises; it does not correct. Where the published record
contains something implausible, the value is retained and flagged. A reader who wants it
removed can filter; a reader given a cleaned table cannot recover what was cleaned.

**Assert nothing that can be tested.** Wherever the pipeline would otherwise rely on domain
knowledge — that a column is in particular units, that a key is unique, that a reshape
preserved the row count — the belief is written as a check that runs on every build.
Section 4.2 gives the clearest case: a units claim that began as an inference and became a
test.

**Fail loudly.** An unmapped pollutant raises rather than being dropped. An attribute that
varies within a family raises rather than being resolved by taking the first row. A merge
that changes the row count raises rather than proceeding. Silence is the failure mode this
dataset exists to remove, so the pipeline is written to be noisy.

**Make judgements visible.** Every decision that could reasonably have gone the other way
— keeping units divergent, retaining NMHCE as distinct from NMHC, treating a
self-reference as a terminus — is documented with its reasoning, so a user who
disagrees can find the decision rather than discovering it.

### 2.2 Sources and provenance

Two EPA workbooks, both US Government works without copyright restriction: heavy-duty
highway gasoline and diesel engines (model years
2015–2026,
7,804 source rows) and nonroad compression-ignition engines
(2011–2027,
10,214 rows).

EPA replaces these files in place each quarter with no changelog and no versioned archive.
A dataset built from them is therefore identified by the bytes it was built from, not by the
URL. We record the SHA-256 digest of every source file at fetch time along with the
retrieval timestamp and byte count; the deposited version carries fixed digests that a
rebuilder can verify. If EPA revises a file, a rebuild produces a different digest and the
difference surfaces immediately rather than being absorbed into the results.

This is a stronger requirement than it may appear. Without it, "the EPA certification data"
names a moving target, two papers citing the same URL can rest on different numbers, and
neither can tell. The digest makes the dataset a fixed object that a disagreement can be
resolved against.

### 2.3 Schema and the family key

The target is a single long form keyed on **(panel, model year, engine family, pollutant,
test type)**, with three supporting tables.

We establish that the engine family name is a **true key** rather than assuming it. In both
panels the count of distinct family names equals exactly the count of distinct (model year,
family) pairs — 702 and 7,925
respectively — because EPA encodes the model year in the name's first character. No
surrogate key is introduced, so every row remains traceable to EPA's own record by a value a
reader can look up in EPA's public certificate tool. The equality is re-checked on every
build, because it is a property of EPA's naming convention and not a guarantee.

We separate **family-level** from **configuration-level** attributes, and the need for the
separation is measured rather than assumed. In the nonroad source, 1,487 of
7,925 families occupy more than one row — up to 34 rows
for a single family — differing by engine code, model, displacement, fuel or test
procedure. Retaining these at family level would require an arbitrary row to win.

Table 1 gives the number of families for which each attribute takes more than one value in
the source, before the split. These are the columns that would have been silently collapsed
by a naive de-duplication.

Table 1. Nonroad attributes conflicting within a family, before the family/configuration
split.

| Attribute | Families with conflicting values |
|:--------------------------|---------------------------------:|
| `engine_code` | 609 |
| `test_procedure` | 428 |
| `engine_operation` | 422 |
| `engine_model` | 278 |
| `displacement_l` | 88 |
| `test_procedure_type` | 80 |
| `certification_fuel` | 35 |

After the split, the family table's attribute conflicts number
0, and the highway table's number
0. The separation is enforced by assertion: the build fails
if any attribute remaining in the family table varies within a family.

### 2.4 Harmonization: the highway panel

The file is read with the header on row two. The pollutant name maps through a controlled
vocabulary of 10 terms; an unmapped value raises rather than being
dropped, since a silently discarded pollutant is the precise failure this work exists to
prevent. Appendix B lists the vocabulary in full.

The test-type block is unpivoted from 15,608 intermediate rows,
yielding one record per family, pollutant and test type. 2,184
rows carry no value in any measurement column and are removed as artefacts of the unpivot
rather than facts about an engine; the count is reported rather than absorbed, because a
dropped-row count that nobody reports is a dropped-row count that nobody can check. The
panel resolves to 702 family rows, 875 configuration
rows and 13,424 emission records.

### 2.5 Harmonization: the nonroad panel

The two-level header is resolved without positional assumptions, which would break on any
column insertion. The group row is forward-filled, then a column is classified as a
measurement **only if its sub-name is one its group actually contains**. This test is
load-bearing: the attribute columns trailing the measurement block inherit a forward-filled
group label and would otherwise be misclassified as pollutants. The classifier identifies
22 measurement and 24 attribute columns, and
reports 0 unmapped attribute columns.

The wide measurement block unpivots to 224,708 intermediate rows, of
which 141,657 are empty cells in the wide layout rather than
observations; the wide form is sparse because most families are not tested for most
pollutants. 81,445 emission records remain.

The panel also carries 1,606 Family Emission Limit values, which are
declared limits rather than test results and must be attached to the corresponding
measurement rather than treated as one. Section 2.6 describes what went wrong when they
were.

### 2.6 A defect found during development: the FEL merge

We report this in full because it is the class of error CIDEX exists to prevent, and
because the way it was found is more informative than the fix.

FEL values arrive in the nonroad source as rows of the same shape as test results. The
first implementation attached them to their measurements by merging on
`(model_year, engine_family, pollutant)`. That key is not unique. As Section 2.3 records,
1,487 families occupy more than one source row, up to 34, so a family with
several source rows matched every FEL row against every measurement row, and the merge
multiplied.

Nothing raised. The merge succeeded, the resulting table had valid types and plausible
values, and every individual number in it was a number EPA had published. Only the count was
wrong — inflated by roughly two thousand rows against an arithmetic expectation derived
independently from the source row counts.

It was found by computing what the row count should be before looking at what it was. That
is now a permanent control: the merge is performed on the **source row identifier** rather
than the family, and the row count before and after is compared, with a failure raising and
naming both numbers. The QA report records the check as
`fel_merge_row_count_stable = true`.

Three lessons are worth stating explicitly, because they generalise beyond this dataset.
A merge is a join and a join on a non-unique key is a multiplication, which is obvious in
the abstract and easy to miss in a pipeline of twenty steps. A transformation's row count is
a testable prediction and should be predicted before it is observed. And a check that
compares an output to an independently derived expectation catches a whole class of defects
that no amount of type checking or null checking will reach.

### 2.7 Lineage resolution

5,982 nonroad families name a predecessor family. Resolution is
a traversal to each family's root, with three cases handled explicitly.

**Self-reference.** 30 families name themselves. EPA appears
to use this to denote an unchanged re-certification; the convention is undocumented. A naive
traversal treats it as a cycle, and our first implementation reported a large number of
spurious cycles for this reason. We treat `parent(x) = x` as a terminus.

**Orphans.** 568 families name a predecessor absent from the published
window, almost all pre-2011 families held in EPA's archive file.
5,414 edges resolve within the window. Truncated lineages are not
erroneous, but they carry a consequence a user must know: **a recorded depth of zero does
not always denote the first of its line**. Both counts are published so a user can decide
whether to exclude truncated lineages from a depth analysis.

**Cycles.** Detected with a visited set. Count: 0. The graph is a
forest.

The result is 2,541 distinct lineages over
7,925 nonroad families, with mean depth 1.382 and maximum
depth 14. The deepest example is family
`TCPXL18.1NYS` (MY2026),
rooted at `CCPXL18.1NYS`. Appendix D gives the full depth
distribution; 5,384 families sit at depth one or greater.

### 2.8 Units

Highway results are certified in g/bhp-hr, nonroad in g/kW-hr, nonroad smoke opacity in
percent opacity. **No conversion is performed.** Each record carries its unit system
explicitly, and 3 unit labels appear in the panel.

We regard this as a substantive design decision rather than an omission. Normalising to a
single system would produce a tidier table in which a user aggregating across panels obtains
a plausible and wrong result with nothing to signal the error. The conversion factor is
0.7457, so a mixed aggregation is wrong by a third — large enough to matter and
small enough to look like a finding. Leaving the units divergent makes the incompatibility
visible at the point of use.

A conversion helper is provided and must be called deliberately. The margin helper, which
computes headroom against a standard, raises rather than computing across unit systems: the
one operation where a mixed comparison would be most tempting is the one operation that
refuses.

### 2.9 Quality flags

Two flag columns travel with the data rather than with the documentation.

`quality_flag` marks records whose values are physically impossible — in this version,
negative certification results. `year_coverage` marks each row's model year as complete,
partially archived or partially forward, so a time series can be filtered without the user
having to know where the archive boundaries fall.

The principle in both cases is that a hazard described only in a limitations section is a
hazard that will be encountered by users who did not read it. A flag column is read by the
code.

---


## 3 Data records

### 3.1 Files

Table 2. Published tables.

| Table | Rows | Columns | Contents |
|:-------------------------|-------:|--------:|:-----------------------------------------|
| `cidex_family.csv` | 8,627 | 20 | One row per (panel, model year, family) |
| `cidex_config.csv` | 9,794 | 14 | Configurations within a family |
| `cidex_emissions.csv` | 94,869 | 17 | One row per family, pollutant, test type |
| `cidex_carryover.csv` | 7,925 | 6 | Resolved lineage: parent, root, depth |

Parquet mirrors accompany each table. A machine-readable codebook documents every column;
Appendix A lists the schema as published.

The panel covers 108 manufacturers
(27 highway, 86 nonroad),
14 pollutants and 3 test types
(smoke, steady state, transient).

### 3.2 Pollutant coverage

Coverage is strongly uneven, and the unevenness is a property of the certification
programme rather than of this dataset. Criteria pollutants are measured for nearly every
family; greenhouse gases and air toxics are measured for a subset determined by service
class and model year.

Table 3. Emission records by pollutant.

| Pollutant | Records | Share of panel |
|:-------------|-----------:|---------------:|
| `CO` | 14,238 | 15.0% |
| `NOx` | 14,238 | 15.0% |
| `NMHC` | 14,219 | 15.0% |
| `PM` | 14,190 | 15.0% |
| `CO2` | 13,196 | 13.9% |
| `CH4` | 7,456 | 7.9% |
| `NMHC_NOx` | 6,712 | 7.1% |
| `N2O` | 4,700 | 5.0% |
| `smoke_accel` | 1,853 | 2.0% |
| `smoke_peak` | 1,785 | 1.9% |
| `smoke_lug` | 1,763 | 1.9% |
| `HCHO` | 503 | 0.5% |
| `NMHCE` | 13 | 0.0% |
| `NH3` | 3 | 0.0% |

`NMHCE` (Non-Methane Hydrocarbon Equivalent,
13 records) is retained as distinct from
`NMHC` (14,219 records) because it is a different
regulatory construct, not a different spelling. Folding it in would destroy information a
user cannot reconstruct; keeping it separate costs a filter expression. `NH3`
(3 records) and `HCHO`
(503 records) are retained on the same
principle despite being rare: a pollutant with three records is still a pollutant, and a
user studying ammonia slip would rather have three rows than none.

### 3.3 Model year coverage

Table 4 gives family counts by panel and model year with the coverage classification each
row carries. Years marked other than complete are discussed in Section 5.2; they are
retained, not removed, and flagged so that a filter can exclude them.

Table 4. Families by panel and model year.

| Panel | Model year | Families | Share of interior median | Coverage |
|:--------|-----------:|---------:|-------------------------:|:-----------------|
| highway | 2015 | 3 | 5% | partial archive |
| highway | 2016 | 29 | 45% | partial archive |
| highway | 2017 | 75 | 117% | complete |
| highway | 2018 | 61 | 95% | complete |
| highway | 2019 | 61 | 95% | complete |
| highway | 2020 | 56 | 88% | complete |
| highway | 2021 | 64 | 100% | complete |
| highway | 2022 | 72 | 112% | complete |
| highway | 2023 | 64 | 100% | complete |
| highway | 2024 | 76 | 119% | complete |
| highway | 2025 | 75 | 117% | complete |
| highway | 2026 | 66 | 103% | complete |
| nonroad | 2011 | 66 | 12% | partial archive |
| nonroad | 2012 | 521 | 98% | complete |
| nonroad | 2013 | 401 | 75% | complete |
| nonroad | 2014 | 430 | 80% | complete |
| nonroad | 2015 | 454 | 85% | complete |
| nonroad | 2016 | 485 | 91% | complete |
| nonroad | 2017 | 489 | 92% | complete |
| nonroad | 2018 | 496 | 93% | complete |
| nonroad | 2019 | 534 | 100% | complete |
| nonroad | 2020 | 569 | 107% | complete |
| nonroad | 2021 | 583 | 109% | complete |
| nonroad | 2022 | 597 | 112% | complete |
| nonroad | 2023 | 607 | 114% | complete |
| nonroad | 2024 | 597 | 112% | complete |
| nonroad | 2025 | 558 | 104% | complete |
| nonroad | 2026 | 530 | 99% | complete |
| nonroad | 2027 | 8 | 2% | partial forward |

Usable ranges, defined as the contiguous span of years at or above
50% of the panel's interior median, are
highway MY2017–2026 and
nonroad MY2012–2026.

### 3.4 Nonroad standard tiers

Table 5. Nonroad families by emission standard tier.

| Tier | Families | Share of nonroad panel |
|:----------------------------|---------:|-----------------------:|
| Tier 4 (Final or Phase In) | 5,626 | 71.0% |
| Tier 3 | 983 | 12.4% |
| Interim Tier 4 | 828 | 10.4% |
| Tier 2 | 488 | 6.2% |

The distribution is a snapshot of the currently published window rather than a history of
adoption: the window is bounded below by the archive boundary described in Section 5.2, so
earlier tiers are under-represented by construction and the table should not be read as a
technology transition curve.

---

## 4 Technical validation

### 4.1 Automated checks

Ten checks execute on every build. All pass.

Table 6. Integrity checks.

| Check | Result |
|:-------------------------------------------|:-------|
| `family_key_unique` | pass |
| `no_emission_row_without_family` | pass |
| `units_never_null` | pass |
| `no_mixed_units_within_panel` | pass |
| `highway_units_evidenced_by_standards` | pass |
| `highway_units_labelled` | pass |
| `nonroad_units_correct` | pass |
| `carryover_no_true_cycles` | pass |
| `every_negative_value_is_flagged` | pass |
| `flagged_share_below_0pt1pct` | pass |

These establish **internal consistency**: that the key is unique, that no emission record
refers to a family that does not exist, that units are labelled and consistent within a
panel, that the lineage graph is acyclic, and that every anomalous value is flagged. They
cannot establish correspondence with EPA's record, which is what Section 4.3 is for.

Two of the checks deserve comment because they encode decisions rather than truisms.
`every_negative_value_is_flagged` asserts that the pipeline has not silently dropped the
anomalies it found. `flagged_share_below_0pt1pct` is a tripwire: it does not assert that the
flagged share is correct, but it fails if the share ever jumps, which would indicate that a
change to the pipeline had begun flagging a class of values it previously accepted.

### 4.2 Units established by evidence, not assertion

The highway source states its units nowhere; its headers are bare. That highway results are
in g/bhp-hr was initially an inference from domain knowledge, which is to say an assumption
with a good pedigree and no test behind it.

We replaced it with a test. United States heavy-duty highway standards have known values in
g/bhp-hr, and the modal certification standard per pollutant in the panel is compared
against them.

Table 7. Units evidence: known heavy-duty highway standards against the modal value in
CIDEX.

| Pollutant | Known standard (g/bhp-hr) | Modal value in CIDEX | Same standard in g/kW-hr |
|:----------|--------------------------:|---------------------:|-------------------------:|
| NOx | 0.2 | 0.2 | 0.268 |
| PM | 0.01 | 0.01 | 0.013 |
| NMHC | 0.14 | 0.14 | 0.188 |
| CO | 15.5 | 15.5 | 20.786 |

The final column is why the test cannot pass by coincidence: expressed in the other unit
system the same standards are an order of magnitude distant in every case, so a panel
mislabelled as g/bhp-hr would fail the comparison rather than pass it weakly. The check runs
on every build, so a future source change that altered the unit basis would break the build
rather than quietly change the meaning of a column.

### 4.3 Manual verification

No automated check can establish correspondence with the source. A pipeline can verify that
it did what it was told; only a person can verify that what it was told was right.

The pipeline ships five named spot-checks, each probing a distinct
failure mode, which an author looks up in EPA's public certificate tool and compares by
hand.

Table 8. Pinned spot-checks.

| Family | MY | Panel | Pollutant | Test | CIDEX value | Failure mode probed |
|:--------------------|-----:|:--------|:----------|:-------------|:-------------|:-------------------|
| MSZXH05.23FD | 2021 | highway | NOx | transient | 0.17 g/bhp-hr | highway, transient NOx — the standard case |
| FNGCH0466AEA | 2015 | highway | PM | steady state | 0.01 g/bhp-hr | highway, earliest model year present — tests the MY2015-16 archive boundary |
| LCEXL60.0AAB | 2020 | nonroad | NOx | steady state | 0.48 g/kW-hr | nonroad, steady-state NOx — tests the wide-to-long unpivot |
| TCPXL32.1NZS | 2026 | nonroad | NMHC | steady state | 0.08 g/kW-hr | deepest carryover lineage (depth 14, root CCPXL32.0NZS) — tests lineage resolution |
| CDICL05.8HTA | 2012 | nonroad | NOx | steady state | -1.0 g/kW-hr | a flagged negative value — is this real in EPA's own record? |

Publication is blocked until this is signed. The attestation **pins which records were
checked**, by family name, because the selector originally chose a median row and its output
moves when the row set changes; without pinning, a signature given against one set of
records could come to refer to records nobody had examined. The gate compares the pinned
names against the current selection and fails on drift.

### 4.4 What the validation does not establish

It does not establish that EPA's published values are correct. CIDEX inherits whatever is in
the source, and Section 5.1 documents values that are certainly wrong in the source and are
preserved anyway.

It does not establish that the five checked records generalise. They
were chosen to span distinct failure modes rather than to be a random sample, which is the
right design for catching structural errors and the wrong design for estimating an error
rate. We make no error-rate claim.

It does not establish completeness against EPA's full certification history, for the archive
reason in Section 1.5.

---


## 5 Anomalies in the published record

### 5.1 Physically impossible values

50 records (0.0527% of the panel,
18 families, all
nonroad) carry a **negative** certification result. An
emission rate cannot be negative.

We publish them unaltered, flagged. Correcting them would break the claim that CIDEX
faithfully reorganises a published record, and would conceal a finding: either the source
contains data-entry errors worth raising with EPA, or an encoding convention exists — a
sentinel for "not applicable", perhaps — that neither party has documented. Both
possibilities are more useful to a reader than a quietly cleaned column, and a reader who
wants them gone has one filter expression to write.

The share is small enough that it would not disturb an aggregate and large enough that it
would disturb a minimum. That asymmetry is the argument for flagging rather than
documenting: a user computing a minimum or a lower percentile needs to know, and a user
computing a mean does not, and neither can be relied upon to have read a limitations
section.

One flagged record is included among the pinned spot-checks in Table 8, so the verification
procedure confirms that the negative value is present in EPA's own record rather than
introduced by the pipeline.

### 5.2 Archive boundaries that resemble trends

Both panels thin sharply at their edges, for two unrelated reasons. EPA holds older model
years in **separate archive files**, so the earliest year of each panel contains only
whichever families happen to sit in the current file. Separately, the newest model year is
still being certified when the file is retrieved, so its count is partial for a reason that
has nothing to do with the fleet.

Table 9. Model years with incomplete coverage.

| Panel | Model year | Families | Share of interior median | Coverage |
|:--------|-----------:|---------:|-------------------------:|:-----------------|
| highway | 2015 | 3 | 5% | partial archive |
| highway | 2016 | 29 | 45% | partial archive |
| nonroad | 2011 | 66 | 12% | partial archive |
| nonroad | 2027 | 8 | 2% | partial forward |

A time series spanning these years reads a filing artefact as a collapse or a boom. The
highway panel's MY2015 count is
5% of the
interior median; a chart drawn without the flag would show a catastrophic fall in heavy-duty
certification followed by an equally implausible recovery, and nothing in the data would
contradict it.

We flag every affected row rather than documenting the hazard in prose alone, and report
usable ranges: highway MY2017–2026,
nonroad MY2012–2026.

### 5.3 Depth zero is ambiguous

The 568 orphan edges of Section 2.7 produce a subtler hazard. A family
whose declared predecessor lies outside the published window resolves to itself as root and
records depth zero, which is indistinguishable in the table from a family that genuinely
begins its line.

2,541 families sit at depth zero. Some are first-of-line;
some are truncated. The carryover table carries the orphan status so the two can be separated, and a
depth analysis that does not separate them will understate lineage length by an amount that
grows with how much of the history sits in the archive.

### 5.4 An undocumented convention

The 30 self-referencing families of Section 2.7 are worth
recording as a finding in their own right. A family naming itself as its own predecessor is
not a data error: it appears to be a deliberate encoding for an unchanged re-certification.
But it is documented nowhere, and the natural implementation of a lineage traversal treats
it as a cycle and either loops forever or reports a corrupt graph.

We report it because the next person to resolve this structure will otherwise rediscover it
by debugging, and because it is a small example of a general point about open government
data: publication of the bytes is not publication of the semantics, and the gap between them
is where reuse costs accumulate.

---

## 6 Usage notes

### 6.1 Three cautions

**Do not compare across panels without converting units.** Filter on `panel`, or convert
deliberately using the provided helper. The conversion factor is 0.7457; an
unconverted cross-panel aggregate is wrong by about a third.

**Exclude incomplete years from time series.** Filter `year_coverage == "complete"`, or
restrict to the usable ranges given in Section 3.3.

**Decide about flagged values explicitly.** Filter on `quality_flag` if physically plausible
values are required. Do not assume the default is what you want; the default is the source.

### 6.2 What the panel supports

The harmonized panel supports the questions the source makes expensive: the distribution of
certification results within and across manufacturers, the relationship between certified
result and applicable standard, the composition of the certified population by tier and
displacement, and cross-panel comparisons where the unit discipline is observed.

The lineage table supports questions the panel alone cannot answer. How long does a
certification family persist? How do technology changes propagate through successive
re-certifications? Does lineage depth differ systematically across power categories, tiers or
manufacturers? Is a deep lineage associated with a certification result that changes slowly?
These are questions about the regulatory process rather than about engines, and the resolved
lineage is what makes them askable from public data.

Because the family name is EPA's own and no surrogate key is introduced, any row can be
taken back to EPA's certificate tool and checked. A result computed from CIDEX is falsifiable
against the source by a reader who has never run the pipeline.

### 6.3 Limitations

EPA's archive files are not ingested in this version, which bounds the panel's history and
produces the depth-zero ambiguity of Section 5.3.

Manufacturer names are not normalised across years. The same corporate entity may appear
under more than one spelling, so a manufacturer-level aggregate requires the user to decide
on a normalisation. We do not impose one, because the right normalisation depends on whether
the question is about corporate groups, legal entities or brands, and that is the user's
question to answer.

Nonroad records carry no pollutant-specific standard, because the source states the standard
only at family level. Inferring a per-pollutant standard from the family-level value would be
a guess presented as data.

Certification results are laboratory values on a certification fuel and a specified duty
cycle. They are not in-service emissions, and the difference is not a small correction.

The panel is a snapshot of a file EPA replaces quarterly. It is identified by digest and
should be cited by version.

---

## 7 Reuse and extension

Three extensions are straightforward and would each add substantially to the panel's value.

**Ingest the archive files.** This would extend both panels backward, close the depth-zero
ambiguity for most lineages, and turn the tier distribution in Table 5 into something that
could legitimately be read as an adoption curve.

**Normalise manufacturer identity.** A curated crosswalk, published separately so that users
can disagree with it, would make manufacturer-level analysis possible without each user
building their own.

**Link to other public records.** The engine family is a key that appears in other federal
datasets. Joining on it would connect certification to recall, in-use testing and
enforcement records, and the join is cheap precisely because CIDEX keeps EPA's own key rather
than inventing one.

We publish the pipeline under a permissive licence to make these extensions possible without
permission or coordination.

---

## Data availability

The dataset is deposited on Zenodo under the concept DOI 10.5281/zenodo.22761791, which always resolves to the newest version; the version described here is 10.5281/zenodo.22833302. The dataset is released under CC BY 4.0. All processed tables are in the
repository under `data/processed/`, with Parquet mirrors and a machine-readable codebook. The
source files are US Government works published by EPA and are identified in the provenance
log by URL, retrieval date, byte count and SHA-256 digest.

## Code availability

The complete pipeline is at <https://github.com/osariemenimafidon/cidex> under the MIT
licence, with a technical report, codebook, verification checklist and provenance log. A
single command rebuilds every published figure from the source files and diffs the result
against the deposited values.

## Competing interests

The author declares no competing interests.

## Funding

This work received no external funding.

## Use of AI assistance

Pipeline code, table generation and manuscript drafting were produced with AI assistance.
The harmonization decisions, the verification spot-checks against EPA's certificate tool and
the interpretation of the record's structure were made and checked by the author, who is
responsible for the content.

## References

1. US Environmental Protection Agency. *Annual Certification Data for Vehicles, Engines, and
   Equipment.*
   <https://www.epa.gov/compliance-and-fuel-economy-data/annual-certification-data-vehicles-engines-and-equipment>
2. US Environmental Protection Agency. *Control of Air Pollution from New Motor Vehicles and
   New Motor Vehicle Engines.* 40 CFR Part 86.
3. US Environmental Protection Agency. *Control of Emissions from New and In-Use Nonroad
   Compression-Ignition Engines.* 40 CFR Part 1039.
4. US Environmental Protection Agency. *Engine Testing Procedures.* 40 CFR Part 1065.
5. US Environmental Protection Agency. *Regulation of Fuels and Fuel Additives.* 40 CFR
   Part 1090.
6. Imafidon, O. *What the fuel regulation guarantees an engine designer: a specification
   divergence register for United States compression-ignition certification.* FACET research
   program.

---

## Appendix A: published schema

Column names as they appear in the published files.

**`cidex_family.csv`** (20 columns)

`panel`, `manufacturer`, `model_year`, `engine_family`, `certificate_no`, `date_issued`, `engine_cycle`, `fuel_type`, `fuel_metering_system`, `introduction_date`, `useful_life`, `intended_service_class`, `carryover_family`, `power_category`, `regulation`, `tier`, `compliance_standard`, `non_aftertreatment_device`, `aftertreatment_device`, `year_coverage`

**`cidex_config.csv`** (14 columns)

`panel`, `model_year`, `engine_family`, `engine_code`, `engine_test_model`, `engine_id`, `test_fuel`, `test_date`, `engine_model`, `displacement_l`, `certification_fuel`, `engine_operation`, `test_procedure`, `test_procedure_type`

**`cidex_emissions.csv`** (17 columns)

`panel`, `model_year`, `engine_family`, `engine_code`, `engine_test_model`, `pollutant`, `test_type`, `cert_result`, `adj_result`, `standard`, `fel`, `fcl`, `df_type`, `df_value`, `units`, `quality_flag`, `year_coverage`

**`cidex_carryover.csv`** (6 columns)

`panel`, `model_year`, `engine_family`, `carryover_family`, `lineage_root`, `lineage_depth`

---

## Appendix B: pollutant vocabulary

Source spellings and their canonical forms. An unmapped source value raises rather than
being dropped.

`Ammonia` → `NH3`, `Carbon Dioxide` → `CO2`, `Carbon Monoxide` → `CO`, `Formaldehyde` → `HCHO`, `Methane` → `CH4`, `Nitrogen Oxides` → `NOx`, `Nitrous Oxide` → `N2O`, `Non-Methane Hydrocarbon Equivalent` → `NMHCE`, `Non-Methane Hydrocarbons` → `NMHC`, `Particulate Matter` → `PM`

---

## Appendix C: test types and units

Test types: `smoke`, `steady_state`, `transient`.

Unit labels present: `g/bhp-hr`, `g/kW-hr`, `pct opacity`.

Conversion factor between the two rate systems: 0.7456998716 kW per bhp. The pipeline's
margin helper raises rather than computing a headroom across unit systems.

---

## Appendix D: lineage depth distribution

| Depth | Families | Share of nonroad panel |
|------:|---------:|-----------------------:|
| 0 | 2,541 | 32.1% |
| 1 | 3,719 | 46.9% |
| 2 | 583 | 7.4% |
| 3 | 295 | 3.7% |
| 4 | 211 | 2.7% |
| 5 | 157 | 2.0% |
| 6 | 114 | 1.4% |
| 7 | 67 | 0.8% |
| 8 | 58 | 0.7% |
| 9 | 50 | 0.6% |
| 10 | 41 | 0.5% |
| 11 | 36 | 0.5% |
| 12 | 23 | 0.3% |
| 13 | 16 | 0.2% |
| 14 | 14 | 0.2% |

Depth zero includes both first-of-line families and lineages truncated at the archive
boundary; see Section 5.3.

---

*Preprint generated 2026-09-15. Every quantity is interpolated from the pipeline's own
statistics and quality-assurance files; none is transcribed by hand.*
