#!/usr/bin/env python3
"""13 — Deposit CIDEX on Zenodo.

RUN THIS FROM YOUR OWN TERMINAL, not from an agent session. The build
environment cannot reach zenodo.org: the egress proxy refuses CONNECT with 403
before any TLS handshake, so no token is ever transmitted. Your own shell has no
such restriction.

    export ZENODO_SANDBOX_TOKEN=...      # rehearse first
    python3 scripts/13_zenodo_deposit.py --sandbox

    export ZENODO_TOKEN=...              # then the real thing
    python3 scripts/13_zenodo_deposit.py

The script uploads and sets metadata but STOPS before publishing. Publishing is
irreversible, so it is a separate, deliberate act: pass --publish once you have
reviewed the draft record in the browser.

Metadata comes from .zenodo.json, so the record cannot disagree with the dataset.
"""
import argparse, json, os, sys
from pathlib import Path

try:
    import requests
except ImportError:
    sys.exit("This script needs 'requests':  pip install requests")

REAL, SANDBOX = "https://zenodo.org", "https://sandbox.zenodo.org"


def die(msg, resp=None):
    if resp is not None:
        msg += f"\n  HTTP {resp.status_code}: {resp.text[:400]}"
    sys.exit("ERROR: " + msg)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sandbox", action="store_true", help="deposit to sandbox.zenodo.org")
    ap.add_argument("--publish", action="store_true",
                    help="publish immediately. IRREVERSIBLE. Omit to leave a draft.")
    ap.add_argument("--archive", default=None, help="zip to upload (default: newest in release/)")
    a = ap.parse_args()

    base = SANDBOX if a.sandbox else REAL
    var = "ZENODO_SANDBOX_TOKEN" if a.sandbox else "ZENODO_TOKEN"
    token = os.environ.get(var)
    if not token:
        die(f"{var} is not set. Create one at {base}/account/settings/applications/tokens/new/ "
            "with scopes deposit:write and deposit:actions.")

    gate = Path(".gate-signed")
    if not gate.exists():
        die("docs/VERIFICATION_CHECKLIST.md has not been signed (.gate-signed is absent). "
            "A DOI is permanent; do not deposit unverified work.")

    meta_path = Path(".zenodo.json")
    if not meta_path.exists():
        die(".zenodo.json not found. Run scripts/12_zenodo_metadata.py first.")
    meta = json.loads(meta_path.read_text())

    if a.archive:
        archive = Path(a.archive)
    else:
        zips = sorted(Path("release").glob("*.zip"), key=lambda p: p.stat().st_mtime)
        if not zips:
            die("No archive in release/. Run scripts/09_release.py first.")
        archive = zips[-1]
    if not archive.exists():
        die(f"{archive} not found.")

    s = requests.Session()
    s.params = {"access_token": token}

    print(f"Target:   {base}")
    print(f"Archive:  {archive}  ({archive.stat().st_size/1e6:.1f} MB)")
    print(f"Title:    {meta['title']}")
    print(f"Creator:  {meta['creators'][0]['name']} ({meta['creators'][0].get('orcid','-')})")
    print(f"Version:  {meta.get('version','-')}   Licence: {meta.get('license','-')}")
    print()

    r = s.get(f"{base}/api/deposit/depositions")
    if r.status_code == 401:
        die("Token rejected. Check it is for this instance "
            f"({'sandbox' if a.sandbox else 'production'}) and has deposit:write.", r)
    if not r.ok:
        die("Could not reach the deposit API.", r)

    r = s.post(f"{base}/api/deposit/depositions", json={})
    if not r.ok:
        die("Could not create the deposition.", r)
    dep = r.json()
    dep_id, bucket = dep["id"], dep["links"]["bucket"]
    print(f"Created draft deposition {dep_id}")

    with archive.open("rb") as fh:
        r = s.put(f"{bucket}/{archive.name}", data=fh)
    if not r.ok:
        die("Upload failed.", r)
    print(f"Uploaded {archive.name}")

    r = s.put(f"{base}/api/deposit/depositions/{dep_id}",
              json={"metadata": meta},
              headers={"Content-Type": "application/json"})
    if not r.ok:
        die("Metadata rejected.", r)
    print("Metadata set")

    draft = f"{base}/deposit/{dep_id}"
    if not a.publish:
        print(f"\nDRAFT created, NOT published.")
        print(f"Review it at: {draft}")
        print("\nWhen you are satisfied, either press Publish in the browser or re-run")
        print("this script with --publish. Publishing is irreversible.")
        return

    print("\n--- PUBLISHING. This is irreversible. ---")
    r = s.post(f"{base}/api/deposit/depositions/{dep_id}/actions/publish")
    if not r.ok:
        die("Publish failed.", r)
    out = r.json()
    doi = out.get("doi") or out.get("metadata", {}).get("prereserve_doi", {}).get("doi")
    print(f"\nPUBLISHED")
    print(f"  DOI:    {doi}")
    print(f"  Record: {out.get('links',{}).get('record_html', draft)}")
    print("\nNow: add the DOI to CITATION.cff and README.md, log it in")
    print("~/Documents/facet/docs/EVIDENCE_LOG.csv, and move CIDEX to 'Published'")
    print("in ~/Documents/facet/PORTFOLIO.md. Same day - unlogged publications go missing.")


if __name__ == "__main__":
    main()
