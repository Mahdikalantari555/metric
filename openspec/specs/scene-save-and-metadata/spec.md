# scene-save-and-metadata Specification

## Purpose
Controls retention of downloaded Landsat scene data and defines a clean, separated
metadata layout that distinguishes scene-level metadata (shared across products) from
product-level metadata (per product). Implemented in `run_metric_workflow.py` via the
`--save-scenes` flag and the `_finalize_layout()` method, with metadata written by
`metric_et/output/product_organizer.py` (product metadata) and
`metric_et/output/writer.py` `write_metadata()` (scene metadata).

## Requirements

### Requirement: Save-scenes flag controls raw scene retention
The workflow SHALL provide a `--save-scenes` flag (argparse `BooleanOptionalAction`)
defaulting to ON. When ON, the `scenes/` folder containing the downloaded and clipped
Landsat scene data (bands + MTL.json per `landsat_<date>_<path>_<row>/`) is retained
after the workflow completes. When OFF (`--no-save-scenes`), the `scenes/` folder SHALL
be deleted via `shutil.rmtree` once `_finalize_layout()` has finished.

#### Scenario: Default keeps scenes
- **WHEN** the workflow runs without `--save-scenes`
- **THEN** the `scenes/` folder remains present in the output directory after completion

#### Scenario: Disabled deletes scenes
- **WHEN** the workflow runs with `--no-save-scenes`
- **THEN** the `scenes/` folder is removed from the output directory after `_finalize_layout()`

### Requirement: Final output has only scenes and products folders
The workflow SHALL produce a final output layout containing exactly two top-level
folders: `scenes/` and `products/`. The intermediate `et_output/result_<date>/`
staging folders SHALL NOT be present in the final output. A transient `output/_work/`
staging dir is used during processing and removed by `_finalize_layout()`.

#### Scenario: No per-date result folders
- **WHEN** the workflow finishes
- **THEN** the output directory contains `scenes/` and `products/` and no `et_output/result_<date>/` directory

#### Scenario: Transient staging dir cleaned up
- **WHEN** the workflow finishes (success or failure path)
- **THEN** no `output/_work/` directory remains

### Requirement: Scene metadata saved in shared across-products folder
The workflow SHALL save scene-level metadata (emitted by the pipeline as
`metadata_<sensor>_<platform>_<level>_<res>_<sceneid>_<date>_<aoi>.json` via
`writer.write_metadata_file()`) into a shared `products/metadata/` folder that is
common across all products. Each file SHALL be renamed with a `META_` prefix
(dropping the leading `metadata` stem) and a `.geojson` extension, and SHALL NOT be
duplicated inside individual product folders.

#### Scenario: Scene metadata relocation
- **WHEN** a scene is processed and scene metadata is generated
- **THEN** the file `products/metadata/META_<sensor>_<platform>_<level>_<res>_<sceneid>_<date>_<aoi>.geojson` exists and no `metadata_*.json` remains in any product folder

#### Scenario: Scene metadata content preserved
- **WHEN** scene metadata is relocated
- **THEN** the `.geojson` file contains the original scene metadata fields (scene_id, acquisition_time, calibration, anchor_pixels, quality, scene_info)

### Requirement: Product metadata saved in each product's own folder
The workflow SHALL save product-level metadata (emitted by `ProductOrganizer._create_product_metadata()`)
into a `metadata/` subfolder inside that product's own directory
(`products/<product-name>/metadata/`). Each file SHALL be renamed with a `META_` prefix
and a `.geojson` extension (e.g. `META_ETaDaily_L9_oli_tirs_..._2023-06-07_user5.geojson`).

#### Scenario: Product metadata relocation
- **WHEN** a product `.tif` is organized
- **THEN** its metadata exists at `products/<product-name>/metadata/META_<product>_<scene>_<date>_<aoi>.geojson` and no flat `*.json` remains beside the `.tif`

#### Scenario: Product metadata content preserved
- **WHEN** product metadata is written
- **THEN** the `.geojson` file contains product_name, product_type, file_path, dimensions, crs, bounds, dtype, nodata, and statistics
