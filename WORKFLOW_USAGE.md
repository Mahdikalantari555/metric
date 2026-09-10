# METRIC Workflow Usage Guide

Source-of-truth usage guide for the unified METRIC workflow
(`run_metric_workflow.py`). It covers the CLI flags, the final output layout,
and where metadata and visualizations land.

## What the workflow does

`run_metric_workflow.py` runs the full METRIC ETa pipeline end to end:

1. Fetch Landsat 8/9 scenes from Microsoft Planetary Computer
2. Calculate ET for every scene via the METRIC pipeline
3. Interpolate / extrapolate ET across the time series
4. Organize products and write metadata

## CLI usage

```bash
python run_metric_workflow.py \
    --roi path/to/roi.geojson \
    --output path/to/output \
    --start-date 2023-06-01 \
    --end-date 2023-08-31 \
    [--aoi-name MY_FIELD] \
    [--max-cloud 50.0] \
    [--source-crs EPSG:4326] \
    [--interpolation-method weighted] \
    [--extrapolation-days 14] \
    [--no-surface] \
    [--output-categories et_core,spectral_indices] \
    [--save-scenes | --no-save-scenes] \
    [--visualization | --no-visualization]
```

### Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--roi` | required | Path to ROI file (GeoJSON `.geojson`/`.json` or Shapefile `.shp`) |
| `--output` | required | Base output directory |
| `--start-date` | required | Start date `YYYY-MM-DD` |
| `--end-date` | required | End date `YYYY-MM-DD` |
| `--aoi-name` | `AOI` | Area of Interest name used in file naming |
| `--max-cloud` | `50.0` | Maximum cloud cover percentage |
| `--source-crs` | `EPSG:4326` | CRS of the input ROI |
| `--interpolation-method` | `weighted` | `linear` or `weighted` |
| `--extrapolation-days` | `14` | Days to extrapolate beyond the last scene |
| `--no-surface` | off | Disable surface properties in output |
| `--output-categories` | `full` | Comma-separated category list (e.g. `et_core,spectral_indices`). Defaults to all categories. Each category gates a group of products — see presets below. |
| `--save-scenes` / `--no-save-scenes` | **on** | Keep the `scenes/` folder after processing. `--no-save-scenes` deletes it once products are organized |
| `--visualization` / `--no-visualization` | **off** | Emit `overview_<date>.png` and `et_map_<date>.png`. Off by default |

### Category presets

| Preset | Categories included |
|--------|-------------------|
| `full` (default) | `et_core`, `energy_balance`, `quality`, `surface_props`, `radiation`, `spectral_indices`, `stress_indices` |
| `standard` | `et_core`, `energy_balance`, `surface_props` |
| `minimal` | `et_core` |

Categories map to groups of products:

- **`et_core`** — ETaDaily, ETinst, ETrF, LE
- **`energy_balance`** — Rn, G, H
- **`quality`** — ET_quality_class, ETa_class
- **`surface_props`** — NDVI, EVI, LAI, FVC, SAVI, Albedo, LST, Emissivity
- **`radiation`** — Rns, Rnl, Rs_down, Rl_down, Rl_up
- **`spectral_indices`** — NDVI, SAVI, EVI, NDMI, MSI, NMDI, **MNDWI**, NIRv, GCI, NDSI, SI_T
- **`stress_indices`** — CWSI_ET, CWSI_LST, TVDI, VSWI, TCI, VCI, VHI

## Final output layout

After the workflow finishes, `--output` contains exactly two top-level folders:

```
<output>/
├── scenes/                         # raw downloaded Landsat data (clipped bands + MTL)
│   └── landsat_20230607_165_039/
│       ├── *_B1.tif
│       ├── ...
│       └── MTL.json
└── products/                       # organized METRIC output products
    ├── ETaDaily/
    │   ├── ETaDaily_L9_oli_tirs_..._2023-06-07_user5.tif
    │   └── metadata/
    │       └── META_ETaDaily_L9_oli_tirs_..._2023-06-07_user5.geojson
    ├── ETrF/
    │   ├── ETrF_L9_oli_tirs_..._2023-06-07_user5.tif
    │   └── metadata/
    │       └── META_ETrF_L9_oli_tirs_..._2023-06-07_user5.geojson
    ├── NDVI/
    │   └── ...
    ├── metadata/                   # scene-level metadata (shared across products)
    │   └── META_L9_oli_tirs_..._165039_2023-06-07_user5.geojson
    └── visualizations/             # only present when --visualization is on
        ├── overview_20230607.png
        └── et_map_20230607.png
```

### What changed

- The old intermediate `et_output/result_<date>/` staging folders are gone.
- Scene-level metadata (`metadata_*.json` from the pipeline) is renamed with a
  `META_` prefix, given a `.geojson` extension, and moved into the shared
  `products/metadata/` folder.
- Product-level metadata (`*.json` written next to each `.tif`) is renamed with a
  `META_` prefix, given a `.geojson` extension, and moved into that product's own
  `products/<product>/metadata/` folder.
- `overview_*.png` and `et_map_*.png` are only written when `--visualization` is
  on, and live under `products/visualizations/`.

## Metadata

Two distinct metadata kinds are produced:

- **Scene metadata** (`products/metadata/META_*.geojson`) — one per scene. Contains
  scene id, acquisition time, calibration coefficients, anchor pixels, quality
  metrics, and scene info (extent, CRS, sensor). Shared across all products.
- **Product metadata** (`products/<product>/metadata/META_*.geojson`) — one per
  product file. Contains product name/type, file path, dimensions, CRS, bounds,
  dtype, nodata, and pixel statistics.

## Examples

Default run (keeps scenes, no visualizations):

```bash
python run_metric_workflow.py \
    --roi data/roi.geojson \
    --output out/run1 \
    --start-date 2023-06-01 \
    --end-date 2023-08-31
```

Drop raw scene data after processing, and emit visualizations:

```bash
python run_metric_workflow.py \
    --roi data/roi.geojson \
    --output out/run2 \
    --start-date 2023-06-01 \
    --end-date 2023-08-31 \
    --no-save-scenes \
    --visualization
```

Only generate ET core and spectral indices:

```bash
python run_metric_workflow.py \
    --roi data/roi.geojson \
    --output out/run3 \
    --start-date 2023-06-01 \
    --end-date 2023-08-31 \
    --output-categories et_core,spectral_indices
```
