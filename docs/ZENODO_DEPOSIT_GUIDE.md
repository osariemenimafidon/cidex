# Depositing CIDEX on Zenodo

**Do not start until `docs/VERIFICATION_CHECKLIST.md` is signed.** A DOI is permanent.

There are two routes. **Route A is better** and is the one this repository is set up for.

---

## Route A — GitHub release, Zenodo deposits automatically

Zenodo's GitHub integration performs the deposit on Zenodo's servers. Nothing has to reach
Zenodo from your machine, and every future version is one release away. `.zenodo.json` in
the repository root supplies the metadata, so the record is not assembled from GitHub's
repository description.

### A1. Link Zenodo to GitHub, once

1. Go to <https://zenodo.org/account/settings/github/>
2. Sign in with your ORCID if prompted, and authorise GitHub access
3. Find **osariemenimafidon/cidex** in the repository list and switch it **On**

If the repository does not appear, use **Sync now** — Zenodo caches the list.

### A2. Publish a release on GitHub

1. Go to <https://github.com/osariemenimafidon/cidex/releases/new>
2. Click **Choose a tag**, type `v1.0.0`, choose **Create new tag on publish**
3. Release title: `CIDEX v1.0.0`
4. Description: a sentence or two. The archive's own README carries the detail.
5. Click **Publish release**

Zenodo receives the webhook, fetches the source archive, reads `.zenodo.json`, and mints
the DOI. It usually appears within a few minutes at
<https://zenodo.org/account/settings/github/>.

### A3. What you get

Two DOIs. A **concept DOI** that always resolves to the newest version — cite this one in
a CV — and a **version DOI** fixed to v1.0.0, which is what a paper citing these exact
numbers should reference.

### A4. Annual versioning

The CV commitment is annual maintenance. Under Route A that is: re-run the pipeline
against the refreshed EPA files, re-verify, tag `v1.1.0`, publish the release. Zenodo
mints a new version DOI under the same concept DOI automatically.

---

## Route B — manual web upload

Use this only if Route A fails. It deposits the built archive rather than the source tree.

### B1. Build the release archive

```bash
cd ~/Documents/cidex
python3 scripts/09_release.py
```

This writes `release/cidex-v1.0.0.zip` containing the data, code, documentation and
provenance log — but **not** the raw EPA files, which are redistributable but large and
better cited than copied.

### B2. New upload

**https://zenodo.org/uploads/new** — drag in `release/cidex-v1.0.0.zip`.

### B3. Metadata

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

### B4. Publish

Zenodo warns that publishing is irreversible. It is. Check the creator spelling and the
ORCID one more time, then publish.

### B5. Record it, the same day

1. Copy the DOI into `CITATION.cff` (`doi:` field) and the README badge.
2. Add a row to `~/Documents/facet/docs/EVIDENCE_LOG.csv` with the date, DOI, URL and a
   saved PDF of the Zenodo record page.
3. Move CIDEX from `Draft built` to `Published` in `~/Documents/facet/PORTFOLIO.md`.
4. Confirm the DOI appears on your ORCID record — it should arrive automatically if
   ORCID is linked to Zenodo. If not, add it manually.
5. Commit and push all of the above.

A publication that is not logged the day it happens is the one that goes missing later.

## After either route — record it

The CV line commits to annual versioning. Zenodo handles this properly: use **New
version** on the existing record rather than a fresh upload, and the DOI you mint stays
resolvable while a version-specific DOI is issued alongside it. EPA refreshes the source
files quarterly, so an annual rebuild is a real commitment with a real cadence behind it —
re-run the pipeline, diff `stats.json`, and deposit a new version.
