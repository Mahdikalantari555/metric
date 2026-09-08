# Tasks: add CWSI_LST and TVDI

- [x] Add `CWSI_LSTCalculator` and `TVDICalculator` in `metric_et/surface/indices.py`
- [x] Export from `metric_et/surface/__init__.py`
- [x] Wire into pipeline after LST
- [x] Rename CWSI -> CWSI_ET, move to surface group (writer/config/organizer)
- [x] Add CWSI_LST/TVDI to surface group
- [x] Update `datacube-contract/spec.md` derived-band list
- [x] Add unit tests in `metric_et/tests/test_surface.py`
- [x] Run `conda run -n geospatial python -m pytest metric_et/tests/ -v`
