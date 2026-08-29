## 1. CLI Flags & Workflow Plumbing

- [x] 1.1 Add `--save-scenes` (default `True`) and `--visualization` (default `False`) argparse flags in `run_metric_workflow.py` main() and pass them into `METRICWorkflow.__init__`; verify `python run_metric_workflow.py --help` lists both flags.
- [x] 1.2 Store `self.save_scenes` and `self.visualization` on `METRICWorkflow` and update the workflow logging to print their values; verify startup log shows both.

## 2. Staging Restructure (remove result_<date>)

- [x] 2.1 Replace `self.et_output_dir / "result_<date>"` per-scene output with a single transient `self.staging_dir = output_dir / "_work"` passed to the pipeline; products land flat in `_work/`; verify no `result_<date>` dir is created during a run.
- [x] 2.2 After `_organize_products()`, move `output/_work/products` → `output/products`; verify final output has only `scenes/` and `products/` (no `et_output/` or `result_*`).

## 3. Scene Metadata Relocation

- [x] 3.1 Collect pipeline `metadata_*.json` from `_work/` and move to `output/products/metadata/META_<name>.geojson` (shared, not per product); verify `products/metadata/` exists with `META_`-prefixed `.geojson` files and none remain in product folders.

## 4. Product Metadata Relocation

- [x] 4.1 Update `ProductOrganizer` to write each product's metadata into `<product>/metadata/META_<name>.geojson` instead of beside the `.tif`; verify `products/<type>/metadata/META_*.geojson` exists and no flat `*.json` sits next to `.tif`.

## 5. Visualization Gating

- [x] 5.1 Thread `save_visualization` into `METRICPipeline.run(...)` and guard the `create_summary_figure` / `plot_et_map` block so PNGs are only generated when enabled; verify no `overview_*.png`/`et_map_*.png` exist when `--visualization` is off.
- [x] 5.2 When enabled, write the PNGs to `output/products/visualizations/`; verify `products/visualizations/overview_<date>.png` and `et_map_<date>.png` exist for each processed scene.

## 6. Scene Retention

- [x] 6.1 When `--save-scenes` is OFF, `shutil.rmtree(self.scenes_dir)` after product organization succeeds; verify `scenes/` is absent post-run and present when default/on.

## 7. Docs & Validation

- [x] 7.1 Update `README.md` / workflow docs with the new flags and final `scenes/`+`products/` layout incl. metadata structure; verify docs match implemented paths.
- [x] 7.2 Run `openspec validate add-scene-save-and-viz-flags` (and `--strict`) and fix any delta issues; verify it passes.
