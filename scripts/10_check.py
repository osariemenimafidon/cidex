"""10 — Compare a fresh rebuild against the shipped reference, and print the
spot-checks the author must do by hand.

Volatile keys (build date, and the provenance timestamps) are excluded from the
diff: they are expected to differ and flagging them would train the reader to
ignore the output.
"""
import json, sys

VOLATILE = {"build_date"}


def flatten(o, prefix=""):
    out = {}
    if isinstance(o, dict):
        for k, v in o.items():
            out.update(flatten(v, f"{prefix}.{k}" if prefix else k))
    elif isinstance(o, list):
        out[prefix] = json.dumps(o, sort_keys=True)
    else:
        out[prefix] = o
    return out


def main():
    new = json.load(open("data/processed/stats.json"))
    try:
        ref = json.load(open("docs/stats_reference.json"))
    except FileNotFoundError:
        print("No reference to compare against (docs/stats_reference.json missing).")
        return 1

    a, b = flatten(ref), flatten(new)
    diffs = [(k, a.get(k), b.get(k)) for k in sorted(set(a) | set(b))
             if k.split(".")[0] not in VOLATILE and a.get(k) != b.get(k)]

    print("▶ Reproduction")
    if diffs:
        print(f"  MISMATCH — {len(diffs)} value(s) differ from the shipped build:\n")
        for k, x, y in diffs[:25]:
            print(f"    {k}\n      shipped:  {x}\n      your run: {y}")
        if len(diffs) > 25:
            print(f"    … and {len(diffs)-25} more")
        print("\n  Do not proceed. A mismatch means the pipeline is not deterministic,")
        print("  or your raw files differ from the ones this build used. Check the")
        print("  SHA-256 hashes in logs/provenance.jsonl first.")
        return 1

    print("  PASS — every value matches the shipped build exactly.\n")

    checks = new["integrity_checks"]
    print("▶ Integrity checks")
    for k, v in checks.items():
        print(f"  {'PASS' if v else 'FAIL':<5} {k}")
    if not all(checks.values()):
        return 1
    print()

    print("▶ Spot-checks — YOU must do these by hand")
    print("  EPA's tool: https://www.epa.gov/compliance-and-fuel-economy-data"
          "/annual-certification-data-vehicles-engines-and-equipment")
    print("  Open the interactive certificate data tool and search each family name.\n")
    for i, c in enumerate(new["spot_checks"], 1):
        print(f"  {i}. {c['engine_family']}   MY{c['model_year']}   [{c['panel']}]")
        print(f"     {c['pollutant']} / {c['test_type']}")
        print(f"     CIDEX says: {c['cidex_cert_result']} {c['units']}")
        print(f"     why: {c['why']}")
        print(f"     EPA says: ______________________\n")

    print("▶ Judgement calls — see docs/VERIFICATION_CHECKLIST.md Part 3")
    print("  Four decisions only you can make. Read them there.\n")
    print("════════════════════════════════════════════════════════════")
    print(" Mechanical half: PASS")
    print(" Human half: not done until you have completed the spot-checks,")
    print(" ruled on the judgement calls, and signed the checklist. Then:")
    print()
    print("     touch .gate-signed && python3 scripts/09_release.py")
    print("════════════════════════════════════════════════════════════")
    return 0


if __name__ == "__main__":
    sys.exit(main())
