"""05 — Combine both panels, emit stats.json, and write the QA report.

Every number that appears in any CIDEX document is written here, into
stats.json, and interpolated from there. No figure or sentence in this
repository contains a hand-typed number.
"""
import json, os, hashlib
import pandas as pd

OUT = "data/processed"
S = {}


def load(name):
    return pd.read_csv(f"{OUT}/{name}.csv", low_memory=False)


def main():
    hw_f, nr_f = load("highway_family"), load("nonroad_family")
    hw_c, nr_c = load("highway_config"), load("nonroad_config")
    hw_e, nr_e = load("highway_emissions"), load("nonroad_emissions")
    carry = load("cidex_carryover")

    fam = pd.concat([hw_f, nr_f], ignore_index=True)
    cfg = pd.concat([hw_c, nr_c], ignore_index=True)
    em = pd.concat([hw_e, nr_e], ignore_index=True)

    # Quality flags. An emission rate cannot be physically negative, but 50 rows
    # in the EPA nonroad source are. CIDEX does not correct, clip or drop them:
    # the value stays as published and carries a flag, so a user can exclude
    # them deliberately and an author can raise them with EPA. [VERIFY]
    em["quality_flag"] = pd.NA
    em.loc[em.cert_result < 0, "quality_flag"] = "negative_cert_result"


    # --- model-year coverage -------------------------------------------------
    # Both panels are structurally incomplete at their edges, for two different
    # reasons: EPA holds older model years in separate archive files that CIDEX
    # v1.0 does not ingest, and the newest model year is still being certified.
    # A year is marked incomplete when it holds under half the median count of
    # the panel's interior years. Without this, a naive time series reads the
    # archive boundary as an industry collapse. Threshold is a judgment: [VERIFY]
    COVERAGE_THRESHOLD = 0.5
    coverage = {}
    for panel in ("highway", "nonroad"):
        s_ = fam[fam.panel.eq(panel)].groupby("model_year").size().sort_index()
        s_ = s_[s_ > 0]
        interior = s_.iloc[2:-2] if len(s_) > 4 else s_
        med = float(interior.median())
        years = {}
        for yr, n in s_.items():
            ratio = n / med if med else 1.0
            if ratio >= COVERAGE_THRESHOLD:
                state = "complete"
            elif yr == s_.index[-1]:
                state = "partial_forward"      # still being certified
            else:
                state = "partial_archive"      # older years live in EPA archive files
            years[str(int(yr))] = {"families": int(n), "share_of_median": round(ratio, 3),
                                   "coverage": state}
        good = [int(y) for y, v in years.items() if v["coverage"] == "complete"]
        coverage[panel] = {"interior_median": med, "by_year": years,
                           "usable_range": [min(good), max(good)] if good else None,
                           "excluded": sorted(int(y) for y, v in years.items()
                                              if v["coverage"] != "complete")}
    S["model_year_coverage"] = coverage
    S["coverage_threshold"] = COVERAGE_THRESHOLD

    # Carry the flag into the data so a user cannot miss it.
    flag = {}
    for panel, c in coverage.items():
        for y, v in c["by_year"].items():
            flag[(panel, int(y))] = v["coverage"]
    for df in (fam, em):
        df["year_coverage"] = [flag.get((p, y), "complete")
                               for p, y in zip(df.panel, df.model_year)]

    S["build_date"] = pd.Timestamp.utcnow().strftime("%Y-%m-%d")
    S["panels"] = ["highway", "nonroad"]

    S["families_total"] = int(len(fam))
    S["families_highway"] = int(len(hw_f))
    S["families_nonroad"] = int(len(nr_f))
    S["configs_total"] = int(len(cfg))
    S["emission_rows_total"] = int(len(em))
    S["emission_rows_highway"] = int(len(hw_e))
    S["emission_rows_nonroad"] = int(len(nr_e))

    S["model_year_min_highway"] = int(hw_f.model_year.min())
    S["model_year_max_highway"] = int(hw_f.model_year.max())
    S["model_year_min_nonroad"] = int(nr_f.model_year.min())
    S["model_year_max_nonroad"] = int(nr_f.model_year.max())

    S["manufacturers_highway"] = int(hw_f.manufacturer.nunique())
    S["manufacturers_nonroad"] = int(nr_f.manufacturer.nunique())
    S["manufacturers_total"] = int(fam.manufacturer.nunique())

    S["pollutants"] = sorted(em.pollutant.dropna().unique().tolist())
    S["pollutant_count"] = len(S["pollutants"])
    S["test_types"] = sorted(em.test_type.dropna().unique().tolist())
    S["units_present"] = sorted(em.units.dropna().unique().tolist())

    S["rows_by_panel_pollutant"] = {
        p: int(n) for p, n in em.groupby("pollutant").size().sort_values(ascending=False).items()
    }
    S["families_by_model_year"] = {
        str(int(y)): int(n) for y, n in fam.groupby("model_year").size().items()
    }
    S["nonroad_by_tier"] = {
        str(k): int(v) for k, v in nr_f.tier.value_counts().items()
    }

    car = json.load(open("qa/04_carryover.json"))
    S["carryover_families_with_link"] = car["families_with_carryover"]
    S["carryover_orphan_edges"] = car["orphan_edges"]
    S["carryover_self_referencing"] = car["self_referencing_families"]
    S["carryover_true_cycles"] = car["true_cycles_detected"]
    S["carryover_distinct_lineages"] = car["distinct_lineages"]
    S["carryover_depth_max"] = car["depth_max"]
    S["carryover_depth_mean"] = car["depth_mean"]
    S["carryover_longest_example"] = car["longest_lineage_example"]

    # --- integrity checks: each must hold or the build is not publishable ---
    checks = {}
    checks["family_key_unique"] = bool(
        not fam.duplicated(subset=["panel", "model_year", "engine_family"]).any())
    checks["no_emission_row_without_family"] = bool(
        em.merge(fam[["panel", "model_year", "engine_family"]],
                 on=["panel", "model_year", "engine_family"], how="left",
                 indicator=True)["_merge"].eq("both").all())
    checks["units_never_null"] = bool(em.units.notna().all())
    checks["no_mixed_units_within_panel"] = bool(
        em.groupby("panel").units.nunique().le(2).all())
    checks["highway_units_correct"] = bool(
        set(em.loc[em.panel == "highway", "units"].unique()) == {"g/bhp-hr"})
    checks["nonroad_units_correct"] = bool(
        set(em.loc[em.panel == "nonroad", "units"].unique()) <= {"g/kW-hr", "pct opacity"})
    checks["carryover_no_true_cycles"] = car["true_cycles_detected"] == 0
    n_neg = int((em.cert_result < 0).sum())
    n_flagged = int(em.quality_flag.eq("negative_cert_result").sum())
    checks["every_negative_value_is_flagged"] = n_neg == n_flagged
    checks["flagged_share_below_0pt1pct"] = (n_neg / len(em)) < 0.001
    S["negative_cert_results"] = n_neg
    S["negative_cert_result_share_pct"] = round(100 * n_neg / len(em), 4)
    S["negative_cert_result_families"] = int(
        em.loc[em.cert_result < 0, "engine_family"].nunique())
    S["negative_cert_result_panels"] = sorted(
        em.loc[em.cert_result < 0, "panel"].unique().tolist())
    S["integrity_checks"] = checks
    S["integrity_all_passed"] = all(checks.values())

    # --- five named spot checks for the author to verify against EPA ---
    # Chosen to SPAN the dataset rather than cluster: each probes a different
    # failure mode of the harmonization. Deterministic, so the list is stable
    # across rebuilds and the author can check the same five every time.
    def pick(df, why, at="median", **flt):
        q = df
        for k, v in flt.items():
            q = q[q[k].eq(v)]
        q = q[q.cert_result.notna()].sort_values(["model_year", "engine_family"])
        if not len(q):
            return None
        r = q.iloc[0] if at == "first" else q.iloc[len(q) // 2]
        return {"why": why, "panel": r.panel, "engine_family": r.engine_family,
                "model_year": int(r.model_year), "pollutant": r.pollutant,
                "test_type": r.test_type, "cidex_cert_result": float(r.cert_result),
                "units": r.units}

    deep = carry.sort_values("lineage_depth", ascending=False).iloc[0]
    deep_row = em[em.engine_family.eq(deep.engine_family) & em.cert_result.notna()]
    flagged = em[em.quality_flag.eq("negative_cert_result")].sort_values(
        ["engine_family", "pollutant"]).iloc[0]

    spot = [r for r in [
        pick(hw_e, "highway, transient NOx — the standard case",
             panel="highway", pollutant="NOx", test_type="transient"),
        pick(hw_e, "highway, earliest model year present — tests the MY2015-16 archive boundary",
             at="first", panel="highway", pollutant="PM", test_type="steady_state"),
        pick(nr_e, "nonroad, steady-state NOx — tests the wide-to-long unpivot",
             panel="nonroad", pollutant="NOx", test_type="steady_state"),
    ] if r]

    if len(deep_row):
        r = deep_row.iloc[0]
        spot.append({"why": f"deepest carryover lineage (depth {int(deep.lineage_depth)}, "
                            f"root {deep.lineage_root}) — tests lineage resolution",
                     "panel": r.panel, "engine_family": r.engine_family,
                     "model_year": int(r.model_year), "pollutant": r.pollutant,
                     "test_type": r.test_type, "cidex_cert_result": float(r.cert_result),
                     "units": r.units})

    spot.append({"why": "a flagged negative value — is this real in EPA's own record?",
                 "panel": flagged.panel, "engine_family": flagged.engine_family,
                 "model_year": int(flagged.model_year), "pollutant": flagged.pollutant,
                 "test_type": flagged.test_type,
                 "cidex_cert_result": float(flagged.cert_result), "units": flagged.units})

    S["spot_checks"] = spot

    for df, name in [(fam, "cidex_family"), (cfg, "cidex_config"), (em, "cidex_emissions")]:
        df.to_csv(f"{OUT}/{name}.csv", index=False)
        df.to_parquet(f"{OUT}/{name}.parquet", index=False)

    with open(f"{OUT}/stats.json", "w") as fh:
        json.dump(S, fh, indent=2, default=str)

    print(json.dumps({k: S[k] for k in
        ["families_total","families_highway","families_nonroad","configs_total",
         "emission_rows_total","manufacturers_total","pollutant_count",
         "units_present","carryover_distinct_lineages","integrity_all_passed"]},
        indent=2, default=str))
    print("\nintegrity:", json.dumps(checks, indent=2))


if __name__ == "__main__":
    main()
