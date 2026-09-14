"""Controlled vocabulary for CIDEX pollutant names and test types."""

# Highway 'Pollutant Name' values -> CIDEX controlled vocabulary.
# D3: 'Non-Methane Hydrocarbon Equivalent' is kept DISTINCT from NMHC.
POLLUTANT_MAP = {
    "Nitrogen Oxides": "NOx",
    "Carbon Monoxide": "CO",
    "Non-Methane Hydrocarbons": "NMHC",
    "Non-Methane Hydrocarbon Equivalent": "NMHCE",
    "Particulate Matter": "PM",
    "Carbon Dioxide": "CO2",
    "Methane": "CH4",
    "Nitrous Oxide": "N2O",
    "Formaldehyde": "HCHO",
    "Ammonia": "NH3",
}

# Nonroad wide-format column labels (row-2 subheader) -> controlled vocabulary.
NONROAD_POLLUTANT_MAP = {
    "NMHC": "NMHC",
    "NOx": "NOx",
    "NMHC+NOx": "NMHC_NOx",
    "CO": "CO",
    "PM": "PM",
    "CO2": "CO2",
    "N2O": "N2O",
    "CH4": "CH4",
}

# Nonroad row-1 group headers -> CIDEX test_type.
NONROAD_GROUP_MAP = {
    "Certification Level Steady-State Discrete Modal": "steady_state",
    "Certification Level Transient Test Results": "transient",
    "FEL": "fel",
    "Smoke Opacity": "smoke",
}

TEST_TYPES = ("transient", "steady_state", "fel", "smoke")

PANEL_UNITS = {
    "highway": "g/bhp-hr",
    "nonroad": "g/kW-hr",
}
