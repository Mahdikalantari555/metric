# output-layout Specification

## Purpose
Defines the on-disk directory structure produced by the METRIC workflow so
that downstream tools (visualization, QA, archival) can find products
reliably.

## Requirements

### Requirement: Two top-level folders only
**Reason**: New product categories (`spectral_indices`, `stress_indices`)
require documented product-directory conventions alongside existing ones.
**Migration**: No migration needed — existing directories continue to work;
new directories are added.

The final output directory SHALL contain exactly:
```
output/
├── scenes/           # Raw downloaded & clipped Landsat data
│   └── landsat_<date>_<path>_<row>/
│       ├── *.tif
│       └── MTL.json
└── products/         # Derived ETa products
    ├── <product-name>/
    │   ├── *.tif
    │   └── metadata/
    │       └── META_*.geojson
    ├── metadata/
    │   └── META_*.geojson      # scene-level metadata
    └── visualizations/         # optional
        ├── overview_<date>.png
        └── et_map_<date>.png
```

Product subdirectories SHALL group by category when writing indexed products:
```
products/
├── spectral_indices/
│   ├── ndmi_<scene>.tif
│   ├── msi_<scene>.tif
│   └── ...
├── stress_indices/
│   ├── cwsi_lst_<scene>.tif
│   ├── tvdi_<scene>.tif
│   ├── vswi_<scene>.tif
│   ├── tc i_<scene>.tif        # interpolated/scenes temporal result
│   ├── vci_<scene>.tif
│   └── vhi_<scene>.tif
└── ...existing product dirs...
```

No `et_output/result_<date>/` or `_work/` staging folders SHALL remain.

#### Scenario: Clean layout after workflow
- **WHEN** the workflow finishes successfully
- **THEN** `os.listdir(output_dir)` returns `["scenes", "products"]` (plus
  any user-supplied files)

### Requirement: Scene metadata in shared metadata folder
Scene-level metadata (`scene_id`, `acquisition_time`, `calibration`,
`anchor_pixels`, `quality`, `scene_info`) SHALL be written to
`products/metadata/META_<sensor>_<platform>_<level>_<res>_<sceneid>_<date>_<aoi>.geojson`.

No duplicate metadata SHALL exist inside individual product folders.

#### Scenario: Single scene metadata file
- **WHEN** one scene is processed
- **THEN** exactly one `META_*.geojson` exists in `products/metadata/`

### Requirement: Product metadata beside each product
Each product `.tif` SHALL have a sibling `metadata/META_<product>_<scene>_<date>_<aoi>.geojson`
containing: `product_name`, `product_type`, `file_path`, `dimensions`,
`crs`, `bounds`, `dtype`, `nodata`, `statistics`.

#### Scenario: Product metadata presence
- **WHEN** `products/ETaDaily/ETaDaily_....tif` exists
- **THEN** `products/ETaDaily/metadata/META_ETaDaily_....geojson` also exists

### Requirement: save-scenes flag controls raw data retention
`--save-scenes` (default ON) retains `scenes/`. `--no-save-scenes` deletes
`scenes/` via `shutil.rmtree` after `_finalize_layout()` completes.

#### Scenario: Disabled removes raw data
- **WHEN** `--no-save-scenes` is passed
- **THEN** `scenes/` does not exist after workflow completion

### Requirement: Visualization folder optional
`products/visualizations/` SHALL only be created when `--visualization` is
ON. When OFF, no PNG files are written.

#### Scenario: No visualization folder by default
- **WHEN** workflow runs without `--visualization`
- **THEN** `products/visualizations/` does not exist
