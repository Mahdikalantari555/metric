#!/usr/bin/env python3
"""Example 6: Full Synthetic Workflow (manual chain).

Demonstrates the complete METRIC chain on an in-memory synthetic scene
without touching the filesystem. Uses the same calculators that
METRICPipeline uses internally.

Run:
    conda activate geospatial
    python examples/06_full_workflow_synthetic.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import xarray as xr

from metric_et.core.datacube import DataCube
from metric_et.calibration.dt_calibration import DTCalibration
from metric_et.surface.vegetation import VegetationIndices
from metric_et.surface.albedo import AlbedoCalculator
from metric_et.surface.emissivity import EmissivityCalculator
from metric_et.surface.temperature import LandSurfaceTemperature
from metric_et.surface.roughness import RoughnessCalculator
from metric_et.radiation.net_radiation import NetRadiationCalculator
from metric_et.energy_balance.soil_heat_flux import SoilHeatFlux, SoilHeatFluxConfig
from metric_et.energy_balance.sensible_heat_flux import SensibleHeatFlux, SensibleHeatFluxConfig
from metric_et.energy_balance.latent_heat_flux import LatentHeatFlux, LatentHeatFluxConfig
from metric_et.et.instantaneous_et import InstantaneousET
from metric_et.et.daily_et import DailyET, DailyETConfig


def build_scene(size: int = 60) -> DataCube:
    np.random.seed(123)
    cube = DataCube()
    cube.add("blue",   xr.DataArray(np.random.rand(size, size).astype(np.float32), dims=["y","x"]))
    cube.add("green",  xr.DataArray(np.random.rand(size, size).astype(np.float32), dims=["y","x"]))
    cube.add("red",    xr.DataArray(np.random.rand(size, size).astype(np.float32), dims=["y","x"]))
    cube.add("nir08",  xr.DataArray(np.random.rand(size, size).astype(np.float32), dims=["y","x"]))
    cube.add("swir16", xr.DataArray(np.random.rand(size, size).astype(np.float32), dims=["y","x"]))
    cube.add("swir22", xr.DataArray(np.random.rand(size, size).astype(np.float32), dims=["y","x"]))
    cube.add("lwir11", xr.DataArray(285 + np.random.rand(size, size) * 20, dims=["y","x"]))
    cube.add("wind_speed", xr.DataArray(np.random.rand(size, size) * 5 + 2, dims=["y","x"]))
    cube.metadata.update({"sun_elevation": 45.0, "sun_azimuth": 160.0, "air_temperature": 298.0})
    return cube


def main() -> None:
    cube = build_scene()

    # 1 — Surface
    cube = VegetationIndices().compute(cube)
    cube = AlbedoCalculator(use_collection2=True, dark_pixel_correction=True).compute(cube)
    cube = EmissivityCalculator().compute(cube)
    cube = LandSurfaceTemperature().compute(cube)
    cube = RoughnessCalculator().compute(cube)
    print("Surface done")

    # 2 — Radiation (inject R_ns/R_nl, derive R_n)
    size = cube.data["lwir11"].shape[0]
    cube.add("R_ns", xr.DataArray(350 + np.random.rand(size, size) * 100, dims=["y","x"]))
    cube.add("R_nl", xr.DataArray(40 + np.random.rand(size, size) * 30, dims=["y","x"]))
    cube = NetRadiationCalculator(clip_negative=True).compute(cube)
    cube.add("temperature_2m", xr.DataArray(298 + np.random.rand(size, size) * 3, dims=["y","x"]))
    cube.add("u", cube.data["wind_speed"])
    cube.add("P", xr.DataArray(np.full((size,size), 101325.0), dims=["y","x"]))
    print("Radiation done")

    # 3 — Calibration
    cal = DTCalibration.create()
    result = cal.calibrate(ts_cold=300.0, ts_hot=325.0, air_temperature=298.0,
                           rn_hot=450.0, g_hot=22.5, et0_daily=5.0,
                           rs_inst=600.0, rs_daily=20.0, rn_cold=500.0, g_cold=25.0)
    print(f"Calibration: a={result.a_coefficient:.2f}, b={result.b_coefficient:.2f}")

    # 4 — Energy balance
    cube = SensibleHeatFlux(SensibleHeatFluxConfig(dt_a=result.a_coefficient, dt_b=result.b_coefficient)).compute(cube, result)
    cube = SoilHeatFlux(SoilHeatFluxConfig()).compute(cube)
    cube = LatentHeatFlux(LatentHeatFluxConfig()).compute(cube)
    print("Energy balance done")

    # 5 — ET
    cube.add("ETr_inst", xr.DataArray(np.random.rand(size,size) * 0.1 + 0.05, dims=["y","x"]))
    cube = InstantaneousET().compute(cube)
    et_daily = DailyET(DailyETConfig()).calculate_daily_et(cube.data["ETrF"], np.full((size,size), 5.0))
    print(f"Daily ET: {float(np.nanmin(et_daily)):.2f} – {float(np.nanmax(et_daily)):.2f} mm/day")
    print("Full synthetic workflow OK")


if __name__ == "__main__":
    main()
