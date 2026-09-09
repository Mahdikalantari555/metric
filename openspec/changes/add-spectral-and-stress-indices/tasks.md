## 1. Scaffolding & Module Structure

- [ ] 1.1 Create `metric_et/surface/moisture.py`, `productivity.py`, `salinity.py`, `temporal_stress.py` as empty modules with `__all__` exports, then verify `python -c "from metric_et.surface import moisture, productivity, salinity, temporal_stress"` imports cleanly
- [ ] 1.2 Update `metric_et/surface/__init__.py` to export from new modules; verify the package imports without errors (`python -c "import metric_et.surface"`)

## 2. Per-Scene Spectral Indices

- [ ] 2.1 Implement `NDMI` class in `moisture.py` — formula `(nir08 - swir16)/(nir08 + swir16)` — then verify with a unit test that checks the formula against hand-computed values and that missing `swir16` raises `ValueError`
- [ ] 2.2 Implement `MSI` class in `moisture.py` — formula `swir16/nir08` — then verify with a unit test checking that dry-soil ratios produce MSI > 1.0
- [ ] 2.3 Implement `NMDI` class in `moisture.py` — formula `(nir08 - (swir16 - swir22))/(nir08 + (swir16 - swir22))` — then verify with a unit test that missing `swir22` raises `ValueError`
- [ ] 2.4 Implement `NIRv` class in `productivity.py` — formula `ndvi * nir08` — then verify with a unit test that it reads existing `ndvi` from the cube rather than recomputing
- [ ] 2.5 Implement `GCI` class in `productivity.py` — formula `(nir08 / green) - 1` — then verify with a unit test checking zero-green gives NaN
- [ ] 2.6 Implement `NDSI` class in `salinity.py` — formula `(red - nir08)/(red + nir08)` — then verify with a unit test checking saline (red > nir) gives positive values
- [ ] 2.7 Implement `SI_T` class in `salinity.py` — formula `sqrt(red * swir16)` — then verify with a unit test checking non-negative output for positive reflectance inputs
- [ ] 2.8 Run `pytest metric_et/tests/ -q` to confirm no regressions from new module structure

## 3. Stress Module (Migrate + Extend)

- [ ] 3.1 Create `metric_et/surface/stress.py` containing migrated `CWSILSTCalculator` and `TVDICalculator` classes (ported from `indices.py` with identical behavior), plus a new `VSWI` class computing `ndvi / lst` with `lst_units: K` in attrs — then verify by running existing CWSI_LST/TVDI tests against the new module path
- [ ] 3.2 Delete `metric_et/surface/indices.py` and remove its exports from `__init__.py` — then verify the package still imports and all CWSI_LST/TVDI tests pass from the new location
- [ ] 3.3 Verify `CWSI_ET` stays in `metric_pipeline.py` (no code movement) — confirm by grep that no import of `CWSI_ET` exists in `stress.py` and the pipeline still computes it inline

## 4. Temporal Stress Indices

- [ ] 4.1 Implement `TCI`, `VCI`, `VHI` classes in `temporal_stress.py` that accept pre-computed min/max arrays (not DataCube) — then verify with unit tests that zero-denominator cases return NaN
- [ ] 4.2 Implement `_compute_temporal_indices(processed_scenes)` method in `run_metric_workflow.py` — accumulate `ndvi` and `lst` from each scene dict, build `ndvi_min/max`, `lst_min/max` stacks, then compute and attach `vci`, `tc i`, `vhi` DataArrays back to each scene's DataCube — then verify the method is callable and runs without error on a mock list of scene dicts with ndvi/lst fields

## 5. Pipeline Stage 3b

