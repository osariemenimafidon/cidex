# CIDEX Limitations

> **DRAFT — NOT VERIFIED.** This package has not passed its verification gate. No number in it has been checked against the primary source by the author. Do not cite, deposit, or redistribute.

Version 1.0 · built 2026-09-15

Stated plainly, because a dataset whose limitations are buried is worse than one that
does not exist.

## 1. Units are not comparable across panels

The single largest correctness risk in this dataset. Highway results are certified in
`g/bhp-hr`, nonroad in `g/kW-hr`. Any aggregate that mixes panels without converting is
wrong. CIDEX labels every row and refuses to convert silently; the responsibility for
converting is deliberately left with the user.

## 2. 50 negative certification results

50 rows (0.0515% of
97,008), across 18 engine families,
all in the nonroad panel, carry a negative
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

A year is flagged incomplete when it holds under 50% of the median count of that
panel's interior years:

| Panel | Model year | Families | Share of interior median | Reason |
|---|---|---|---|---|
| highway | 2015 | 3 | 5% | EPA archive file not ingested |
| highway | 2016 | 29 | 45% | EPA archive file not ingested |
| nonroad | 2011 | 66 | 12% | EPA archive file not ingested |
| nonroad | 2027 | 8 | 2% | still being certified when the file was downloaded |

Every row of `cidex_family.csv` and `cidex_emissions.csv` carries a **`year_coverage`**
column (`complete` / `partial_archive` / `partial_forward`), so this cannot be missed by
accident.

**Usable ranges for trend analysis:** highway **MY2017-2026**, nonroad **MY2012-2026**.

```python
df = df[df.year_coverage == "complete"]   # before any time series
```

The 50% threshold is a judgement, not a fact about the data. It happens to separate
the observed cases cleanly - no year sits near the boundary - but a reuser with a different
purpose may prefer a different cut, and the raw counts above are given so they can make one.

## 5. Manufacturer names are not normalised

Spellings vary across model years in the source and CIDEX preserves them. Grouping by
manufacturer requires the user's own normalisation.

## 6. Carryover lineage is nonroad-only and has open edges

5,982 nonroad families name a predecessor.
568 of those name a family that is **not** in this panel —
usually a pre-2011 family, outside the published window. Those
lineages are truncated, not wrong, but a depth of 0 does not always mean "first of its line".
30 families point at themselves, which EPA appears to use to
mark an unchanged re-certification; these are treated as lineage termini.
0 true cycles exist.

## 7. Family-level attributes were de-duplicated

Where a source attribute was constant within a family it was kept at family level; where
it varied it was moved to `cidex_config.csv`. The build asserts the family table is truly
family-level and fails rather than silently picking a winning row.

## Integrity checks

All checks below pass in this build. They are assertions about internal consistency, **not**
evidence that the values match EPA — that is what the verification gate is for.

- PASS — `family_key_unique`
- PASS — `no_emission_row_without_family`
- PASS — `units_never_null`
- PASS — `no_mixed_units_within_panel`
- PASS — `highway_units_correct`
- PASS — `nonroad_units_correct`
- PASS — `carryover_no_true_cycles`
- PASS — `every_negative_value_is_flagged`
- PASS — `flagged_share_below_0pt1pct`
