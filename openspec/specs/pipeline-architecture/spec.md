# pipeline-architecture Specification

## Purpose
Defines the canonical six-stage processing contract for `METRICPipeline` and the
responsibility of each stage. All consumers (CLI, `run_metric_workflow.py`,
tests, notebooks) SHALL respect this ordering so that intermediate DataCube
bands produced by one stage are available to the next.

## Requirements

### Requirement: Six-stage linear pipeline
**Reason**: Spectral index computation must run after surface properties are
available but before radiation balance, so that indices can read raw
reflectance bands without interference from radiation-derived quantities.
**Migration**: Existing stage ordering is preserved; a new Stage 3b is
inserted between stages 3 and 4. Callers that hard-code stage indices must
account for the insertion.

The pipeline SHALL execute, in order:
1. `load_data()` — populate `self.data` DataCube from a Landsat source and
   meteorological inputs
2. `preprocess()` — cloud masking, resampling, ROI clipping
3. `calculate_surface_properties()` — NDVI/EVI/LAI/SAVI/FVC, albedo,
   emissivity, LST, roughness
3b. `calculate_spectral_indices()` — NDMI, MSI, NMDI, NIRv, GCI, NDSI, SI_T
4. `calculate_radiation_balance()` — R_ns, R_nl, R_n
5. `calculate_soil_heat_flux()` — G (calibration-free)
6. `calibrate()` — anchor-pixel selection + dT calibration
7. `calculate_et()` — H, LE, ET_inst, ETrF, ET_daily

No stage SHALL be skipped unless explicitly gated by a quality flag
(e.g. REJECTED scenes still proceed to ET calculation for assessment).

#### Scenario: Normal execution order
- **WHEN** `METRICPipeline.run()` is called
- **THEN** stages 1–7 execute sequentially and each stage logs its start/end
- **THEN** stage 3b executes between stages 3 and 4

#### Scenario: Preprocess failure halts pipeline
- **WHEN** `preprocess()` raises (e.g. all pixels masked by clouds)
- **THEN** the pipeline aborts, logs the error, and re-raises

### Requirement: Stage outputs become next-stage inputs
Each stage SHALL write its outputs as named bands (or metadata fields) on
`self.data`. Downstream stages SHALL read only from the DataCube, not from
stage-local return values.

| Stage | Writes | Reads |
|-------|--------|-------|
| load_data | raw bands, metadata | — |
| preprocess | cloud mask, clipped bands | raw bands |
| surface | ndvi, lai, albedo, emissivity, lst, z0m | preprocessed bands |
| radiation | R_ns, R_nl, R_n | albedo, lst, Rs_down, R_l_down |
| soil_heat | G | R_n, ndvi, lst |
| calibrate | dt_a, dt_b (in metadata), anchor pixels | lst, temperature_2m, R_n, G |
| et | H, LE, ET_inst, ETrF, ET_daily | R_n, G, dt_a, dt_b, ETr_inst |

#### Scenario: Missing band raises early
- **WHEN** a stage needs a band that does not exist on the DataCube
- **THEN** it raises `ValueError` with the missing band name before computing

### Requirement: Calibration is optional but threaded
The pipeline SHALL support both automatic (`AnchorPixelSelector`) and manual
calibration. When calibration produces `CalibrationStatus.REJECTED`, the
pipeline SHALL still continue to ET calculation so that quality-assessment
outputs are available.

#### Scenario: REJECTED scene still produces ET
- **WHEN** calibration returns REJECTED
- **THEN** `calculate_et()` still runs and `get_results()` returns ET arrays

### Requirement: Pipeline is stateless between runs
A single `METRICPipeline` instance SHALL NOT retain results from a previous
`run()` call. Re-running `run()` on the same instance SHALL reset internal
state (`self.data`, `_calibration_result`, `_anchor_result`, etc.).

#### Scenario: Re-run produces fresh results
- **WHEN** `pipeline.run()` is called twice with different inputs
- **THEN** the second result set reflects only the second inputs
