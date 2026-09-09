# output-taxonomy Specification

## Purpose
Defines the restructured OUTPUT_PRODUCTS taxonomy and OUTPUT_PRESETS
contract. Separates ET-core products, energy-balance components, quality
layers, surface physical properties, radiation fluxes, spectral indices, and
stress indices into discrete named categories so users compose outputs via
`output_categories` rather than monolithic boolean flags.

## Requirements

### Requirement: OUTPUT_PRODUCTS categorized taxonomy
`metric_et/config/settings.py` SHALL define `OUTPUT_PRODUCTS` as a dict
with exactly these seven top-level keys:

| Key | Products |
|-----|----------|
| `et_core` | `ETa_daily`, `ET_inst`, `ETrF`, `LE` |
| `energy_balance` | `Rn`, `G`, `H` |
| `quality` | `ET_quality_class`, `ETa_class` |
| `surface_props` | `albedo`, `lst`, `emissivity`, `lai`, `fvc` |
| `radiation` | `Rns`, `Rnl`, `Rs_down`, `R_l_down`, `R_l_up` |
| `spectral_indices` | `ndvi`, `savi`, `evi`, `ndmi`, `msi`, `nmdi`, `nirv`, `gci`, `ndsi`, `si_t` |
| `stress_indices` | `cwsi_et`, `cwsi_lst`, `tvdi`, `vswi`, `tc i`, `vci`, `vhi` |

Each value SHALL be a list of `(output_name, band_name_in_cube, dtype)` tuples,
consistent with the existing format used by the OutputWriter.

#### Scenario: All seven categories present
- **WHEN** `settings.OUTPUT_PRODUCTS` is imported
- **THEN** all seven keys exist and each maps to a non-empty list of tuples

---

### Requirement: OUTPUT_PRESETS collapsed to three entries
`OUTPUT_PRESETS` SHALL contain exactly three keys:

| Preset | Categories included |
|--------|-------------------|
| `minimal` | `et_core` |
| `standard` | `et_core`, `energy_balance`, `surface_props` |
| `full` | all seven categories |

No other preset names SHALL be defined. `drought` and `crop_health` are
user-defined category combinations expressed in application code, not
preset entries.

#### Scenario: minimal preset
- **WHEN** `OUTPUT_PRESETS["minimal"]` is resolved
- **THEN** it expands to all products in the `et_core` category only

#### Scenario: full preset resolves all categories
- **WHEN** `OUTPUT_PRESETS["full"]` is resolved
- **THEN** it includes every product from all seven categories

---

### Requirement: output_categories parameter replaces include_surface
`METRICWorkflow.__init__` SHALL accept an `output_categories` parameter:

```python
output_categories: Optional[List[str]] = None
```

- When `None`, the preset named `standard` is used (backward-compatible default).
- When a list of category strings, only those categories are included.
- The old `include_surface: bool = True` parameter SHALL be removed.

#### Scenario: Default uses standard preset
- **WHEN** `output_categories` is not passed
- **THEN** the workflow produces et_core + energy_balance + surface_props

#### Scenario: Custom category list
- **WHEN** `output_categories=["et_core", "spectral_indices"]`
- **THEN** only ET-core and spectral-index products are written

---

### Requirement: get_output_products helper updated
The `get_output_products(categories: List[str])` helper SHALL resolve a
list of category names to the flat product tuple list. It SHALL raise
`ValueError` for unknown category names.

#### Scenario: Unknown category raises
- **WHEN** `get_output_products(["unknown_category"])` is called
- **THEN** `ValueError` is raised
