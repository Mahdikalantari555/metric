# energy-balance Specification

## Purpose
Defines the equations, input contracts, and validation rules for the three
energy-balance flux components: sensible heat (H), soil heat flux (G), and
latent heat flux (LE).

## Requirements

### Requirement: Surface energy balance equation
The model SHALL enforce:
```
R_n = H + LE + G
```
where:
- `R_n` = net radiation (W/m²)
- `H` = sensible heat flux (W/m²)
- `LE` = latent heat flux (W/m²)
- `G` = soil heat flux (W/m²)

#### Scenario: Closure residual computed
- **WHEN** all three fluxes and R_n are present
- **THEN** `residual = R_n - H - LE - G` is defined (used for validation)

### Requirement: Sensible heat flux formula
`H` SHALL be computed as:
```
H = ρ * c_p * dT / r_ah
dT = a * (Ts - Ta) + b
```
where:
- `ρ` = air density (kg/m³), temperature-dependent
- `c_p` = specific heat of air (≈ 1013 J/kg/K)
- `r_ah` = aerodynamic resistance (s/m), computed from wind speed and
  roughness via Monin-Obukhov similarity with stability corrections

#### Scenario: Aerodynamic resistance bounded
- **WHEN** `rah` is computed
- **THEN** it is clipped to `[min_rah, max_rah]` (default 10–500 s/m)

### Requirement: Soil heat flux is calibration-free
`G` SHALL be computed from `R_n`, NDVI/LAI, and `Ts` without any anchor-pixel
calibration. The default formulation is:
```
G = R_n * (Ts - 273.15) / (albedo * Rn_factor) * ndvi_factor
```
(exact coefficients depend on the implementation in `soil_heat_flux.py`).

#### Scenario: G computed before calibration
- **WHEN** the pipeline runs
- **THEN** `calculate_soil_heat_flux()` executes before `calibrate()` so
  that G is available for anchor-pixel energy-balance checks

### Requirement: Latent heat flux is residual
`LE` SHALL be computed as:
```
LE = R_n - H - G
```
No independent formulation for LE is used; it is the residual of the energy
balance.

#### Scenario: Negative LE clipped
- **WHEN** `LE < 0`
- **THEN** it is clipped to 0 (condensation / dew is not modeled)

### Requirement: Monin-Obukhov stability corrections
When `use_stability_correction=True` (default), the SHALL iterate to solve
for `L` (Obukhov length) and apply:
```
ψ_m = 2 * ln((1 + x)/2) + ln((1 + x²)/2) - 2*atan(x) + π/2
ψ_h = 2 * ln((1 + y)/2) + ln((1 + y²)/2)
```
where `x = (1 - 16 * z/L)^(1/4)` and `y = (1 - 16 * z/L)^(1/2)`.

#### Scenario: Stability iterations bounded
- **WHEN** stability correction is enabled
- **THEN** iteration count is bounded by `stability_iterations` (default 5)

### Requirement: Physical bounds on outputs
| Flux | Min | Max | Unit |
|------|-----|-----|------|
| H | -500 | 800 | W/m² |
| G | -200 | 300 | W/m² |
| LE | 0 | R_n | W/m² |

Values outside bounds SHALL be clipped and a warning logged.
