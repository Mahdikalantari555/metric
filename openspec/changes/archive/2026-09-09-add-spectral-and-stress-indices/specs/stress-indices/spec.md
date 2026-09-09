## Purpose

Defines the per-scene stress-index computation contract. Stress indices combine
multiple physical variables (NDVI, LST, ET products) into dimensionless
indicators of crop water stress. Includes CWSI_ET (pipeline-derived),
CWSI_LST (feature-space), TVDI (feature-space), and VSWI (instantaneous).

## ADDED Requirements

### Requirement: CWSI_ET — Crop Water Stress Index from ET ratio
The `CWSI_ET` indicator SHALL be computed within the ET pipeline as:

    CWSI_ET = 1 − (ET_inst / ETrF_inst)

where `ET_inst` is the instantaneous actual evapotranspiration and
`ETrF_inst` is the reference transpiration factor, both produced by the
existing ET calculation stage.

The result SHALL be an `xr.DataArray` named `CWSI_ET` (preserving the
existing naming convention in the pipeline) with:
- `long_name`: "Crop Water Stress Index (ET-ratio method)"
- `units`: "dimensionless"
- `range`: "[0, 1]" — 0 = well-watered, 1 = maximum stress

This computation SHALL remain inside `calculate_et()` in the METRIC pipeline
and is NOT moved to the stress.py module.

#### Scenario: Well-watered scene
- **WHEN** ET_inst ≈ ETrF_inst
- **THEN** CWSI_ET ≈ 0

#### Scenario: Stressed scene
- **WHEN** ET_inst << ETrF_inst
- **THEN** CWSI_ET approaches 1.0

---

### Requirement: CWSI_LST — Crop Water Stress Index from NDVI-LST feature space
The `CWSILSTCalculator` class SHALL compute CWSI using the NDVI-LST
binning method (migrated from `indices.py`).

Formula:
    CWSI_LST = (LST − LST_wet) / (LST_dry − LST_wet)

where LST_wet and LST_dry are interpolated from per-NDVI-bin quantiles
(wet_quantile=0.05, dry_quantile=0.95).

Required bands: `ndvi`, `lst`.

The result SHALL be an `xr.DataArray` named `cwsi_lst` with:
- `long_name`: "Crop Water Stress Index (NDVI-LST feature space)"
- `units`: "dimensionless"
- `range`: "[0, 1]"

Parameters (configurable): `wet_quantile=0.05`, `dry_quantile=0.95`,
`ndvi_bin_width=0.02`, `ndvi_min=0.2`, `ndvi_max=0.9`, `clip=True`.

#### Scenario: Insufficient bins raises
- **WHEN** fewer than 2 valid NDVI bins exist
- **THEN** `ValueError` is raised

#### Scenario: Clip defaults to [0, 1]
- **WHEN** `clip=True` (default)
- **THEN** out-of-range values are clamped

---

### Requirement: TVDI — Temperature Vegetation Dryness Index
The `TVDICalculator` class SHALL compute TVDI using a polyfit dry-edge
model (migrated from `indices.py`).

Formula:
    TVDI = (LST − LST_min) / (LST_max − LST_min)

where LST_min = global wet-edge quantile and LST_max = a + b·NDVI fitted
to per-bin dry quantiles.

Required bands: `ndvi`, `lst`.

The result SHALL be an `xr.DataArray` named `tvdi` with:
- `long_name`: "Temperature Vegetation Dryness Index"
- `units`: "dimensionless"
- `range`: "[0, 1]"

#### Scenario: TVDI dry edge fit
- **WHEN** ≥ 2 valid NDVI bins with LST data
- **THEN** a linear polyfit is applied to estimate LST_max per NDVI bin

---

### Requirement: VSWI — Vegetation Supply Water Index
The `VSWI` class SHALL compute the instantaneous vegetation supply water
index:

    VSWI = NDVI / LST

Required bands: `ndvi`, `lst`.

The result SHALL be an `xr.DataArray` named `vswi` with:
- `long_name`: "Vegetation Supply Water Index"
- `units`: "dimensionless (NDVI / LST_K)"
- Expected LST units: Kelvin. Document this in attributes.

Some papers multiply by 1000 or use Celsius; this implementation uses the
basic form with LST in Kelvin. The caller is responsible for ensuring LST
is in Kelvin before invoking VSWI.

Invalid pixels (zero LST or non-finite input) SHALL be NaN.

#### Scenario: VSWI unit documentation
- **WHEN** `compute(cube)` returns the VSWI DataArray
- **THEN** attrs include `lst_units: "K"` documenting the expected input unit
