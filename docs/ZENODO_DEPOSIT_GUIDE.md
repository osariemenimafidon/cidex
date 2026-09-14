# Depositing CIDEX on Zenodo

**Do not start this until `docs/VERIFICATION_CHECKLIST.md` is signed.** A DOI is permanent.

Zenodo is unreachable from the build environment (organisation egress policy), so this
step is manual. It is a web form and takes about ten minutes. Every field you need is
filled in below — this should be copy-paste, not decisions.

## Step 0 — practise on the sandbox first

Do the whole thing once at **https://sandbox.zenodo.org** before touching the real site.
Sandbox DOIs are fake and the instance is wiped periodically, which is exactly what you
want for a rehearsal. The form is identical.

## Step 1 — build the release archive

```bash
cd ~/Documents/cidex
python3 scripts/09_release.py
```

This writes `release/cidex-v1.0.0.zip` containing the data, code, documentation and
provenance log — but **not** the raw EPA files, which are redistributable but large and
better cited than copied.

## Step 2 — new upload

**https://zenodo.org/uploads/new** — drag in `release/cidex-v1.0.0.zip`.

## Step 3 — metadata

| Field | Value |
|---|---|
| **Resource type** | Dataset |
| **Title** | CIDEX: Compression-Ignition Engine Certification Panel |
| **Creator** | Imafidon, Osariemen |
| **ORCID** | 0009-0006-3069-4674 |
| **Affiliation** | Independent Researcher |
| **Publication date** | the date you deposit |
| **Version** | 1.0.0 |
| **Language** | English |
| **Licence** | Creative Commons Attribution 4.0 International |

**Description** — paste the abstract from `CITATION.cff`, then add:

> Units are preserved as certified and are not comparable across panels without
> conversion. See LIMITATIONS.md in the archive before use, in particular the note on
> structurally incomplete model years at each panel's edge.

**Keywords**: `diesel engines`, `emissions certification`, `compression ignition`, `EPA`,
`nonroad engines`, `heavy-duty engines`, `open data`, `engine family`

**Related identifiers** — add once the GitHub repository exists:

| Relation | Identifier |
|---|---|
| is supplement to | the CIDEX GitHub repository URL |
| is derived from | https://www.epa.gov/compliance-and-fuel-economy-data/annual-certification-data-vehicles-engines-and-equipment |

## Step 4 — publish

Zenodo warns that publishing is irreversible. It is. Check the creator spelling and the
ORCID one more time, then publish.

## Step 5 — record it, the same day

1. Copy the DOI into `CITATION.cff` (`doi:` field) and the README badge.
2. Add a row to `~/Documents/facet/docs/EVIDENCE_LOG.csv` with the date, DOI, URL and a
   saved PDF of the Zenodo record page.
3. Move CIDEX from `Draft built` to `Published` in `~/Documents/facet/PORTFOLIO.md`.
4. Confirm the DOI appears on your ORCID record — it should arrive automatically if
   ORCID is linked to Zenodo. If not, add it manually.
5. Commit and push all of the above.

A publication that is not logged the day it happens is the one that goes missing later.

## On annual maintenance

The CV line commits to annual versioning. Zenodo handles this properly: use **New
version** on the existing record rather than a fresh upload, and the DOI you mint stays
resolvable while a version-specific DOI is issued alongside it. EPA refreshes the source
files quarterly, so an annual rebuild is a real commitment with a real cadence behind it —
re-run the pipeline, diff `stats.json`, and deposit a new version.
