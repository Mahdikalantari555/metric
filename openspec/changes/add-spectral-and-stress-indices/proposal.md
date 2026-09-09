## Why

The METRIC pipeline currently computes only NDVI-derived vegetation indices and two stress indices (CWSI_LST, TVDI). Researchers need a complete set of spectral, moisture, productivity, and climatological stress indices to support drought monitoring and crop-health workflows — not scattered hand-computations after the fact.

## What Changes

- Add six new source modules under `metric_et/surface/`: `moisture.py`, `stress.py`, `temporal_stress.py`, `productivity.py`, `salinity.py`. (Rename `indices.py` → `stress.py`; remove unused alias block.)
- Migrate `CWSI_LST` and `TVDI` classes from `indices.py` into `stress.py`; add `CWSI_ET` and `VSWI` to the same module.
- Add per-scene index classes: `NDMI`, `MSI`, `NMDI`, `NIRv`, `GCI`, `NDSI`, `SI_T` across their respective modules.
- Add temporal-stress classes (`TCI`, `VCI`, `VHI`) that accumulate min/max LST and NDVI across scenes during `_calculate_et_all()`, then compute in a new `_compute_temporal_indices()` workflow step inserted before `_interpolate_et()`.
- Restructure `OUTPUT_PRODUCTS` in `settings.py` into seven named categories: `et_core`, `energy_balance`, `quality`, `surface_props`, `radiation`, `spectral_indices`, `stress_indices`.
- Narrow `OUTPUT_PRESETS` to three entries (`minimal`, `standard`, `full`); deprecate the older granular presets (`et_only`, `with_quality`, `research`).
- Update `run_metric_workflow.py` constructor to accept `output_categories` (list of category strings) replacing the old boolean `include_surface` flag.
- Update `pipeline-architecture` stage 3 to document the new per-scene index computation step alongside existing surface-property stages.

## Capabilities

### New Capabilities
- `spectral-indices`: Per-scene computation of NDVI, SAVI, EVI, NDMI, MSI, NMDI, NIRv, GCI, NDSI, SI_T via the `DataCube` band contract. Each class exposes `compute(cube)` and returns an `xr.DataArray` with standardized attributes.
- `stress-indices`: Per-scene stress indicators (CWSI_ET, CWSI_LST, TVDI, VSWI) computed from NDVI/LST or ET products already in the cube. VSWI = NDVI / LST (documented units).
- `temporal-stress`: TCI, VCI, and VHI computed from multi-scene accumulated min/max LST and NDVI. Requires a new `_compute_temporal_indices()` workflow step called after `_calculate_et_all()` and before `_interpolate_et()`.
- `output-taxonomy`: OUTPUT_PRODUCTS split into discrete categories; OUTPUT_PRESETS collapsed to `minimal`, `standard`, `full`; new `output_categories` parameter on `METRICWorkflow`.

### Modified Capabilities
- `datacube-contract`: Extend derived-band list to include new snake_case band names (`ndmi`, `msi`, `nmdi`, `nirv`, `gci`, `ndsi`, `si_t`, `cwsi_et`, `tc i`, `vci`, `vhi`).
- `pipeline-architecture`: Insert a new Stage 3b (`calculate_spectral_indices`) and a new workflow-level step (`_compute_temporal_indices`) between scene processing and ET interpolation.
- `output-layout`: Document new product directories for `spectral_indices` and `stress_indices` categories.

## Impact

- **Breaking**: `OUTPUT_PRESETS` keys change — `et_only`, `with_quality`, `research` removed; callers using these exact preset names must update.
- **Breaking**: `METRICWorkflow.include_surface` flag replaced by `output_categories` list. Existing CLI/scripts passing `--include-surface` must migrate.
- No changes to existing band contracts — all new indices use bands already present (`blue`, `green`, `red`, `nir08`, `swir16`, `swir22`, `lwir11`).
- CWSI_ET computation location unchanged (stays inside the ET pipeline).
- `LAI` and `FVC` remain in `surface_props`, not moved to `spectral_indices`.
