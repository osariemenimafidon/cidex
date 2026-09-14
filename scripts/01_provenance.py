"""01 — Record provenance for every raw source file.

EPA is not reachable from the build environment (organisation egress policy),
so raw files are placed in data/raw/ by hand. Provenance is therefore recorded
from the bytes on disk: name, size, SHA-256, mtime, and the canonical source URL
they are asserted to have come from. A rebuilder checks the hash, not our word.
"""
import hashlib, json, os, datetime

RAW = "data/raw"
LOG = "logs/provenance.jsonl"

SOURCES = {
    "heavy-duty-gas-and-diesel-engines-2015-present.xlsx": {
        "panel": "highway",
        "url": "https://www.epa.gov/system/files/documents/2026-03/heavy-duty-gas-and-diesel-engines-2015-present.xlsx",
        "publisher": "US EPA Office of Transportation and Air Quality",
        "vintage": "2026-03 file drop",
        "model_years": "2015-present",
    },
    "nonroad-compression-ignition-2011-present.xlsx": {
        "panel": "nonroad",
        "url": "https://www.epa.gov/system/files/documents/2026-03/nonroad-compression-ignition-2011-present.xlsx",
        "publisher": "US EPA Office of Transportation and Air Quality",
        "vintage": "2026-03 file drop",
        "model_years": "2011-present",
    },
}


def sha256(path, chunk=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def main():
    os.makedirs("logs", exist_ok=True)
    records = []
    for fname, meta in SOURCES.items():
        path = os.path.join(RAW, fname)
        if not os.path.exists(path):
            raise SystemExit(
                f"MISSING: {path}\nDownload it from:\n  {meta['url']}\n"
                "See README section 'Getting the source data'."
            )
        st = os.stat(path)
        rec = {
            "recorded_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "file": fname,
            "bytes": st.st_size,
            "sha256": sha256(path),
            "mtime_utc": datetime.datetime.fromtimestamp(
                st.st_mtime, datetime.timezone.utc).isoformat(),
            **meta,
        }
        records.append(rec)
        print(f"{fname}\n  {rec['bytes']:,} bytes  sha256={rec['sha256'][:16]}…")
    with open(LOG, "a") as fh:
        for r in records:
            fh.write(json.dumps(r) + "\n")
    print(f"\nprovenance appended to {LOG} ({len(records)} records)")


if __name__ == "__main__":
    main()
