## Purpose

Defines the per-scene spectral-index computation contract — classes that read
Landsat reflectance bands from a DataCube and write dimensionless index
DataArrays back to the cube. Covers moisture, productivity, and salinity
indices; vegetation-health indices (NDVI/EVI/LAI/SAVI/FVC) are governed by
the vegetation pipeline stage and not restated here.

## ADDED Requirements

### Requirement: NDMI — Normalized Difference Moisture Index
The `NDMI` class SHALL compute:

    NDMI = (nir08 − swir16) / (nir08 + swir16)

Required bands: `nir08`, `swir16`.

The result SHALL be an `xr.DataArray` named `ndmi` with:
- `long_name`: "Normalized Difference Moisture Index"
- `units`: "dimensionless"
- `range`: "[-1, 1]"

Invalid pixels (denominator == 0 or non-finite input) SHALL be set to NaN.

#### Scenario: NDMI on valid Landsat data
- **WHEN** a DataCube contains `nir08` and `swir16` with finite values
- **THEN** `ndmi` is written to the cube with values in [-1, 1]

#### Scenario: NDMI missing bands raises
- **WHEN** `compute(cube)` is called without `swir16`
- **THEN** `ValueError` is raised listing the missing band

---

### Requirement: MSI — Moisture Stress Index
The `MSI` class SHALL compute:

    MSI = swir16 / nir08

Required bands: `nir08`, `swir16`.

The result SHALL be an `xr.DataArray` named `msi` with:
- `long_name`: "Moisture Stress Index"
- `units`: "dimensionless"
- Higher values indicate stronger moisture stress

Invalid pixels SHALL be NaN.

#### Scenario: MSI on bare soil
- **WHEN** nir08 is low and swir16 is moderate (dry soil)
- **THEN** MSI value is > 1.0

---

### Requirement: NMDI — Normalized Multi-band Drought Index
The `NMDI` class SHALL compute:

    NMDI = (nir08 − (swir16 − swir22)) / (nir08 + (swir16 − swir22))

Required bands: `nir08`, `swir16`, `swir22`.

The result SHALL be an `xr.DataArray` named `nmdi` with:
- `long_name`: "Normalized Multi-band Drought Index"
- `units`: "dimensionless"
- `range`: "[-1, 1]"

#### Scenario: NMDI needs three SWIR bands
- **WHEN** `swir22` is absent from the DataCube
- **THEN** `ValueError` lists `swir22` as missing

---

### Requirement: NIRv — Near-Infrared Reflectance of Vegetation
The `NIRv` class SHALL compute:

    NIRv = ndvi × nir08

Required bands: `ndvi` (pre-computed), `nir08`.

The result SHALL be an `xr.DataArray` named `nirv` with:
- `long_name`: "Near-Infrared Reflectance of Vegetation"
- `units`: "dimensionless × reflectance" (typically ~0–0.5)
- One of the strongest simple predictors of GPP and biomass

#### Scenario: NIRv uses cube's existing NDVI
- **WHEN** `ndvi` is already in the cube
- **THEN** NIRv reads it directly rather than recomputing

---

### Requirement: GCI — Green Chlorophyll Index
The `GCI` class SHALL compute:

    GCI = (nir08 / green) − 1

Required bands: `nir08`, `green`.

The result SHALL be an `xr.DataArray` named `gci` with:
- `long_name`: "Green Chlorophyll Index"
- `units`: "dimensionless"
- Useful for chlorophyll and nitrogen status assessment

Invalid pixels (zero or negative green) SHALL be NaN.

#### Scenario: GCI on dense vegetation
- **WHEN** green reflectance is low and nir08 is high
- **THEN** GCI > 2.0

---

### Requirement: NDSI — Normalized Difference Salinity Index
The `NDSI` class SHALL compute:

    NDSI = (red − nir08) / (red + nir08)

Required bands: `red`, `nir08`.

The result SHALL be an `xr.DataArray` named `ndsi` with:
- `long_name`: "Normalized Difference Salinity Index"
- `units`: "dimensionless"
- `range`: "[-1, 1]"
- Positive values indicate saline/urban surfaces; negative values indicate healthy vegetation

#### Scenario: NDSI on saline soil
- **WHEN** red > nir08 (bright saline surface)
- **THEN** NDSI is positive

---

### Requirement: SI_T — Soil Salinity Index (geometric mean)
The `SI_T` class SHALL compute:

    SI_T = sqrt(red × swir16)

Required bands: `red`, `swir16`.

The result SHALL be an `xr.DataArray` named `si_t` with:
- `long_name`: "Soil Salinity Index (geometric mean variant)"
- `units`: "reflectance-scaled" (not dimensionless — square-root of product)
- More useful for agricultural soils than NDSI

Invalid pixels SHALL be NaN.

#### Scenario: SI_T on bare soil
- **WHEN** both red and swir16 are positive
- **THEN** SI_T is a positive real number
