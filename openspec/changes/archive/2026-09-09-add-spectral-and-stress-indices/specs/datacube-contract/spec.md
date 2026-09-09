## MODIFIED Requirements

### Requirement: Canonical Landsat band names
**Reason**: New spectral indices require additional derived-band names to be
recorded in the contract.
**Migration**: Existing code is unaffected; only downstream consumers that
parse the derived-band list need to know the new names.

The DataCube SHALL use the following band names (matching
`LandsatReader.BAND_MAPPING`):

| Band name | Description |
|-----------|-------------|
| blue | Coastal / blue aerosol |
| green | Green |
| red | Red |
| nir08 | Near-infrared (L8/9 Band 5) |
| swir16 | Shortwave infrared 1.6 μm |
| swir22 | Shortwave infrared 2.2 μm |
| lwir11 | Thermal infrared 10.9–12.5 μm (brightness temp) |
| qa | Quality band (optional) |
| qa_pixel | Pixel QA band (optional) |

Derived bands SHALL use snake_case:
`ndvi`, `evi`, `lai`, `savi`, `fvc`, `albedo`, `emissivity`,
`lst`, `z0m`, `Rs_down`, `R_l_down`, `R_ns`, `R_nl`, `R_n`, `H`, `G`, `LE`,
`ET_inst`, `ETrF`, `ET_daily`, `CWSI_ET`, `cwsi_lst`, `tvdi`,
`ndmi`, `msi`, `nmdi`, `nirv`, `gci`, `ndsi`, `si_t`,
`vswi`, `tc i`, `vci`, `vhi`.

#### Scenario: Surface properties read by name
- **WHEN** `VegetationIndices.compute()` runs
- **THEN** it reads `cube.get("red")` and `cube.get("nir08")` — not aliases
