# CIDEX

**Compression-Ignition Engine Certification Panel**

> **DRAFT — NOT VERIFIED.** This package has not passed its verification gate. No number in it has been checked against the primary source by the author. Do not cite, deposit, or redistribute.

A harmonized engine-family-level panel of US EPA certification data for heavy-duty
highway and nonroad compression-ignition engines.

8,627 engine families · 97,008 emission records ·
108 manufacturers · MY2011–2027

Imafidon, Osariemen · [ORCID 0009-0006-3069-4674](https://orcid.org/0009-0006-3069-4674) · Independent Researcher
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
| `cidex_family.csv` | 8,627 | One row per (panel, model year, engine family) |
| `cidex_config.csv` | 9,794 | Engine configurations within a family |
| `cidex_emissions.csv` | 97,008 | One row per (family, pollutant, test type) |
| `cidex_carryover.csv` | 7,925 | Resolved nonroad certification lineage |

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
right. Usable ranges: highway **MY2017–2026**,
nonroad **MY2012–2026**.

```python
df = df[df.year_coverage == "complete"]
```

**3. 50 records have negative certification results.** Published
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
