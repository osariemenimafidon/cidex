"""03 — Harmonize the EPA nonroad CI panel into CIDEX long form.

Source shape: WIDE. A two-level header (row 1 = measurement group, row 2 =
pollutant) spreads ~24 measurement columns across four groups, and family
attributes appear both BEFORE and AFTER the measurement blocks.

Column blocks are not hard-coded by index. The group row is forward-filled, then
a column counts as a measurement only if its sub-name is one the group actually
contains. That is what keeps 'Engine Model' (which sits immediately after the FEL
block and inherits its filled group) classified as an attribute, not a pollutant.
"""
import sys, os, json, re
import pandas as pd
sys.path.insert(0, "src")
from cidex.vocab import NONROAD_POLLUTANT_MAP

SRC = "data/raw/nonroad-compression-ignition-2011-present.xlsx"
OUT = "data/processed"

POLLUTANT_SUBS = set(NONROAD_POLLUTANT_MAP)
SMOKE_SUBS = {"Acceleration": "smoke_accel", "LUG": "smoke_lug", "Peak": "smoke_peak"}

# group keyword -> (test_type, allowed sub-names, units)
GROUPS = [
    ("steady-state", "steady_state", POLLUTANT_SUBS, "g/kW-hr"),
    ("transient",    "transient",    POLLUTANT_SUBS, "g/kW-hr"),
    ("smoke",        "smoke",        set(SMOKE_SUBS), "pct opacity"),
    ("fel",          "fel",          POLLUTANT_SUBS, "g/kW-hr"),
]

ATTR_MAP = {
    "Model Year": "model_year", "Engine Family": "engine_family",
    "Manufacturer": "manufacturer", "Certificate #": "certificate_no",
    "Issue Date": "date_issued", "Commerce Introduction Date": "introduction_date",
    "Carryover Engine Family Name": "carryover_family",
    "Power Category": "power_category", "Applicatable Regulation": "regulation",
    "Applicable Tier": "tier", "Applicable Compliance Standard": "compliance_standard",
    "Fuel": "fuel_type", "Fuel Meter System": "fuel_metering_system",
    "Useful Life of Engine Family": "useful_life",
    "Engine Combustion Cycle": "engine_cycle",
    "Non Aftertreatment Device Type": "non_aftertreatment_device",
    "Aftertreatment Device Type": "aftertreatment_device",
    "Engine Model": "engine_model", "Engine Code": "engine_code",
    "Displacement": "displacement_l", "Certification Fuel": "certification_fuel",
    "Engine Operation": "engine_operation", "Test Procedure": "test_procedure",
    "Test Type": "test_procedure_type",
}


def classify_columns():
    hdr = pd.read_excel(SRC, sheet_name="Family Info", header=None, nrows=2)
    groups, subs = [], []
    current = None
    for i in range(hdr.shape[1]):
        g, s = hdr.iloc[0, i], hdr.iloc[1, i]
        if isinstance(g, str) and g.strip():
            current = g.strip()
        groups.append(current)
        subs.append(str(s).strip() if pd.notna(s) else None)

    measures, attrs = [], []
    for i, (g, s) in enumerate(zip(groups, subs)):
        if s is None:
            continue
        matched = None
        if g:
            gl = g.lower()
            for kw, test_type, allowed, units in GROUPS:
                if kw in gl and s in allowed:
                    matched = (test_type, units)
                    break
        if matched:
            measures.append((i, s, *matched))
        else:
            attrs.append((i, s))
    return measures, attrs


