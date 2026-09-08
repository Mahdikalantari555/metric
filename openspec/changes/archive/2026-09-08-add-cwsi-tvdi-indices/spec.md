# Surface indices specification

## Requirement: CWSI_LST index
The module SHALL provide `CWSI_LSTCalculator`.

- Inputs: `lst` and `ndvi` DataArrays.
- Edge estimation: NDVI binning + per-bin quantile lookup + `np.interp`.
- Wet edge: `LST_wet = Q_0.05(LST | NDVI)` per bin.
- Dry edge: `LST_dry = Q_0.95(LST | NDVI)` per bin.
- Formula: `CWSI_LST = (LST - LST_wet) / (LST_dry - LST_wet)`.
- Default clip to `[0, 1]`.
- Raise if required bands are missing.
- Constructor params:
  - `wet_quantile: float = 0.05`
  - `dry_quantile: float = 0.95`
  - `ndvi_bin_width: float = 0.02`
  - `ndvi_min: float = 0.2`
  - `ndvi_max: float = 0.9`
  - `clip: bool = True`
- Future: support `method="quantile_regression"` as alternative to binning.

## Requirement: TVDI index
The module SHALL provide `TVDICalculator`.

- Inputs: `lst` and `ndvi` DataArrays.
- Edge estimation: NDVI binning + per-bin 95th quantile + `np.polyfit` for dry edge.
- Dry edge: `LST_max = a + b * NDVI` fit to per-bin 95th percentile points.
- Wet edge: `LST_min` at `wet_quantile` (default 0.05).
- Formula: `TVDI = (LST - LST_min) / (LST_max - LST_min)`.
- Default clip to `[0, 1]`.
- Raise if required bands are missing.
- Constructor params:
  - `dry_quantile: float = 0.95`
  - `wet_quantile: float = 0.05`
  - `ndvi_bin_width: float = 0.02`
  - `ndvi_min: float = 0.2`
  - `ndvi_max: float = 0.9`
  - `clip: bool = True`

## Requirement: DataCube contract compliance
New indices SHALL read bands via `cube.get("lst")` and `cube.get("ndvi")` and SHALL return `xr.DataArray` with `name` and `attrs`.

## Requirement: Derived band names
Derived bands SHALL use snake_case: `cwsi_lst`, `tvdi`.

## Requirement: Existing CWSI rename
The existing ET-based `CWSI` band SHALL be renamed to `CWSI_ET` to distinguish it from the new `CWSI_LST` index.

Affected files:
- `metric_et/pipeline/metric_pipeline.py` — band name in calculation and `get_results()`
- `metric_et/output/writer.py` — output group, metadata key, config
- `metric_et/config/settings.py` — band list entries
- `metric_et/output/product_organizer.py` — regex pattern
