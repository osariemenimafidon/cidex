# CIDEX Codebook

> **DRAFT — NOT VERIFIED.** This package has not passed its verification gate. No number in it has been checked against the primary source by the author. Do not cite, deposit, or redistribute.

Version 1.0 · built 2026-09-15

CIDEX is distributed as four tables. The unit of analysis for emissions is
**(model year, engine family, pollutant, test type)**. Family-level attributes and
configuration-level attributes are separated, because configuration attributes vary
*within* a family and keeping them together would force an arbitrary row to win.

## Keys

`(panel, model_year, engine_family)` uniquely identifies a family. The engine family
name already encodes the model year, so it is a true key rather than a surrogate.

## Units — read this before comparing anything

Three unit systems travel in the `units` column:

| Panel / measure | Units |
|---|---|
| Highway certification results | `g/bhp-hr` |
| Nonroad certification results | `g/kW-hr` |
| Smoke opacity (nonroad) | `pct opacity` |

**CIDEX performs no unit conversion.** Comparing a highway `cert_result` to a nonroad
`cert_result` without converting is invalid and will produce a plausible, wrong number.
Convert deliberately:

```python
from cidex.units import to_g_per_kWh
to_g_per_kWh(0.20, "g/bhp-hr")   # -> 0.2682 g/kW-hr
```

`cidex.units.headroom()` raises `MixedUnitsError` rather than computing across panels.

## Pollutant vocabulary

`NMHCE` (Non-Methane Hydrocarbon Equivalent) is deliberately **not** folded into `NMHC`.
It is a different regulatory construct; folding would destroy information that cannot be
reconstructed.

| Pollutant | Rows |
|---|---|
| `CH4` | 7,456 |
| `CO` | 14,238 |
| `CO2` | 13,196 |
| `HCHO` | 503 |
| `N2O` | 4,700 |
| `NH3` | 3 |
| `NMHC` | 14,219 |
| `NMHCE` | 13 |
| `NMHC_NOx` | 6,712 |
| `NOx` | 14,238 |
| `PM` | 14,190 |
| `smoke_accel` | 1,853 |
| `smoke_lug` | 1,763 |
| `smoke_peak` | 1,785 |

## Tables

### `cidex_family.csv`

8,627 rows.

| Column | Type | Description |
|---|---|---|
| `panel` | string | Which EPA source the row came from: `highway` or `nonroad`. |
| `manufacturer` | string | Certificate holder, as EPA spells it. Not normalised across years. |
| `model_year` | integer | Certification model year. |
| `engine_family` | string | EPA engine family name. Unique per model year; the first character encodes the model year. |
| `certificate_no` | string | EPA certificate number. |
| `date_issued` | date | Date the certificate was issued. |
| `engine_cycle` | string | Combustion cycle. |
| `fuel_type` | string | Certification fuel type, source spelling. |
| `fuel_metering_system` | string | Fuel metering system. |
| `introduction_date` | date | Date of introduction into commerce. |
| `useful_life` | string | Useful life as EPA states it; free text, units vary by panel. |
| `intended_service_class` | string | Highway only. Service class, e.g. Heavy Heavy-Duty Diesel. |
| `carryover_family` | string | Nonroad only. Family this one was carried over from; null if none. |
| `power_category` | string | Nonroad only. Power band, e.g. `130<=kW<=560`. |
| `regulation` | string | Nonroad only. Applicable regulation. |
| `tier` | string | Nonroad only. Applicable emission tier. |
| `compliance_standard` | string | Nonroad only. Applicable compliance standard, family level, not pollutant-specific. |
| `non_aftertreatment_device` | string | Nonroad only. Non-aftertreatment devices, semicolon separated. |
| `aftertreatment_device` | string | Nonroad only. Aftertreatment devices, semicolon separated. |
| `year_coverage` | string | — |

### `cidex_config.csv`

9,794 rows.

| Column | Type | Description |
|---|---|---|
| `panel` | string | Which EPA source the row came from: `highway` or `nonroad`. |
| `model_year` | integer | Certification model year. |
| `engine_family` | string | EPA engine family name. Unique per model year; the first character encodes the model year. |
| `engine_code` | string | Configuration level. Engine code. |
| `engine_test_model` | string | Highway only, configuration level. Test model. |
| `engine_id` | string | Highway only, configuration level. Engine identifier. |
| `test_fuel` | string | Highway only, configuration level. |
| `test_date` | date | Highway only, configuration level. |
| `engine_model` | string | Configuration level. Engine model name. |
| `displacement_l` | float | Configuration level. Displacement in litres. |
| `certification_fuel` | string | Configuration level. Fuel used for certification testing. |
| `engine_operation` | string | Nonroad only, configuration level. |
| `test_procedure` | string | Nonroad only, configuration level. |
| `test_procedure_type` | string | Nonroad only, configuration level. |

### `cidex_emissions.csv`

94,869 rows.

| Column | Type | Description |
|---|---|---|
| `panel` | string | Which EPA source the row came from: `highway` or `nonroad`. |
| `model_year` | integer | Certification model year. |
| `engine_family` | string | EPA engine family name. Unique per model year; the first character encodes the model year. |
| `engine_code` | string | Configuration level. Engine code. |
| `engine_test_model` | string | Highway only, configuration level. Test model. |
| `pollutant` | string | Controlled vocabulary. See the pollutant table below. |
| `test_type` | string | `transient`, `steady_state`, or `smoke`. |
| `cert_result` | float | Certification result. **Units are given by the `units` column and differ between panels.** |
| `adj_result` | float | Highway only. Deterioration-adjusted result. Null for nonroad. |
| `standard` | float | Highway only. Applicable standard for this pollutant and test type. Null for nonroad — see LIMITATIONS. |
| `fel` | float | Family Emission Limit where the family certified to one. Null is not zero. |
| `fcl` | float | Highway only. Family Certification Level. |
| `df_type` | string | Highway only. Deterioration factor type. |
| `df_value` | float | Highway only. Deterioration factor value. |
| `units` | string | `g/bhp-hr` (highway), `g/kW-hr` (nonroad), or `pct opacity` (smoke). Never null. |
| `quality_flag` | string | Null, or `negative_cert_result`. See LIMITATIONS. |
| `year_coverage` | string | — |

### `cidex_carryover.csv`

7,925 rows.

| Column | Type | Description |
|---|---|---|
| `panel` | string | Which EPA source the row came from: `highway` or `nonroad`. |
| `model_year` | integer | Certification model year. |
| `engine_family` | string | EPA engine family name. Unique per model year; the first character encodes the model year. |
| `carryover_family` | string | Nonroad only. Family this one was carried over from; null if none. |
| `lineage_root` | string | Oldest family reachable through the carryover chain. |
| `lineage_depth` | integer | Number of carryover steps to the lineage root. 0 = starts its own lineage. |

