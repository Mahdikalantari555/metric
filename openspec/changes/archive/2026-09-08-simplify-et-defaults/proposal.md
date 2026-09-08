# Simplify ET defaults and remove regional presets

## Summary
Remove regional presets, standardize defaults to one configuration, and remove the ETrF upper clamp at 2.0.

## Motivation
- Regional presets (`tropical`, `arid`, `temperate`, `mediterranean`) add complexity without clear benefit when `daylight_fraction` is always 1.0 and `max_et_daily` is always 30.
- The ETrF clamp at 2.0 incorrectly caps reference ET fraction. ETrF can exceed 2.0 in advection conditions (e.g., irrigated areas, oases), which is physically valid per METRIC methodology.
- A single default configuration is simpler and easier to maintain.

## Changes

### 1. Remove regional presets from `create_daily_et()`
- Remove `region_presets` dict from `metric_et/et/daily_et.py`
- Remove `region` parameter from `create_daily_et()` factory
- Set factory defaults: `daylight_fraction=1.0`, `max_et_daily=30.0`

### 2. Standardize `DailyETConfig` defaults
- `daylight_fraction: float = 1.0` (already set, keep)
- `max_et_daily: float = 30.0` (change from 20.0)
- Remove `use_diurnal_distribution` (unused)

### 3. Remove ETrF upper clamp
- In `InstantaneousETConfig`: remove or set `max_etrf` to infinity / remove upper bound
- In `calculate_etrf()`: remove `np.clip` upper bound, keep only `min_etrf` floor
- Remove `region_max_et_rate`, `region_min_etrf`, `region_max_etrf` from config
- Remove regional override logic in `InstantaneousET.__init__()` (lines 117-122)

### 4. Remove regional documentation
- Remove "Regional Adaptations" sections from docstrings in `daily_et.py` and `instantaneous_et.py`

## Non-goals
- No changes to ET calculation formulas
- No changes to validation or QA/QC logic beyond removing regional overrides
