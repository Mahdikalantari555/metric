# Add CWSI_LST and TVDI indices

## Summary
Add two new surface indices to `metric_et/surface/`: `CWSI_LST` and `TVDI`.

Both indices operate on `lst` + `ndvi` and fit the existing `DataCube` surface-properties flow.

## Motivation
- Provide drought/water-stress diagnostics without requiring meteorological inputs.
- Reuse already-computed `lst` and `ndvi` bands.
- Keep implementation minimal and testable.

## Scope
- New module: `metric_et/surface/indices.py` (CWSI_LST + TVDI)
- Export from `metric_et/surface/__init__.py`
- Wire into `metric_pipeline.calculate_surface_properties()` after LST
- Rename existing ET-based `CWSI` -> `CWSI_ET`, move all CWSI variants to surface group
- Add to `writer.py` / `settings.py` / `product_organizer.py`
- Update `datacube-contract` derived-band list

## Non-goals
- No visualization changes.
- No weather-dependent indices.
