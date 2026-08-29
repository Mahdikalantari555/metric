## Purpose

Controls whether the workflow emits overview visualizations (`overview_*.png` and
`et_map_*.png`) produced by the pipeline, defaulting to OFF so they are not written
unless explicitly requested. Implemented via the `--visualization` flag in
`run_metric_workflow.py`, threaded through `METRICWorkflow.run()` →
`METRICPipeline.run()` → `save_results()`, which gates the `Visualization`
`create_summary_figure()` and `plot_et_map()` calls in
`metric_et/pipeline/metric_pipeline.py`.

## ADDED Requirements

### Requirement: Visualization flag defaults to off
The workflow SHALL provide a `--visualization` flag (argparse `BooleanOptionalAction`)
defaulting to OFF. When OFF, the pipeline SHALL NOT write the `overview_<date>.png`
and `et_map_<date>.png` files.

#### Scenario: Default suppresses PNGs
- **WHEN** the workflow runs without `--visualization`
- **THEN** no `overview_*.png` or `et_map_*.png` files exist in the output

### Requirement: Visualization flag enables PNG output
When `--visualization` is ON, the workflow SHALL write `overview_<date>.png` and
`et_map_<date>.png` for each processed scene into `products/visualizations/`. The
PNGs are first written to the transient staging dir by the pipeline, then moved to
`products/visualizations/` by `_finalize_layout()`.

#### Scenario: Enabled writes PNGs
- **WHEN** the workflow runs with `--visualization` ON and a scene is processed
- **THEN** `products/visualizations/overview_<date>.png` and `products/visualizations/et_map_<date>.png` exist for that scene

### Requirement: Visualization flag threaded through pipeline
The visualization decision SHALL be passed from the workflow into the pipeline so that
PNG generation is gated at the source; the pipeline SHALL NOT generate or save the
figures when visualization is disabled. The `save_results()` method accepts a
`save_visualization` parameter and only instantiates `Visualization` and calls
`create_summary_figure()` / `plot_et_map()` when it is True.

#### Scenario: Pipeline respects flag
- **WHEN** the pipeline is invoked with `save_visualization=False`
- **THEN** the summary figure and ET map figure are neither generated nor saved to disk

#### Scenario: Pipeline generates when enabled
- **WHEN** the pipeline is invoked with `save_visualization=True`
- **THEN** `overview_<date>.png` and `et_map_<date>.png` are written to the output dir
