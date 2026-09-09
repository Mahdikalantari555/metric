## MODIFIED Requirements

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
