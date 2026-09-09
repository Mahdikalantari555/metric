## Context

The pipeline currently computes surface properties (NDVI, EVI, LAI, SAVI, FVC, albedo, emissivity, LST, roughness) per scene in Stage 3. CWSI_LST and TVDI are computed ad-hoc in the same method but live in a separate `indices.py` module. No per-scene spectral indices exist beyond the vegetation suite. Temporal stress indices (VCI, TCI, VHI) do not exist at all.

The `OutputWriter.DEFAULT_PRODUCTS` dict is hardcoded in `writer.py`; `settings.py` holds a parallel `OUTPUT_PRODUCTS`/`OUTPUT_PRESETS` dict that is only partially used (the `surface` flag gates NDVI/LAI/etc. but NOT radiation or energy-balance products). The `METRICWorkflow` constructor exposes `include_surface: bool = True` and `products: Optional[List[str]]`.

## Goals / Non-Goals

**Goals:**
- Add 11 new per-scene index computations (7 spectral + 4 stress) without changing any existing band names or formulas.
- Add 3 temporal indices (TCI, VCI, VHI) computed from multi-scene accumulated min/max.
- Restructure output product categories so users select by semantic group rather than boolean flags.
- Keep CWSI_ET inside the ET pipeline (it depends on ET_inst and ETrF which are computed there).
- Keep LST in `surface_props` (it is both an ET driver and an index input).

**Non-Goals:**
- No new satellite sensor support — all indices target Landsat 8/9 bands already in the contract.
- No change to the ET energy-balance equations themselves.
- No new CLI arguments beyond `output_categories` (replacing `--no-surface`).
- No backward-compatible aliases for the old preset names (`et_only`, `with_quality`, `research`).

## Decisions

### D1: File layout — five new modules + one rename

```
surface/
├── vegetation.py       ← unchanged API; NDVI/EVI/LAI/SAVI/FVC stay here
├── moisture.py         ← NDMI, MSI, NMDI          (new)
├── stress.py           ← CWSI_ET, CWSI_LST, TVDI, VSWI   (migrate + extend)
├── temporal_stress.py  ← TCI, VCI, VHI            (new)
├── productivity.py     ← NIRv, GCI                (new)
└── salinity.py         ← NDSI, SI_T               (new)
```

**Rationale**: `stress.py` groups indices whose physical meaning is "crop water stress" regardless of whether they use spectral bands alone (VSWI) or feature-space methods (CWSI_LST, TVDI). `CWSI_ET` is included here because it is semantically a stress indicator even though its computation stays in the ET pipeline — the pipeline will import the class only for documentation/registry purposes, not for execution.

**Alternative considered**: Single `indices.py` with all new classes. Rejected because the stress/spectral/temporal boundary becomes impossible to read.

### D2: Per-scene indices run in Stage 3b

New pipeline method `calculate_spectral_indices()` runs immediately after `calculate_surface_properties()` and before `calculate_radiation_balance()`. It reads raw reflectance bands directly from the cube. Each module exports a single callable that takes a `DataCube` and returns it with added bands.

Missing-band graceful skip follows the existing pattern in `albedo.py` (fallback with log warning) rather than raising.

### D3: Temporal accumulation pattern

During `_calculate_et_all()`, each processed scene's `ndvi` and `lst` are appended to lists keyed by (y, x) coordinate. After the loop:

```python
# Build coordinate-aware DataArrays
ndvi_stack = np.stack([s['ndvi'] for s in processed_scenes], axis=0)  # (T, y, x)
lst_stack  = np.stack([s['lst']  for s in processed_scenes], axis=0)
ndvi_min = np.nanmin(ndvi_stack, axis=0)
ndvi_max = np.nanmax(ndvi_stack, axis=0)
lst_min  = np.nanmin(lst_stack,  axis=0)
lst_max  = np.nanmax(lst_stack,  axis=0)
```

TCI uses the *last* scene's LST as the instantaneous value. VCI/TCI/VHI are computed once and attached to each scene's DataCube as extra bands before `_interpolate_et()` runs, so downstream organizers see them consistently.

**Alternative considered**: Compute temporal indices after interpolation. Rejected because VCI/TCI/VHI are scene-level products meant for direct comparison with per-scene ET; interpolating them would introduce temporal smoothing artifacts not present in the original index formulas.

### D4: OUTPUT_PRESETS reduced to three; output_categories replaces include_surface

The three presets map directly to category lists:

| Preset | Categories |
|--------|-----------|
| `minimal` | `[et_core]` |
| `standard` | `[et_core, energy_balance, surface_props]` |
| `full` | all seven |

Old presets (`et_only`, `with_quality`, `research`) are removed. If callers reference them, they get a clear `KeyError` at startup rather than silent misbehaviour.

`METRICWorkflow.__init__` gains `output_categories: Optional[List[str]] = None`. When `None`, the `standard` preset categories are used. The old `include_surface` parameter is removed entirely.

The `OutputWriter` constructor replaces `include_surface_properties: bool` with `output_categories: List[str]` and resolves products dynamically from `settings.OUTPUT_PRODUCTS`.

### D5: CWSI_ET stays in the ET pipeline

CWSI_ET = 1 − ET_inst / ETrF_inst requires both ET quantities that are computed in `calculate_et()`. Moving it to `stress.py` would require either a cross-stage dependency or duplicating the formula. Keeping it in the pipeline preserves the existing call site and avoids adding a new stage boundary. The class is imported in `stress.py` only for registry/documentation if needed; actual computation remains where it is.

## Risks / Trade-offs

- **Breaking change on preset names**: Old scripts using `output_products=["et_only"]` will fail. Mitigation: error message clearly states available presets.
- **Temporal index memory**: Stacking all NDVI/LST arrays in memory could be significant for large ROIs with many scenes (~100 MB for 30 scenes at 1 km × 1 km, 30 m resolution). Acceptable for current use cases; document the limit.
- **VSWI in stress category vs spectral**: VSWI uses NDVI and LST (non-spectral inputs) but is per-scene. Placed in `stress_indices` for semantic consistency with other stress indicators.
- **TCI instantaneous value source**: Using the last scene's LST for TCI means TCI is not truly "scene-agnostic" — it reflects the most recent observation. This matches the standard interpretation in remote-sensing literature.

## Migration Plan

1. Create new files (`moisture.py`, `stress.py`, `temporal_stress.py`, `productivity.py`, `salinity.py`).
2. Update `surface/__init__.py` to export from new locations; delete `indices.py`.
3. Add Stage 3b call in `metric_pipeline.py`.
4. Restructure `settings.py` `OUTPUT_PRODUCTS` and `OUTPUT_PRESETS`.
5. Update `OutputWriter` to accept `output_categories`.
6. Update `run_metric_workflow.py`: replace `include_surface` with `output_categories`, add `_compute_temporal_indices()`.
7. Update tests referencing old paths or preset names.
8. Verify existing tests pass; add new tests for each index formula.

Rollback: revert to the pre-change git commit; the change is fully reversible as no existing band names or core ET equations are modified.

## Open Questions

(None — all decisions resolved in exploration.)
