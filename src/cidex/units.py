"""Unit handling for CIDEX.

D2: CIDEX performs no silent unit conversion. The highway panel is certified in
g/bhp-hr and the nonroad panel in g/kW-hr. Comparing them numerically without
conversion is invalid. Conversion is available but must be called deliberately.
"""

# 1 hp (mechanical) = 0.7456998716 kW
# A rate in g/bhp-hr converts to g/kW-hr by dividing by kW per hp.
HP_TO_KW = 0.7456998716


class MixedUnitsError(ValueError):
    """Raised when an operation would silently combine incompatible units."""


def to_g_per_kWh(value, from_units):
    """Convert an emission rate to g/kW-hr. Explicit by design."""
    if from_units == "g/kW-hr":
        return value
    if from_units == "g/bhp-hr":
        return value / HP_TO_KW
    raise ValueError(f"unknown units: {from_units!r}")


def headroom(df, result_col="cert_result", standard_col="standard",
             units_col="units"):
    """Compute standard - cert_result, refusing to operate across unit systems.

    D4: this is deliberately NOT a column in the published dataset. A margin
    column sitting beside two unit systems invites a plausible, wrong number.
    """
    present = set(df[units_col].dropna().unique())
    if len(present) > 1:
        raise MixedUnitsError(
            f"refusing to compute headroom across mixed units: {sorted(present)}. "
            "Convert with to_g_per_kWh() first, or filter to one panel."
        )
    return df[standard_col] - df[result_col]
