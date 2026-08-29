## Context

`run_metric_workflow.py` orchestrates: fetch scenes → calculate ET → interpolate →
organize products. Today it passes `output_dir=et_output/result_<date>` to the
pipeline, so every scene leaves a `result_<date>/` folder full of `.tif`, `.json`, and
`.png` files. `product_organizer` then scans and moves `.tif`s into
`et_output/products/<type>/`, leaving the redundant `result_*` folders and mixing
scene-level (`metadata_*.json`) and product-level (`<product>_*.json`) metadata as flat
files. PNGs (`overview_*.png`, `et_map_*.png`) are always written by the pipeline
(`metric_pipeline.py` lines ~1542-1552) with no flag to disable them.

See proposal.md — Why for motivation.

## Goals / Non-Goals

**Goals:**
- Two clean top-level output folders: `scenes/` and `products/`.
- `--save-scenes` (default ON) and `--visualization` (default OFF) flags on the CLI.
- Separated metadata: scene metadata shared in `products/metadata/`, product metadata
  in each `products/<product>/metadata/`, both with `META_` prefix and `.geojson`.
- PNG emission gated at the pipeline source.

**Non-Goals:**
- Changing the internal computation/calibration of METRIC.
- Adding new product types or new visualization kinds.
- Altering the Planetary Computer fetch logic.

## Decisions

1. **Transient staging dir instead of `result_<date>`**. The workflow writes pipeline
   output to a hidden transient folder `output/_work/` (replacing per-date
   `result_<date>`). `organize_products` scans `output/_work/` and produces
   `output/_work/products/<type>/`. After organizing, the workflow moves
   `output/_work/products` → `output/products`, relocates metadata/PNGs, then deletes
   `output/_work`. This preserves the organizer's scan-and-move model while removing the
   redundant per-date folders. *Alternative considered*: writing directly into
   `products/<type>` — rejected because it complicates the organizer's "skip already-in-
   products" logic and mixes in-flight and finalized outputs.

2. **Scene metadata → `products/metadata/META_<name>.geojson`**. The pipeline's
   `metadata_<...>.json` is collected from `output/_work/` after the run and moved into
   the shared `products/metadata/` folder, renamed with `META_` prefix and `.geojson`
   extension. It is intentionally NOT duplicated per product.

3. **Product metadata → `products/<product>/metadata/META_<name>.geojson`**. The
   organizer is updated to write each product's metadata into a `metadata/` subfolder of
   that product's directory, with `META_` prefix and `.geojson` extension, instead of
   beside the `.tif`.

4. **`.geojson` extension**. Files are renamed to `.geojson`; content is preserved
   (wrapped as a GeoJSON `Feature`/`FeatureCollection` when a geometry is present,
   otherwise the JSON is kept and merely renamed). *Assumption*: "should become geojson"
   means the extension and GeoJSON framing, not a full geometry reprojection.

5. **Visualization gating**. A `save_visualization` boolean is threaded from the CLI →
   `METRICWorkflow` → `METRICPipeline.run(...)`. When `False`, the pipeline skips
   `create_summary_figure` and `plot_et_map` (no file is generated). When `True`, the
   PNGs are written to `products/visualizations/`.

6. **Scene-folder deletion**. `--save-scenes` OFF triggers `shutil.rmtree(scenes_dir)`
   after `_organize_products()` succeeds.

## Risks / Trade-offs

- **[Breaking layout]** → Any downstream tool reading `et_output/result_<date>/` breaks.
  Mitigation: document the new layout in README and the workflow summary.
- **[Hidden `_work` if crash]** → A failed run may leave `output/_work/`. Mitigation:
  wrap staging cleanup in `finally`; acceptable as it mirrors prior `result_*` clutter.
- **[geojson semantics]** → Scene metadata lacks true CRS geometry; renaming to
  `.geojson` is cosmetic. Mitigation: note assumption in proposal; revisit if a real
  geometry is later required.
