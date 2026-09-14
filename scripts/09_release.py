"""09 — Build the release archive for deposit.

Ships data, code, documentation and the provenance log. Does NOT ship the raw EPA
workbooks: they are redistributable but large, and a hash-verified provenance record
plus a URL is a better citation than a copy that silently ages.

Refuses to build while the publication gate fails.
"""
import json, os, subprocess, sys, zipfile

VERSION = "1.0.0"
NAME = f"cidex-v{VERSION}"
REL = "release"

INCLUDE_DIRS = ["scripts", "src", "docs", "figures"]
INCLUDE_FILES = ["README.md", "LICENSE", "CITATION.cff", "AUTHORS.json",
                 "requirements.txt", "logs/provenance.jsonl"]
DATA = ["cidex_family.csv", "cidex_config.csv", "cidex_emissions.csv",
        "cidex_carryover.csv", "stats.json",
        "cidex_family.parquet", "cidex_config.parquet", "cidex_emissions.parquet"]


def main():
    gate = subprocess.run([sys.executable, "scripts/07_publish_gate.py"],
                          capture_output=True, text=True)
    if gate.returncode != 0:
        print(gate.stdout)
        print("Release refused: the publication gate is failing.")
        print("Resolve the items above, then re-run.")
        return 1
    if not os.path.exists(".gate-signed"):
        print("Release refused: docs/VERIFICATION_CHECKLIST.md has not been signed.")
        print("\nThe mechanical gate passes, but the human half has not happened. When you")
        print("have reproduced the pipeline and completed the five EPA spot-checks, run:")
        print("\n    touch .gate-signed\n")
        print("and re-run this script. That file is your attestation, not a formality.")
        return 1

    os.makedirs(REL, exist_ok=True)
    out = f"{REL}/{NAME}.zip"
    n = 0
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for d in INCLUDE_DIRS:
            for root, _, files in os.walk(d):
                if "__pycache__" in root:
                    continue
                for fn in files:
                    p = os.path.join(root, fn)
                    z.write(p, f"{NAME}/{p}"); n += 1
        for p in INCLUDE_FILES:
            if os.path.exists(p):
                z.write(p, f"{NAME}/{p}"); n += 1
        for fn in DATA:
            p = os.path.join("data/processed", fn)
            if os.path.exists(p):
                z.write(p, f"{NAME}/data/{fn}"); n += 1

    size = os.path.getsize(out)
    print(f"{out}  ({size/1e6:.1f} MB, {n} files)")
    print("\nReady to deposit. Follow docs/ZENODO_DEPOSIT_GUIDE.md.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