def main():
    os.makedirs(OUT, exist_ok=True)
    report = {}
    measures, attrs = classify_columns()
    report["measurement_columns"] = len(measures)
    report["attribute_columns"] = len(attrs)

    df = pd.read_excel(SRC, sheet_name="Family Info", header=None, skiprows=2)
    df = df.dropna(how="all")
    report["source_rows"] = len(df)

    # --- family dimension ---
    fam = pd.DataFrame()
    unmapped_attrs = []
    for i, s in attrs:
        key = ATTR_MAP.get(s) or ATTR_MAP.get(s.rstrip())
        if key is None:
            unmapped_attrs.append(s); continue
        fam[key] = df[i]
    report["unmapped_attribute_columns"] = unmapped_attrs

    # Attributes that vary WITHIN a family describe an engine configuration, not
    # the family. Keeping them in the family table would force an arbitrary
    # "first row wins" choice and silently discard the rest. They go to their own
    # table instead; the conflict test below is what proves the split is right.
    CONFIG_ATTRS = ["engine_model", "engine_code", "displacement_l",
                    "certification_fuel", "engine_operation",
                    "test_procedure", "test_procedure_type"]

    conflicts = {}
    g = fam.groupby(["model_year", "engine_family"], dropna=False)
    for col in fam.columns:
        if col in ("model_year", "engine_family"):
            continue
        bad = int((g[col].nunique(dropna=True) > 1).sum())
        if bad:
            conflicts[col] = bad
    report["attr_conflicts_before_split"] = conflicts

    cfg_cols = [c for c in CONFIG_ATTRS if c in fam.columns]
    cfg = fam[["model_year", "engine_family"] + cfg_cols].drop_duplicates()
    cfg.insert(0, "panel", "nonroad")
    report["config_rows"] = len(cfg)

    fam = fam.drop(columns=cfg_cols)
    residual = {}
    g2 = fam.groupby(["model_year", "engine_family"], dropna=False)
    for col in fam.columns:
        if col in ("model_year", "engine_family"):
            continue
        bad = int((g2[col].nunique(dropna=True) > 1).sum())
        if bad:
            residual[col] = bad
    report["family_attr_conflicts_after_split"] = residual
    if residual:
        raise SystemExit(f"Family table still not family-level: {residual}")

    fam = fam.drop_duplicates(subset=["model_year", "engine_family"], keep="first")
    fam.insert(0, "panel", "nonroad")

    # --- emissions, wide -> long ---
    frames = []
    for i, sub, test_type, units in measures:
        pol = NONROAD_POLLUTANT_MAP.get(sub) or SMOKE_SUBS.get(sub)
        block = pd.DataFrame({
            "panel": "nonroad",
            "model_year": df[0],
            "engine_family": df[1],
            "engine_code": df[40] if 40 in df.columns else pd.NA,
            "engine_test_model": pd.NA,
            "pollutant": pol,
            "test_type": test_type,
            "cert_result": pd.to_numeric(df[i], errors="coerce"),
            "units": units,
        })
        frames.append(block)

    em = pd.concat(frames, ignore_index=True)
    before = len(em)
    em = em[em["cert_result"].notna()].copy()
    report["long_rows_before"] = before
    report["long_empty_dropped"] = before - len(em)

    # FEL is a limit, not a measured result: move it to its own column.
    fel = em[em["test_type"] == "fel"][
        ["model_year", "engine_family", "pollutant", "cert_result"]
    ].rename(columns={"cert_result": "fel"})
    em = em[em["test_type"] != "fel"].copy()
    em = em.merge(fel, on=["model_year", "engine_family", "pollutant"], how="left")
    report["fel_values"] = len(fel)

    # Standards come from the family-level compliance standard string, which is
    # not pollutant-specific. Left null rather than guessed. [VERIFY]
    em["standard"] = pd.NA
    em["adj_result"] = pd.NA
    em["fcl"] = pd.NA

    report["family_rows"] = len(fam)
    report["emission_rows"] = len(em)
    cfg.to_csv(f"{OUT}/nonroad_config.csv", index=False)
    fam.to_csv(f"{OUT}/nonroad_family.csv", index=False)
    em.to_csv(f"{OUT}/nonroad_emissions.csv", index=False)
    with open("qa/03_nonroad.json", "w") as fh:
        json.dump(report, fh, indent=2, default=str)
    print(json.dumps(report, indent=2, default=str))


if __name__ == "__main__":
    main()
