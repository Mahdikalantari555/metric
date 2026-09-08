# Simplify ET defaults and remove regional presets

## Requirement: Remove regional presets
The `create_daily_et()` factory function in `metric_et/et/daily_et.py` SHALL NOT contain regional presets (`tropical`, `arid`, `temperate`, `mediterranean`).

- Remove `region_presets` dictionary
- Remove `region` parameter from `create_daily_et()`
- Default `daylight_fraction` SHALL be `1.0`
- Default `max_et_daily` SHALL be `30.0`

## Requirement: Standardize DailyETConfig defaults
`DailyETConfig` in `metric_et/et/daily_et.py` SHALL use:

- `daylight_fraction: float = 1.0`
- `max_et_daily: float = 30.0` (changed from 20.0)
- Remove `use_diurnal_distribution` field

## Requirement: Remove ETrF upper clamp
`InstantaneousETConfig` in `metric_et/et/instantaneous_et.py` SHALL NOT have an upper bound on `max_etrf`.

- Remove `max_etrf` upper bound from `calculate_etrf()` clipping
- Keep only `min_etrf` floor (default 0.0)
- Remove `region_max_et_rate`, `region_min_etrf`, `region_max_etrf` config fields
- Remove regional override logic in `InstantaneousET.__init__()` (lines 117-122)

## Requirement: Remove regional documentation
Remove "Regional Adaptations" sections from module docstrings in:
- `metric_et/et/daily_et.py`
- `metric_et/et/instantaneous_et.py`
