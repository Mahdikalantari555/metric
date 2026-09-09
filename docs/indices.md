# METRIC Spectral and Stress Indices Reference

This document covers all spectral indices (per-scene) and temporal stress indices in the METRIC ET pipeline. There are **17 indices** grouped into three categories: spectral, per-scene stress, and temporal stress.

---

## 1. Spectral Indices (Stage 3b)

All spectral indices are computed in Stage 3b by reading raw Landsat 8/9 reflectance bands. If a required band is missing, that index is skipped with a warning log and the rest of the stage continues.

---

### NDMI — Normalized Difference Moisture Index

| Item | Value |
|------|-------|
| **Formula** | `NDMI = (NIR − SWIR1) / (NIR + SWIR1)` |
| **Landsat 8/9** | `(B5 − B6) / (B5 + B6)` |
| **Required bands** | `nir08` (B5), `swir16` (B6) |
| **Valid range** | [−1, 1] |
| **Interpretation** | Measures plant and soil moisture content. Higher values indicate better water status; widely used for drought monitoring. |
| **Category** | `spectral_indices` |
| **Source** | `metric_et/surface/moisture.py::NDMI` |

---

### MSI — Moisture Stress Index

| Item | Value |
|------|-------|
| **Formula** | `MSI = SWIR1 / NIR` |
| **Landsat 8/9** | `B6 / B5` |
| **Required bands** | `nir08` (B5), `swir16` (B6) |
| **Valid range** | No fixed upper bound; typical 0.3–3.0 |
| **Interpretation** | Indicates water stress level. Higher values mean greater moisture deficit (dry soil or water-stressed vegetation). |
| **Category** | `spectral_indices` |
| **Source** | `metric_et/surface/moisture.py::MSI` |

---

### NMDI — Normalized Multi-band Drought Index

| Item | Value |
|------|-------|
| **Formula** | `NMDI = (NIR − (SWIR1 − SWIR2)) / (NIR + (SWIR1 − SWIR2))` |
| **Landsat 8/9** | `(B5 − (B6 − B7)) / (B5 + (B6 − B7))` |
| **Required bands** | `nir08` (B5), `swir16` (B6), `swir22` (B7) |
| **Valid range** | [−1, 1] |
| **Interpretation** | More sensitive to atmospheric water vapor than NDMI; useful for regional drought assessment. Higher values indicate better water conditions. |
| **Category** | `spectral_indices` |
| **Source** | `metric_et/surface/moisture.py::NMDI` |

---

### NIRv — Near-Infrared Reflectance of Vegetation

| Item | Value |
|------|-------|
| **Formula** | `NIRv = NDVI × NIR` |
| **Landsat 8/9** | `NDVI × B5` |
| **Required bands** | `ndvi` (pre-computed), `nir08` (B5) |
| **Valid range** | Approximately [0, 0.5] |
| **Interpretation** | Combines canopy greenness with near-infrared reflectance; one of the strongest simple predictors of GPP and biomass. Reads existing `ndvi` from the cube without recomputing. |
| **Category** | `spectral_indices` |
| **Source** | `metric_et/surface/productivity.py::NIRv` |

---

### GCI — Green Chlorophyll Index

| Item | Value |
|------|-------|
| **Formula** | `GCI = (NIR / Green) − 1` |
| **Landsat 8/9** | `(B5 / B3) − 1` |
| **Required bands** | `nir08` (B5), `green` (B3) |
| **Valid range** | Typically 1–10; dense vegetation > 2 |
| **Interpretation** | Reflects leaf chlorophyll and nitrogen content. Higher values indicate higher chlorophyll concentration; used for crop nutrition diagnosis. Zero or negative green reflectance yields NaN. |
| **Category** | `spectral_indices` |
| **Source** | `metric_et/surface/productivity.py::GCI` |

---

### NDSI — Normalized Difference Salinity Index