- [ ] 5.1 Add `calculate_spectral_indices()` method to `METRICPipeline` in `metric_pipeline.py` that calls each index class (`moisture`, `productivity`, `salinity`) on `self.data`, skipping silently with a warning log when required bands are absent — then verify it runs between stages 3 and 4 by checking log order
- [ ] 5.2 Insert the `calculate_spectral_indices()` call in `calculate_surface_properties()` or as a separate pipeline method — the spec requires Stage 3b between 3 and 4, so wire it into the main `run()` dispatch after stage 3 completes — then verify by running a full pipeline on a test scene and confirming `ndmi`, `msi`, `nmdi`, `nirv`, `gci`, `ndsi`, `si_t` appear in the output cube

## 6. Output Taxonomy Refactor

- [ ] 6.1 Restructure `OUTPUT_PRODUCTS` in `settings.py` into seven categories: `et_core`, `energy_balance`, `quality`, `surface_props`, `radiation`, `spectral_indices`, `stress_indices` — then verify all seven keys exist and map to non-empty product lists
- [ ] 6.2 Collapse `OUTPUT_PRESETS` to three entries: `minimal → [et_core]`, `standard → [et_core, energy_balance, surface_props]`, `full → all seven` — then verify `get_output_products()` resolves each preset correctly
- [ ] 6.3 Update `OutputWriter.__init__` in `writer.py`: replace `include_surface_properties: bool` with `output_categories: List[str]`, resolve products dynamically from `settings.OUTPUT_PRODUCTS` — then verify a writer constructed with `output_categories=["et_core", "spectral_indices"]` only writes those products
- [ ] 6.4 Update `save_results()` in `metric_pipeline.py` to pass `output_categories` instead of `include_surface_properties` — then verify the pipeline's existing save flow still works end-to-end

## 7. Workflow Integration

- [ ] 7.1 Replace `include_surface: bool = True` with `output_categories: Optional[List[str]] = None` in `METRICWorkflow.__init__` — default to `None` (uses `standard` preset categories); remove the `--no-surface` CLI arg and replace with an `--output-categories` option accepting comma-separated category names — then verify the CLI help text shows the new option
- [ ] 7.2 Wire `_compute_temporal_indices()` into the workflow between `_calculate_et_all()` and `_interpolate_et()` — then verify the method is called by checking logs or asserting temporal bands exist after the call
- [ ] 7.3 Ensure temporal bands (`vci`, `tc i`, `vhi`) are included in the output product writer when `stress_indices` is in `output_categories` — then verify a run with `output_categories=["stress_indices"]` produces vci/tci/vhi GeoTIFFs in `products/stress_indices/`

## 8. Tests & Validation

- [ ] 8.1 Add unit tests for all new per-scene index classes (NDMI, MSI, NMDI, NIRv, GCI, NDSI, SI_T, VSWI) covering: correct formula, missing-band ValueError, invalid-pixel NaN propagation — then verify `pytest metric_et/tests/test_indices.py -q` passes
- [ ] 8.2 Add unit tests for temporal stress classes (TCI, VCI, VHI) covering: correct formula against known min/max arrays, zero-denominator NaN, multi-scene accumulation logic — then verify `pytest metric_et/tests/test_temporal_stress.py -q` passes
- [ ] 8.3 Add an integration test in `test_pipeline.py` that runs a synthetic pipeline with mocked Landsat data and asserts `ndmi`, `msi`, `nmdi`, `nirv`, `gci`, `ndsi`, `si_t` bands are present after stage 3b — then verify the test passes
- [ ] 8.4 Run the full test suite `pytest metric_et/tests/ -q` and confirm all tests pass (no regressions from migration or refactor)
- [ ] 8.5 Smoke-test the CLI: `metric --help` shows `--output-categories`; a minimal run with `--output-categories et_core,spectral_indices` writes only those product folders — then verify the output directory contains only the expected categories

## 9. Documentation

- [ ] 9.1 Write `docs/indices.md` with a complete reference of every index in the suite — for each index include: full name, formula with Landsat 8/9 band substitution (e.g. NDMI = (B5 − B6)/(B5 + B6)), required bands, valid range, physical interpretation, and which category/preset it belongs to; then verify the document is readable and all 17 indices (10 spectral + 4 stress per-scene + 3 temporal) are covered
