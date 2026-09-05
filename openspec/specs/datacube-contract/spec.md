# datacube-contract Specification

## Purpose
Defines the canonical band names, metadata keys, and data-type expectations
for `DataCube` so that every stage in the pipeline agrees on naming.

## Requirements

### Requirement: Canonical Landsat band names
The DataCube SHALL use the following band names (matching
`LandsatReader.BAND_MAPPING`):

| Band name | Description |
|-----------|-------------|
| blue | Coastal / blue aerosol |
| green | Green |
| red | Red |
| nir08 | Near-infrared (L8/9 Band 5) |
| swir16 | Shortwave infrared 1.6 µm |
| swir22 | Shortwave infrared 2.2 µm |
| lwir11 | Thermal infrared 10.9–12.5 µm (brightness temp) |
| qa | Quality band (optional) |
| qa_pixel | Pixel QA band (optional) |

Derived bands SHALL use snake_case:
`ndvi`, `evi`, `lai`, `savi`, `fvc`, `albedo`, `emissivity`,
`lst`, `z0m`, `Rs_down`, `R_l_down`, `R_ns`, `R_nl`, `R_n`, `H`, `G`, `LE`,
`ET_inst`, `ETrF`, `ET_daily`.

#### Scenario: Surface properties read by name
- **WHEN** `VegetationIndices.compute()` runs
- **THEN** it reads `cube.get("red")` and `cube.get("nir08")` — not aliases

### Requirement: Metadata keys
`cube.metadata` SHALL carry at least:

| Key | Type | Description |
|-----|------|-------------|
| scene_id | str | Landsat product ID |
| platform | str | e.g. `landsat-8`, `landsat-9` |
| sensor | str | e.g. `oli`, `etm`, `oli_tirs` |
| sun_elevation | float | degrees |
| sun_azimuth | float | degrees |
| air_temperature | float | 2-m air temperature (K) |
| cloud_cover | float | percent (0–100) |
| dt_a | float | Calibration slope (W/m²/K) |
| dt_b | float | Calibration intercept (K) |

#### Scenario: Calibration reads air_temperature
- **WHEN** `SensibleHeatFlux.compute()` runs
- **THEN** it reads `cube.get("temperature_2m")` which is populated from `air_temperature` metadata during `load_data()`

### Requirement: Numeric arrays are float64 or float32
All raster bands SHALL be `xarray.DataArray` backed by `numpy.float32` or
`numpy.float64`. Integer masks (e.g. cloud QA) MAY use `int16`/`int32`.
Scalar metadata values MAY be plain Python `float` or `int`.

#### Scenario: Mixed dtype accepted
- **WHEN** a band is stored as `np.float32`
- **THEN** downstream `np.asarray(..., dtype=np.float64)` coercion still works