| Item | Value |
|------|-------|
| **Formula** | `NDSI = (Red − NIR) / (Red + NIR)` |
| **Landsat 8/9** | `(B4 − B5) / (B4 + B5)` |
| **Required bands** | `red` (B4), `nir08` (B5) |
| **Valid range** | [−1, 1] |
| **Interpretation** | Positive values indicate saline or urban surfaces; negative values indicate healthy vegetation. Used for soil salinity and land degradation monitoring. |
| **Category** | `spectral_indices` |
| **Source** | `metric_et/surface/salinity.py::NDSI` |

---

### SI_T — Soil Salinity Index (geometric mean variant)

| Item | Value |
|------|-------|
| **Formula** | `SI_T = √(Red × SWIR1)` |
| **Landsat 8/9** | `√(B4 × B6)` |
| **Required bands** | `red` (B4), `swir16` (B6) |
| **Valid range** | ≥ 0 (reflectance-scaled units) |
| **Interpretation** | Geometric mean of red and SWIR reflectance; more sensitive to agricultural soil salinity than NDSI. |
| **Category** | `spectral_indices` |
| **Source** | `metric_et/surface/salinity.py::SI_T` |

---

## 2. Per-Scene Stress Indices (Stage 3)

These indices require both NDVI and LST to be present in the DataCube. They are computed during the surface properties stage.

---

### CWSI_LST — Crop Water Stress Index (NDVI-LST feature space)

| Item | Value |
|------|-------|
| **Formula** | `CWSI_LST = (LST − LST_wet) / (LST_dry − LST_wet)` |
| **Required bands** | `ndvi`, `lst` |
| **Valid range** | [0, 1] (clipped by default) |
| **Interpretation** | 0 = well-watered; 1 = maximum water stress. Wet and dry edges are estimated from per-NDVI-bin quantiles (wet at 5th percentile, dry at 95th percentile) and interpolated to each pixel. |
| **Category** | `stress_indices` |
| **Source** | `metric_et/surface/stress.py::CWSILSTCalculator` |

---

### TVDI — Temperature Vegetation Dryness Index

| Item | Value |
|------|-------|
| **Formula** | `TVDI = (LST − LST_min) / (LST_max − LST_min)` |
| **Required bands** | `ndvi`, `lst` |
| **Valid range** | [0, 1] (clipped by default) |
| **Interpretation** | 0 = wet edge (well-watered); 1 = dry edge (severe drought). The dry edge is a linear fit (`a + b × NDVI`) to per-bin 95th-percentile LST values; the wet edge is the global 5th-percentile LST. |
| **Category** | `stress_indices` |
| **Source** | `metric_et/surface/stress.py::TVDICalculator` |

---

### VSWI — Vegetation Supply Water Index

| Item | Value |
|------|-------|
| **Formula** | `VSWI = NDVI / LST` |
| **Required bands** | `ndvi`, `lst` |
| **Valid range** | No fixed upper bound |
| **Interpretation** | Instantaneous water-supply indicator. Higher values mean relatively better water conditions. **LST must be in Kelvin.** Zero or non-finite LST yields NaN. |
| **Category** | `stress_indices` |
| **Source** | `metric_et/surface/stress.py::VSWI` |

---

### CWSI_ET — Crop Water Stress Index (ET-ratio method)

| Item | Value |
|------|-------|
| **Formula** | `CWSI_ET = 1 − (ET_inst / ETrF_inst)` |
| **Required data** | `ET_inst`, `ETrF` (computed by ET pipeline) |
| **Valid range** | [0, 1] |
| **Interpretation** | 0 = well-watered; 1 = maximum stress. This is an internal ET-model indicator computed directly in `calculate_et()` rather than in a standalone module. |
| **Category** | `stress_indices` |
| **Source** | `metric_et/pipeline/metric_pipeline.py::calculate_et()` |

---

## 3. Temporal Stress Indices

These indices accumulate NDVI and LST min/max across multiple scenes within a workflow run and are computed once after all scenes are processed, before interpolation.

---

