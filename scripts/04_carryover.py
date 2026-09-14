"""04 — Resolve the nonroad carryover lineage.

The nonroad panel names, for most families, the family it was carried over from.
These references chain, so a family's certification lineage can be followed back
across model years. This is not present in the highway panel and, as far as we
can tell, has not been published in resolved form.

D5: cycles and orphans are resolved-and-reported, never silently dropped.
"""
import json, os
import pandas as pd

OUT = "data/processed"


def main():
    fam = pd.read_csv(f"{OUT}/nonroad_family.csv")
    report = {}

    fam["engine_family"] = fam["engine_family"].astype(str).str.strip()
    fam["carryover_family"] = fam["carryover_family"].astype(str).str.strip()
    fam.loc[fam["carryover_family"].isin(["nan", "", "None"]), "carryover_family"] = pd.NA

    known = set(fam["engine_family"])
    edges = fam[fam["carryover_family"].notna()][
        ["model_year", "engine_family", "carryover_family"]].copy()

    report["families_total"] = len(fam)
    report["families_with_carryover"] = len(edges)
    report["families_without_carryover"] = len(fam) - len(edges)

    # An orphan names a predecessor that is not itself a family in this panel —
    # usually a pre-2011 family, i.e. outside the published window.
    edges["orphan"] = ~edges["carryover_family"].isin(known)
    report["orphan_edges"] = int(edges["orphan"].sum())
    report["resolvable_edges"] = int((~edges["orphan"]).sum())

    parent = dict(zip(edges["engine_family"], edges["carryover_family"]))

    # A family whose carryover_family is ITSELF is a terminus, not a loop: EPA
    # uses the self-reference to mark an unchanged re-certification. Counting it
    # as a cycle (as a naive traversal does) manufactures 109 false positives.
    self_ref = {k for k, v in parent.items() if k == v}
    report["self_referencing_families"] = len(self_ref)

    roots, depths, cycles = {}, {}, []
    for fam_name in fam["engine_family"]:
        seen, node, depth = set(), fam_name, 0
        while True:
            nxt = parent.get(node)
            if nxt is None or nxt not in known or nxt == node:
                break
            if nxt in seen:
                cycles.append(sorted(seen | {nxt})[:8])
                break
            seen.add(node)
            node = nxt
            depth += 1
        roots[fam_name] = node
        depths[fam_name] = depth

    report["true_cycles_detected"] = len(cycles)
    report["true_cycle_members"] = cycles[:10]

    out = pd.DataFrame({
        "panel": "nonroad",
        "model_year": fam["model_year"],
        "engine_family": fam["engine_family"],
        "carryover_family": fam["engine_family"].map(parent),
        "lineage_root": fam["engine_family"].map(roots),
        "lineage_depth": fam["engine_family"].map(depths),
    })
    out.to_csv(f"{OUT}/cidex_carryover.csv", index=False)

    d = out["lineage_depth"]
    report["depth_max"] = int(d.max())
    report["depth_mean"] = round(float(d.mean()), 3)
    report["depth_distribution"] = {str(k): int(v) for k, v in
                                    d.value_counts().sort_index().items()}
    report["distinct_lineages"] = int(out["lineage_root"].nunique())
    longest = out.loc[d.idxmax()]
    report["longest_lineage_example"] = {
        "engine_family": longest["engine_family"],
        "model_year": int(longest["model_year"]),
        "lineage_root": longest["lineage_root"],
        "depth": int(longest["lineage_depth"]),
    }

    with open("qa/04_carryover.json", "w") as fh:
        json.dump(report, fh, indent=2, default=str)
    print(json.dumps(report, indent=2, default=str))


if __name__ == "__main__":
    main()
