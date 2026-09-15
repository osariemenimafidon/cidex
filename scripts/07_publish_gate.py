"""07 — Pre-publication gate.

Scans for anything that must not reach a permanent public record. Two severities,
because they are genuinely different things:

  BLOCKING  A draft stamp or unfilled placeholder in a document a reader will see,
            or a credential anywhere at all. These make publication wrong.

  ADVISORY  A [VERIFY] annotation in source code. That is a legitimate engineering
            note, not a defect — but the author should have consciously resolved
            each one, so they are listed rather than ignored.

The mechanical half of the gate. The human half — the author having actually
reproduced and spot-checked the pipeline — cannot be scripted, which is why
docs/VERIFICATION_CHECKLIST.md ends in a signature line.
"""
import os, re, sys

SKIP_DIRS = {".git", "__pycache__", "data", "logs", ".venv", "figures", "qa"}
# These two describe the gate rather than being subject to it.
SKIP_ENTIRELY = {"07_publish_gate.py", "06_docs.py"}
# The author's own working documents, not publication outputs.
SKIP_DOC_SCAN = {"VERIFICATION_CHECKLIST.md", "BUILD_SPEC.md", "PUBLISH_GUIDE.md"}

DOC_EXT  = {".md", ".cff", ".html", ".txt", ".rst"}
TEXT_EXT = DOC_EXT | {".py", ".json", ".csv", ".yml", ".yaml", ".toml"}

DOC_PATTERNS = [
    # Match the STAMP, not the word. The technical report documents how the draft
    # mechanism works, and a bare \bDRAFT\b flagged that prose as if it were a
    # stamp. A scanner that cries wolf on its own documentation gets ignored,
    # which is the failure mode that matters.
    ("DRAFT stamp",     re.compile(r"DRAFT\s*[-\u2013\u2014]\s*NOT VERIFIED")),
    ("VERIFY tag",      re.compile(r"\[VERIFY[^\]]*\]")),
    ("TARGET tag",      re.compile(r"\[TARGET[^\]]*\]")),
    ("DOI placeholder", re.compile(r"\[DOI\]")),
    ("placeholder",     re.compile(r"\[(TBD|TODO|XXX|FIXME|journal[^\]]*|date|tracking number)\]", re.I)),
]
SECRET_PATTERNS = [
    ("GitHub token",   re.compile(r"gh[pousr]_[A-Za-z0-9]{16,}|github_pat_[A-Za-z0-9_]{20,}")),
    ("generic secret", re.compile(r"(?i)\b(api[_-]?key|secret|password|access[_-]?token)\s*[:=]\s*['\"][^'\"]{8,}")),
    ("private key",    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
]
CODE_ADVISORY = [("VERIFY annotation", re.compile(r"\[VERIFY[^\]]*\]"))]
# A bare "DRAFT" at the start of a line in a document is probably a stamp in a
# shape this scanner does not know. Advisory, not blocking.
DOC_ADVISORY = [("possible draft marker", re.compile(r"^\s*>?\s*\*{0,2}DRAFT\b"))]


def scan():
    blocking, advisory = [], []
    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        for fn in files:
            ext = os.path.splitext(fn)[1]
            if fn in SKIP_ENTIRELY or ext not in TEXT_EXT:
                continue
            path = os.path.join(root, fn)
            try:
                lines = open(path, encoding="utf-8", errors="replace").read().splitlines()
            except OSError:
                continue
            is_doc = ext in DOC_EXT and fn not in SKIP_DOC_SCAN
            for n, line in enumerate(lines, 1):
                for label, rx in SECRET_PATTERNS:
                    if rx.search(line):
                        blocking.append((label, path, n, "<redacted>"))
                if is_doc:
                    for label, rx in DOC_PATTERNS:
                        if rx.search(line):
                            blocking.append((label, path, n, line.strip()[:88]))
                    for label, rx in DOC_ADVISORY:
                        if rx.search(line):
                            advisory.append((label, path, n, line.strip()[:88]))
                elif ext == ".py":
                    for label, rx in CODE_ADVISORY:
                        if rx.search(line):
                            advisory.append((label, path, n, line.strip()[:88]))
    return blocking, advisory


def report(title, items):
    by = {}
    for label, path, n, line in items:
        by.setdefault(label, []).append((path, n, line))
    print(title)
    for label, rows in by.items():
        print(f"  {label} ({len(rows)}):")
        for path, n, line in rows[:12]:
            print(f"    {path}:{n}  {line}")
        if len(rows) > 12:
            print(f"    … and {len(rows)-12} more")
    print()


def attestation_drift():
    """Compare the spot-checks the author signed against the current build.

    The selector picks a median row per category, so its output moves when the
    row set changes. A signature that silently follows is not an attestation.
    """
    if not os.path.exists(".gate-signed"):
        return None
    import json
    line = next((l for l in open(".gate-signed") if l.startswith("ATTESTED_SPOT_CHECKS:")), None)
    if not line:
        return ["attestation file records no spot-checks; re-sign to pin them"]
    attested = [x.strip() for x in line.split(":", 1)[1].split(",") if x.strip()]
    try:
        S = json.load(open("data/processed/stats.json"))
    except OSError:
        return ["stats.json missing; cannot check the attestation"]
    current = [c["engine_family"] for c in S.get("spot_checks", [])]
    if set(attested) != set(current):
        return [f"attested: {sorted(attested)}", f"current build: {sorted(current)}",
                "The signed spot-checks no longer match this build. Re-verify and re-sign."]
    return []


def main():
    blocking, advisory = scan()
    drift = attestation_drift()
    if advisory:
        report(f"ADVISORY — {len(advisory)} engineering annotation(s) to confirm resolved:", advisory)
    if drift:
        print("GATE FAIL — the signed attestation does not match this build:\n")
        for d in drift:
            print("   ", d)
        print()
        return 1
    if blocking:
        report(f"GATE FAIL — {len(blocking)} blocking item(s):", blocking)
        return 1
    print("GATE PASS (mechanical) — no draft stamps, placeholders, or credentials in any")
    print("document intended for publication.\n")
    if os.path.exists(".gate-signed"):
        print("HUMAN HALF: SIGNED. .gate-signed is present — the author has attested to")
        print("reproducing the pipeline, completing the spot-checks against the primary")
        print("source, and ruling on the flagged judgement calls.\n")
        print("Attested spot-checks match this build.")
        print("Delete .gate-signed and rebuild to return every document and figure to DRAFT.")
        print("\nGATE CLEARED.")
    else:
        print("HUMAN HALF: NOT SIGNED. The mechanical checks pass, but .gate-signed is")
        print("absent. The gate is not cleared until the author has reproduced the")
        print("pipeline, completed the spot-checks, and signed")
        print("docs/VERIFICATION_CHECKLIST.md.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