### VCI — Vegetation Condition Index

| Item | Value |
|------|-------|
| **Formula** | `VCI = (NDVI − NDVI_min) / (NDVI_max − NDVI_min)` |
| **Required data** | Per-scene `ndvi` plus accumulated `ndvi_min` and `ndvi_max` |
| **Valid range** | [0, 1] |
| **Interpretation** | 0 = worst vegetation condition; 1 = best. Pixels with no temporal variation (`NDVI_max == NDVI_min`) yield NaN. |
| **Category** | `stress_indices` (temporal) |
| **Source** | `metric_et/surface/temporal_stress.py::VCI` |

---

### TCI — Temperature Condition Index

| Item | Value |
|------|-------|
| **Formula** | `TCI = (LST_max − LST) / (LST_max − LST_min)` |
| **Required data** | Per-scene `lst` plus accumulated `lst_min` and `lst_max`; uses the last scene's LST as the instantaneous value |
| **Valid range** | [0, 1] |
| **Interpretation** | 0 = hottest / most stressed; 1 = coolest / healthiest. Zero denominator yields NaN. |
| **Category** | `stress_indices` (temporal) |
| **Source** | `metric_et/surface/temporal_stress.py::TCI` |

---

### VHI — Vegetation Health Index

| Item | Value |
|------|-------|
| **Formula** | `VHI = α · VCI + (1 − α) · TCI` (default α = 0.5) |
| **Required data** | `vci`, `tci` from the same scene |
| **Valid range** | [0, 1] |
| **Interpretation** | Composite of vegetation condition and thermal stress. Where either VCI or TCI is NaN, VHI is NaN. |
| **Category** | `stress_indices` (temporal) |
| **Source** | `metric_et/surface/temporal_stress.py::VHI` |

---

## 4. Output Category Reference

| Category | Products |
|----------|---------|
| `et_core` | `ET_daily`, `ET_inst`, `ETrF`, `LE` |
| `energy_balance` | `R_n`, `G`, `H` |
| `quality` | `ET_quality_class`, `ETa_class` |
| `surface_props` | `NDVI`, `EVI`, `LAI`, `FVC`, `SAVI`, `Albedo`, `LST`, `Emissivity` |
| `radiation` | `R_ns`, `R_nl`, `Rs_down`, `R_l_down`, `R_l_up` |
| `spectral_indices` | `NDVI`, `SAVI`, `EVI`, **`NDMI`, `MSI`, `NMDI`, `NIRv`, `GCI`, `NDSI`, `SI_T`** |
| `stress_indices` | **`CWSI_ET`, `CWSI_LST`, `TVDI`, `VSWI`, `TCI`, `VCI`, `VHI`** |

### Presets

| Preset | Categories enabled |
|--------|-------------------|
| `minimal` | `et_core` |
| `standard` | `et_core`, `energy_balance`, `surface_props` |
| `full` | All seven categories |

---

## 5. Usage

### Python API

```python
from metric_et.surface.moisture import NDMI, MSI, NMDI
from metric_et.surface.productivity import NIRv, GCI
from metric_et.surface.salinity import NDSI, SI_T
from metric_et.surface.stress import CWSILSTCalculator, TVDICalculator, VSWI
from metric_et.surface.temporal_stress import TCI, VCI, VHI

# Per-scene: compute() modifies the cube in-place
cube = NDMI().compute(cube)   # adds 'ndmi' band
cube = MSI().compute(cube)    # adds 'msi' band
# ...

# Temporal indices (requires pre-computed min/max arrays):
tci_result = TCI().compute(lst_current, lst_min, lst_max)
vci_result = VCI().compute(ndvi_current, ndvi_min, ndvi_max)
vhi_result = VHI(alpha=0.5).compute(vci_result, tci_result)
```

### CLI

```bash
metric --output-categories et_core,spectral_indices,stress_indices \
       --roi roi.geojson --output ./out \
       --start-date 2024-01-01 --end-date 2024-03-31
```
