## Why

The unified METRIC workflow currently dumps every scene's products into redundant
`et_output/result_<date>/` staging folders, mixes scene-level and product-level
metadata as flat `.json` files, and always writes `overview_*.png` / `et_map_*.png`
regardless of need. The final tree is cluttered (`scenes/`, `et_output/products/`,
`et_output/result_*`) and there is no control over retaining raw scene data or
emitting visualizations. This change introduces two flags — `--save-scenes` (default
ON) and `--visualization` (default OFF) — and a clean final layout with exactly two
top-level folders (`scenes/`, `products/`) plus an explicit, separated metadata
structure for scene vs. product metadata.

## What Changes

- Add `--save-scenes` flag to `run_metric_workflow.py` (default ON). When OFF, the
  `scenes/` folder is deleted after product organization completes.
- Add `--visualization` flag to `run_metric_workflow.py` (default OFF). When ON,
  `overview_<date>.png` and `et_map_<date>.png` are written; when OFF they are not.
- Eliminate the intermediate `et_output/result_<date>/` staging folders. Products are
  written directly into `products/<product-name>/`.
- **BREAKING**: Final output layout changes from
  `output/scenes/ + output/et_output/{products,result_*}` to
  `output/scenes/ + output/products/`.
- Scene-level metadata (`metadata_<...>.json` emitted by the pipeline) is saved to a
  shared `products/metadata/` folder (across products), renamed with a `META_` prefix
  and `.geojson` extension.
- Product-level metadata (`*.json` emitted by the organizer next to each `.tif`) is
  saved into each product's own `products/<product-name>/metadata/` folder, renamed
  with a `META_` prefix and `.geojson` extension.
- Visualization PNGs (when enabled) are written to `products/visualizations/`.

## Capabilities

### New Capabilities
- `scene-save-and-metadata`: Controls retention of raw scene downloads and defines the
  separated scene-vs-product metadata layout (shared `products/metadata/` for scene
  metadata, per-product `products/<product>/metadata/` for product metadata).
- `visualization-flag`: Controls whether the workflow emits `overview_*.png` and
  `et_map_*.png` visualizations (default OFF).

### Modified Capabilities
<!-- none -->

## Impact

- `run_metric_workflow.py`: new CLI flags, output-dir restructuring, conditional
  scene-folder deletion, metadata relocation, visualization gating.
- `metric_et/pipeline/metric_pipeline.py`: accept a `save_visualization` parameter to
  gate PNG generation; write products directly to the products root instead of a
  per-date staging dir.
- `metric_et/output/product_organizer.py`: write product metadata into a
  `<product>/metadata/` subfolder with `META_` prefix and `.geojson` extension; skip
  the legacy flat `result_<date>` scan root.
- `metric_et/output/writer.py`: write scene metadata with `META_` prefix / `.geojson`
  extension into the shared metadata folder; thread the visualization flag through.
- Output consumers / any downstream tooling that expected `et_output/result_<date>/`
  must be updated (breaking layout change).
