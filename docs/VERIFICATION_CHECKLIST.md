# CIDEX Verification Checklist

> **DRAFT — NOT VERIFIED.** This package has not passed its verification gate. No number in it has been checked against the primary source by the author. Do not cite, deposit, or redistribute.

Version 1.0 · built 2026-09-14 · author: Imafidon, Osariemen (ORCID 0009-0006-3069-4674)

Nothing in this package may be deposited, cited, or described as published until every
box below is ticked by the author personally. The mechanical checks are automated; the
judgement calls are not, which is the entire point.

---

## Part 1 — Reproduce

- [ ] Ran the pipeline from a clean checkout following `README.md`
- [ ] `data/processed/stats.json` matches the one shipped in this package
- [ ] All 9 integrity checks report PASS
- [ ] The SHA-256 hashes in `logs/provenance.jsonl` match the EPA files I downloaded

Expected headline figures:

| | |
|---|---|
| Engine families | 8,627 (702 highway, 7,925 nonroad) |
| Configurations | 9,794 |
| Emission records | 97,008 |
| Manufacturers | 108 |
| Distinct lineages | 2,541 |

## Part 2 — Spot-check against EPA

Five checks, each probing a different way the harmonization could be wrong. Look each one
up by hand in EPA's interactive certificate data tool.

### Check 1

**highway, transient NOx — the standard case**

| | |
|---|---|
| Panel | highway |
| Engine family | `MSZXH05.23FD` |
| Model year | 2021 |
| Pollutant | NOx |
| Test type | transient |
| **CIDEX says** | **0.17 g/bhp-hr** |

- [ ] Looked this family up in EPA's interactive certificate tool
- [ ] The value above matches, or I have recorded what it actually says: ______________

### Check 2

**highway, earliest model year present — tests the MY2015-16 archive boundary**

| | |
|---|---|
| Panel | highway |
| Engine family | `FNGCH0466AEA` |
| Model year | 2015 |
| Pollutant | PM |
| Test type | steady_state |
| **CIDEX says** | **0.01 g/bhp-hr** |

- [ ] Looked this family up in EPA's interactive certificate tool
- [ ] The value above matches, or I have recorded what it actually says: ______________

### Check 3

**nonroad, steady-state NOx — tests the wide-to-long unpivot**

| | |
|---|---|
| Panel | nonroad |
| Engine family | `LCPXL08.8NZS` |
| Model year | 2020 |
| Pollutant | NOx |
| Test type | steady_state |
| **CIDEX says** | **3.36 g/kW-hr** |

- [ ] Looked this family up in EPA's interactive certificate tool
- [ ] The value above matches, or I have recorded what it actually says: ______________

### Check 4

**deepest carryover lineage (depth 14, root CCPXL32.0NZS) — tests lineage resolution**

| | |
|---|---|
| Panel | nonroad |
| Engine family | `TCPXL32.1NZS` |
| Model year | 2026 |
| Pollutant | NMHC |
| Test type | steady_state |
| **CIDEX says** | **0.08 g/kW-hr** |

- [ ] Looked this family up in EPA's interactive certificate tool
- [ ] The value above matches, or I have recorded what it actually says: ______________

### Check 5

**a flagged negative value — is this real in EPA's own record?**

| | |
|---|---|
| Panel | nonroad |
| Engine family | `CDICL05.8HTA` |
| Model year | 2012 |
| Pollutant | NOx |
| Test type | steady_state |
| **CIDEX says** | **-1.0 g/kW-hr** |

- [ ] Looked this family up in EPA's interactive certificate tool
- [ ] The value above matches, or I have recorded what it actually says: ______________


## Part 3 — Judgement calls only the author can make

- [ ] **`NMHCE` stays separate from `NMHC`.** I have confirmed these are different
      regulatory constructs and should not be merged. *(If wrong, say so — it is one line
      in `src/cidex/vocab.py`.)*
- [ ] **The negative values.** Having checked EPA's own record for
      `CDICL05.8HTA`, I confirm that publishing them as-is with a
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
