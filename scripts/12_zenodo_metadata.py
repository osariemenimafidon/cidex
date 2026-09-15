"""12 — Generate .zenodo.json for the GitHub–Zenodo integration.

Zenodo is unreachable from this build environment, but Zenodo's GitHub
integration performs the deposit server-side: enable it for the repository,
publish a GitHub release, and Zenodo fetches the tarball and mints a DOI without
anything having to reach Zenodo from here.

This file supplies the metadata for that deposit so the record is not built from
GitHub's repository description alone. Fields come from AUTHORS.json and
stats.json, so the deposit cannot disagree with the dataset.
"""
import json
S = json.load(open("data/processed/stats.json"))
A = json.load(open("AUTHORS.json"))
au = A["authors"][0]

desc = f"""<p>A harmonized engine-family-level panel of United States Environmental Protection
Agency emission certification data for heavy-duty highway and nonroad compression-ignition
engines.</p>

<p>EPA publishes this record as two Excel workbooks whose internal structures are mutually
incompatible: one is organised long on pollutant and wide on test type, the other wide on
pollutant beneath a two-level header. Both place their true column headers on the second
row, so a naive read of either produces plausible but incorrect data without raising an
error. CIDEX reconciles both into a single analysis-ready schema.</p>

<p><strong>Contents.</strong> {S['families_total']:,} engine families,
{S['configs_total']:,} engine configurations and {S['emission_rows_total']:,} emission
records across {S['manufacturers_total']:,} manufacturers, model years
{S['model_year_min_nonroad']}&ndash;{S['model_year_max_nonroad']}. Includes a resolved
carryover lineage linking {S['carryover_distinct_lineages']:,} distinct nonroad
certification families across model years, with a maximum chain depth of
{S['carryover_depth_max']}.</p>

<p><strong>Units are preserved as certified and never silently converted.</strong> Highway
results are in g/bhp-hr, nonroad in g/kW-hr, nonroad smoke opacity in percent. Comparing
across panels without deliberate conversion is invalid.</p>

<p><strong>Before use, read LIMITATIONS.md.</strong> In particular:
{S['negative_cert_results']} records carry physically impossible negative certification
results, published exactly as EPA reports them and carrying a quality flag; and four
model years at the panels' edges are structurally incomplete and flagged, because EPA
holds older years in archive files not ingested in this version.</p>

<p>The archive includes the full pipeline, a technical report documenting the method and
the defects found during development, a codebook, a verification checklist signed by the
author, and a provenance log recording the SHA-256 digest of every source file. EPA
replaces the source files quarterly in place, so the digests rather than the URLs identify
the data this version was built from.</p>"""

meta = {
    "title": "CIDEX: Compression-Ignition Engine Certification Panel",
    "upload_type": "dataset",
    "description": desc,
    "creators": [{
        "name": au["name"],
        "orcid": au["orcid"],
        "affiliation": au["affiliation"],
    }],
    "license": "cc-by-4.0",
    "access_right": "open",
    "version": "1.0.0",
    "language": "eng",
    "keywords": [
        "diesel engines", "emissions certification", "compression ignition",
        "EPA", "nonroad engines", "heavy-duty engines", "engine family",
        "air quality", "open data", "data harmonization",
    ],
    "related_identifiers": [
        {"identifier": "https://github.com/osariemenimafidon/cidex",
         "relation": "isSupplementTo", "scheme": "url"},
        {"identifier": "https://www.epa.gov/compliance-and-fuel-economy-data/"
                       "annual-certification-data-vehicles-engines-and-equipment",
         "relation": "isDerivedFrom", "scheme": "url"},
        {"identifier": "https://osariemenimafidon.github.io/facet/",
         "relation": "isPartOf", "scheme": "url"},
    ],
    "notes": ("Part of the FACET research program (Fuel-Adaptive Control Evidence & "
              "Transferability). Built entirely from openly available federal data, "
              "self-funded, and published openly."),
}
json.dump(meta, open(".zenodo.json", "w"), indent=2, ensure_ascii=False)
print(".zenodo.json written")
print(f"  title:     {meta['title']}")
print(f"  version:   {meta['version']}")
print(f"  creator:   {au['name']} ({au['orcid']})")
print(f"  licence:   {meta['license']}")
print(f"  keywords:  {len(meta['keywords'])}")
print(f"  related:   {len(meta['related_identifiers'])} identifiers")
