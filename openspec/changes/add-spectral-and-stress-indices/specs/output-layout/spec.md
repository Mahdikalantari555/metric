## MODIFIED Requirements

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
