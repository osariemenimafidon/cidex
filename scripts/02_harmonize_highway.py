"""02 — Harmonize the EPA heavy-duty highway panel into CIDEX long form.

Source shape: LONG on pollutant (a 'Pollutant Name' column) but WIDE on test
type (separate transient and steady-state column blocks). CIDEX unpivots the
test-type block so the unit of analysis is (MY, family, pollutant, test_type).

Header is on row 2 of the sheet (row 1 is a merged group header).
"""
import sys, os, json
import pandas as pd
sys.path.insert(0, "src")
from cidex.vocab import POLLUTANT_MAP, PANEL_UNITS

SRC = "data/raw/heavy-duty-gas-and-diesel-engines-2015-present.xlsx"
OUT = "data/processed"

FAMILY_COLS = {
    "Manufacturer": "manufacturer",
    "Model Year": "model_year",
    "Engine Family": "engine_family",
    "Certificate No.": "certificate_no",
    "Date Issued": "date_issued",
    "Engine Cycle": "engine_cycle",
    "Fuel Type": "fuel_type",
    "Fuel Metering System": "fuel_metering_system",
    "Introduction Date": "introduction_date",
    "Useful Life": "useful_life",
    "Intended Service Class": "intended_service_class",
}

TEST_BLOCKS = {
    "transient": {
        "cert_result": "TR Cert Result",
        "adj_result": "Transient (TR) Comb Adj Result",
        "standard": "Transient Standard",
        "fel": "Transient FEL",
        "fcl": "Transient FCL",
    },
    "steady_state": {
        "cert_result": "SS Cert Result",
        "adj_result": "Steady State (SS) Adj Result",
        "standard": "SS Standard",
        "fel": "SS FEL",
        "fcl": "SS FCL",
    },
}


def load():
    df = pd.read_excel(SRC, sheet_name="Family Info", header=1)
    df.columns = [str(c).strip() for c in df.columns]
    df = df.dropna(how="all").dropna(axis=1, how="all")
    return df


def build_family(df, report):
    keep = [c for c in FAMILY_COLS if c in df.columns]
    fam = df[keep].rename(columns=FAMILY_COLS)
    # Family attributes should be constant within (model_year, engine_family).
    # Report any that are not rather than silently taking the first.
    conflicts = {}
    g = fam.groupby(["model_year", "engine_family"], dropna=False)
    for col in fam.columns:
        if col in ("model_year", "engine_family"):
            continue
        n = g[col].nunique(dropna=True)
        bad = int((n > 1).sum())
        if bad:
            conflicts[col] = bad
    report["family_attr_conflicts"] = conflicts
    fam = fam.drop_duplicates(subset=["model_year", "engine_family"], keep="first")
    fam.insert(0, "panel", "highway")
    return fam.reset_index(drop=True)


def build_emissions(df, report):
    df = df.copy()
    df["pollutant"] = df["Pollutant Name"].map(POLLUTANT_MAP)
    unmapped = sorted(set(df.loc[df["pollutant"].isna(), "Pollutant Name"].dropna()))
    report["unmapped_pollutants"] = unmapped
    if unmapped:
        raise SystemExit(f"Unmapped pollutant names, refusing to drop silently: {unmapped}")

    frames = []
    for test_type, cols in TEST_BLOCKS.items():
        sub = pd.DataFrame({
            "panel": "highway",
            "model_year": df["Model Year"],
            "engine_family": df["Engine Family"],
            "engine_code": df.get("Engine Code"),
            "engine_test_model": df.get("Engine Test Model"),
            "pollutant": df["pollutant"],
            "test_type": test_type,
        })
        for out_col, src_col in cols.items():
            sub[out_col] = pd.to_numeric(df[src_col], errors="coerce") if src_col in df else pd.NA
        sub["df_type"] = df.get("DF Type")
        sub["df_value"] = pd.to_numeric(df.get("DF Value"), errors="coerce")
        frames.append(sub)

    em = pd.concat(frames, ignore_index=True)
    value_cols = ["cert_result", "adj_result", "standard", "fel", "fcl"]
    before = len(em)
    # A test-type row with no values at all is an artefact of the unpivot, not a fact.
    em = em[em[value_cols].notna().any(axis=1)].copy()
    report["unpivot_rows_before"] = before
    report["unpivot_empty_dropped"] = before - len(em)
    em["units"] = PANEL_UNITS["highway"]
    return em.reset_index(drop=True)


def build_config(df, report):
    """Configuration-level attributes: vary within a family by design."""
    cols = {"Model Year": "model_year", "Engine Family": "engine_family",
            "Engine Code": "engine_code", "Engine Test Model": "engine_test_model",
            "Engine ID": "engine_id", "Test Fuel": "test_fuel",
            "Test Date": "test_date"}
    keep = {k: v for k, v in cols.items() if k in df.columns}
    cfg = df[list(keep)].rename(columns=keep).drop_duplicates()
    cfg.insert(0, "panel", "highway")
    report["config_rows"] = len(cfg)
    return cfg.reset_index(drop=True)


def main():
    os.makedirs(OUT, exist_ok=True)
    report = {}
    df = load()
    report["source_rows"] = len(df)
    fam = build_family(df, report)
    cfg = build_config(df, report)
    em = build_emissions(df, report)
    report["family_rows"] = len(fam)
    report["emission_rows"] = len(em)
    cfg.to_csv(f"{OUT}/highway_config.csv", index=False)
    fam.to_csv(f"{OUT}/highway_family.csv", index=False)
    em.to_csv(f"{OUT}/highway_emissions.csv", index=False)
    with open("qa/02_highway.json", "w") as fh:
        json.dump(report, fh, indent=2, default=str)
    print(json.dumps(report, indent=2, default=str))


if __name__ == "__main__":
    main()
