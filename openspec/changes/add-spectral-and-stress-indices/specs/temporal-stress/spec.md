## Purpose

Defines the temporal-stress index contract: TCI, VCI, and VHI that require
min/max LST and NDVI accumulated across multiple scenes within a workflow run.
These indices cannot be computed per-scene — they require a post-scene-
processing aggregation step in the workflow orchestration layer.

## ADDED Requirements

### Requirement: Temporal accumulation of NDVI and LST
During `_calculate_et_all()`, the workflow SHALL collect the per-scene
`ndvi` and `lst` DataArrays from every successfully processed scene into
in-memory accumulators keyed by pixel coordinates (y, x).

After all scenes are processed, the accumulators SHALL expose:
- `ndvi_min[y,x]` — minimum NDVI across all scenes at each pixel
- `ndvi_max[y,x]` — maximum NDVI across all scenes at each pixel
- `lst_min[y,x]` — minimum LST across all scenes at each pixel
- `lst_max[y,x]` — maximum LST across all scenes at each pixel

Pixels that are valid in only one scene SHALL still participate in min/max
(comparing a single value against itself yields that value).

Invalid pixels (NaN in any scene) SHALL propagate through min/max as NaN
unless at least one valid value exists for that pixel.

#### Scenario: Accumulation across three scenes
- **WHEN** three scenes are processed with valid NDVI at overlapping pixels
- **THEN** `ndvi_min` and `ndvi_max` reflect the global min/max over those three values

---

### Requirement: VCI — Vegetation Condition Index
The `VCI` class SHALL compute:

    VCI = (NDVI − NDVI_min) / (NDVI_max − NDVI_min)

using the temporally accumulated min/max from the previous requirement.

The result SHALL be an `xr.DataArray` named `vci` with:
- `long_name`: "Vegetation Condition Index"
- `units`: "dimensionless"
- `range`: "[0, 1]" — 0 = worst vegetation condition, 1 = best

When `NDVI_max == NDVI_min` (no variation), the denominator is zero; the
result for those pixels SHALL be NaN.

#### Scenario: VCI zero variation
- **WHEN** all scenes have identical NDVI at a pixel
- **THEN** VCI is NaN at that pixel

---

### Requirement: TCI — Temperature Condition Index
The `TCI` class SHALL compute:

    TCI = (LST_max − LST) / (LST_max − LST_min)

Note: this formula uses the *instantaneous* LST of the current scene
(interpolated to the temporal frame) against the accumulated min/max.
In the first implementation, TCI is computed per-scene using that scene's
LST; the accumulated LST bounds come from the same accumulator as VCI.

The result SHALL be an `xr.DataArray` named `tc i` with:
- `long_name`: "Temperature Condition Index"
- `units`: "dimensionless"
- `range`: "[0, 1]" — 0 = hottest/stressed, 1 = coolest/healthy

Higher values indicate cooler, less stressed conditions.

When `LST_max == LST_min`, the denominator is zero; result is NaN.

#### Scenario: TCI uses latest scene LST
- **WHEN** `_compute_temporal_indices()` runs after all scenes are processed
- **THEN** it uses the last-processed scene's LST as the instantaneous value

---

### Requirement: VHI — Vegetation Health Index
The `VHI` class SHALL compute:

    VHI = α · VCI + (1 − α) · TCI

with default `α = 0.5`:

    VHI = 0.5 · VCI + 0.5 · TCI

The result SHALL be an `xr.DataArray` named `vhi` with:
- `long_name`: "Vegetation Health Index"
- `units`: "dimensionless"
- `range`: "[0, 1]"
- Both VCI and TCI must be valid at a pixel for VHI to be valid there.

#### Scenario: VHI requires both inputs
- **WHEN** VCI is valid but TCI is NaN at a pixel
- **THEN** VHI is NaN at that pixel

---

### Requirement: Workflow insertion point
`_compute_temporal_indices()` SHALL be called in `run_metric_workflow.py`
immediately after `_calculate_et_all()` returns and before
`_interpolate_et()` is invoked. It SHALL mutate the `processed_scenes`
list (adding temporal results to each scene dict) or attach results to a
shared accumulator accessible to downstream steps.

#### Scenario: Temporal indices before interpolation
- **WHEN** the workflow has ≥ 2 processed scenes
- **THEN** VCI, TCI, and VHI are available before interpolation begins
