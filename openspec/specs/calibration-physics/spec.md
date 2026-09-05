# calibration-physics Specification

## Purpose
Captures the physical constraints and formulas enforced by
`DTCalibration` so that anchor-pixel selection and coefficient computation
remain physically defensible.

## Requirements

### Requirement: dT linear model
The sensible-heat flux SHALL be parameterized as:
```
H = a * dT + b
dT = Ts - Ta
```
where `a` has units W/m²/K and `b` has units K (or W/m² when expressed as
an equivalent H offset).

#### Scenario: Coefficient units
- **WHEN** `calibrate()` returns
- **THEN** `a_coefficient` is in W/m²/K and `b_coefficient` is in K

### Requirement: Cold pixel enforces dT ≈ 0
A properly selected cold pixel (well-watered vegetation) SHALL satisfy:
`|dT_cold| ≤ 0.5 K`. When violated, the calibration SHALL flag a warning
and mark `valid = False`, but SHALL still return coefficients.

#### Scenario: dT_cold violation warning
- **WHEN** cold-pixel dT > 0.5 K
- **THEN** `errors` includes:
  `"Cold pixel dT constraint violated: dT_cold = X.XX K > 0.5 K"`

### Requirement: Hot pixel dT in physical range
The hot pixel SHALL satisfy `5 K ≤ dT_hot ≤ 35 K`. Values outside this range
indicate either an unrepresentative hot pixel or a scene-quality issue.

#### Scenario: dT_hot out of range
- **WHEN** `dT_hot < 5.0`
- **THEN** `errors` includes:
  `"dT_hot too small: X.XX K. Hot pixel may not be dry enough."`

### Requirement: dt_a clipped to [15, 45] W/m²/K
The slope `dt_a = (Rn_hot - G_hot) / dT_hot` SHALL be clipped to the range
[15, 45] W/m²/K. Values outside this range indicate anchor-pixel selection
problems or atypical surface conditions.

#### Scenario: Clipping logged
- **WHEN** raw dt_a is outside [15, 45]
- **THEN** the returned `a_coefficient` is clipped and a warning is logged

### Requirement: b = -a * (Ts_cold - Ta) (METRIC-consistent)
When both `ts_cold` and `air_temperature` are provided, the intercept SHALL be:
```
b = -a * (ts_cold - air_temperature)
```
This enforces the METRIC cold-pixel assumption that well-watered vegetation
has near-zero sensible heat flux.

#### Scenario: b computed from anchor pixels
- **WHEN** `ts_cold=300.0` and `air_temperature=298.0` and `a=15.83`
- **THEN** `b = -15.83 * (300.0 - 298.0) = -31.66 K`

### Requirement: Energy balance closure at cold pixel
The cold pixel SHALL satisfy `H_cold ≈ 0` (within measurement noise). When
`|H_cold| > 50 W/m²`, the calibration SHALL flag a violation.

#### Scenario: H_cold violation
- **WHEN** cold pixel energy balance is violated
- **THEN** `errors` includes:
  `"Cold pixel energy balance violation: H_cold = X.XX W/m². Should be ≈ 0"`
