"""15 - Regenerate qa/explorer_data.json from the current build.

This file feeds the CIDEX explorer page. It was previously produced by hand,
which meant it drifted: it carried an emission-row count from an earlier build
and an integrity-check list that predated two of the checks. A published file
that disagrees with the dataset it describes is the exact failure this project
exists to prevent, so it is now generated from the processed tables like
everything else, and re-run as the last step of every build.

The sample is deterministic: a fixed stride over the sorted emission table
rather than a random draw, so two builds of the same data produce the same
file and a diff means the data changed.
"""
import csv, json, os, random
from collections import Counter, defaultdict

OUT, QA = "data/processed", "qa"
S = json.load(open(f"{OUT}/stats.json"))
SAMPLE_N = 400

def rows(name):
    with open(f"{OUT}/{name}", newline="") as fh:
        return list(csv.DictReader(fh))

fam  = rows("cidex_family.csv")
emis = rows("cidex_emissions.csv")
carry = rows("cidex_carryover.csv")

# ----------------------------------------------------------------- stats block
STAT_KEYS = [
    "build_date", "families_total", "families_highway", "families_nonroad",
    "configs_total", "emission_rows_total", "emission_rows_highway",
    "emission_rows_nonroad", "manufacturers_total", "manufacturers_highway",
    "manufacturers_nonroad", "pollutant_count", "units_present",
    "model_year_min_highway", "model_year_max_highway", "model_year_min_nonroad",
    "model_year_max_nonroad", "carryover_distinct_lineages", "carryover_depth_max",
    "carryover_families_with_link", "carryover_orphan_edges",
    "carryover_self_referencing", "carryover_true_cycles", "negative_cert_results",
    "negative_cert_result_share_pct", "negative_cert_result_families",
    "integrity_checks", "integrity_all_passed", "carryover_longest_example",
]
missing = [k for k in STAT_KEYS if k not in S]
if missing:
    raise SystemExit(f"stats.json is missing keys the explorer needs: {missing}")
stats = {k: S[k] for k in STAT_KEYS}

# ------------------------------------------------------------------ aggregates
by_year = defaultdict(Counter)
for r in fam:
    by_year[int(r["model_year"])][r["panel"]] += 1
families_by_year = [
    {"year": y, "highway": by_year[y].get("highway", 0),
     "nonroad": by_year[y].get("nonroad", 0)}
    for y in sorted(by_year)]

poll = defaultdict(Counter)
for r in emis:
    poll[r["pollutant"]][r["panel"]] += 1
pollutant_coverage = sorted(
    ({"pollutant": p, "highway": c.get("highway", 0), "nonroad": c.get("nonroad", 0),
      "total": sum(c.values())} for p, c in poll.items()),
    key=lambda d: -d["total"])

tier = Counter(r["tier"] for r in fam if r["panel"] == "nonroad" and r["tier"])
nonroad_tier = [{"tier": t, "n": n} for t, n in tier.most_common()]

depth = Counter(int(r["lineage_depth"]) for r in carry if r["lineage_depth"] != "")
lineage_depth = [{"depth": d, "n": depth[d]} for d in sorted(depth)]

# --------------------------------------------------------------------- records
MFR = {(r["panel"], r["model_year"], r["engine_family"]): r["manufacturer"] for r in fam}
def mfr(r): return MFR.get((r["panel"], r["model_year"], r["engine_family"]))

def num(v):
    if v is None or v == "": return None
    try:    return float(v)
    except ValueError: return v

flagged_rows = [
    {"panel": r["panel"], "model_year": int(r["model_year"]),
     "engine_family": r["engine_family"], "manufacturer": mfr(r),
     "pollutant": r["pollutant"], "test_type": r["test_type"],
     "cert_result": num(r["cert_result"]), "units": r["units"]}
    for r in emis if r["quality_flag"]]

if len(flagged_rows) != S["negative_cert_results"]:
    raise SystemExit(
        f"flagged row count {len(flagged_rows)} != stats negative_cert_results "
        f"{S['negative_cert_results']}; the explorer and the panel disagree.")

# Deterministic stride, not a random draw: the same data yields the same file.
key = lambda r: (r["panel"], r["model_year"], r["engine_family"], r["pollutant"],
                 r["test_type"])
ordered = sorted(emis, key=key)
stride = max(1, len(ordered) // SAMPLE_N)
sample_rows = [
    {"panel": r["panel"], "model_year": int(r["model_year"]),
     "engine_family": r["engine_family"], "manufacturer": mfr(r),
     "pollutant": r["pollutant"], "test_type": r["test_type"],
     "cert_result": num(r["cert_result"]), "standard": num(r["standard"]),
     "fel": num(r["fel"]), "units": r["units"],
     "quality_flag": r["quality_flag"] or None}
    for r in ordered[::stride][:SAMPLE_N]]

payload = {
    "stats": stats,
    "families_by_year": families_by_year,
    "pollutant_coverage": pollutant_coverage,
    "nonroad_tier": nonroad_tier,
    "lineage_depth": lineage_depth,
    "flagged_rows": flagged_rows,
    "sample_rows": sample_rows,
}

os.makedirs(QA, exist_ok=True)
with open(f"{QA}/explorer_data.json", "w") as fh:
    json.dump(payload, fh, indent=1)

print(f"written: {QA}/explorer_data.json "
      f"({os.path.getsize(f'{QA}/explorer_data.json'):,} bytes)")
print(f"  build date            {stats['build_date']}")
print(f"  emission rows         {stats['emission_rows_total']:,}")
print(f"  pollutants            {len(pollutant_coverage)}")
print(f"  flagged rows          {len(flagged_rows)}")
print(f"  sample rows           {len(sample_rows)} (stride {stride})")
print(f"  integrity checks      {len(stats['integrity_checks'])}")
