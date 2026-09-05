#!/usr/bin/env python3
"""Example 4: Energy Balance Demo (H, G, LE).

Requires calibration coefficients (a, b) from Example 1.

Run:
    conda activate geospatial
    python examples/04_energy_balance.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import xarray as xr
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from metric_et.core.datacube import DataCube
from metric_et.energy_balance.soil_heat_flux import SoilHeatFlux, SoilHeatFluxConfig
from metric_et.energy_balance.sensible_heat_flux import SensibleHeatFlux, SensibleHeatFluxConfig
from metric_et.energy_balance.latent_heat_flux import LatentHeatFlux, LatentHeatFluxConfig


def build_cube() -> DataCube:
    np.random.seed(7)
    h, w = 50, 50
    cube = DataCube()
    cube.add("R_n", xr.DataArray(400 + np.random.rand(h, w) * 100, dims=["y", "x"]))
    cube.add("ndvi", xr.DataArray(np.random.rand(h, w), dims=["y", "x"]))
    cube.add("lst", xr.DataArray(285 + np.random.rand(h, w) * 20, dims=["y", "x"]))
    cube.add("lwir11", xr.DataArray(285 + np.random.rand(h, w) * 20, dims=["y", "x"]))
    cube.add("temperature_2m", xr.DataArray(298 + np.random.rand(h, w) * 4, dims=["y", "x"]))
    cube.add("u", xr.DataArray(np.random.rand(h, w) * 5 + 1, dims=["y", "x"]))
    cube.add("z0m", xr.DataArray(np.random.rand(h, w) * 0.1 + 0.01, dims=["y", "x"]))
    cube.add("P", xr.DataArray(np.full((h, w), 101325.0), dims=["y", "x"]))
    return cube


def main() -> None:
    cube = build_cube()

    # Calibration coefficients — normally from DTCalibration
    a_coeff = 15.83
    b_coeff = -31.67
    from metric_et.calibration.dt_calibration import CalibrationResult
    from datetime import datetime
    fake_cal = CalibrationResult(
        a_coefficient=a_coeff, b_coefficient=b_coeff,
        dT_cold=2.0, dT_hot=27.0, ts_cold=300.0, ts_hot=325.0,
        air_temperature=298.0, valid=True, errors=[],
    )

    # H (sensible heat) — requires CalibrationResult as 2nd arg
    h_calc = SensibleHeatFlux(SensibleHeatFluxConfig(dt_a=a_coeff, dt_b=b_coeff))
    cube = h_calc.compute(cube, fake_cal)

    # G (soil heat flux)
    g_calc = SoilHeatFlux(SoilHeatFluxConfig())
    cube = g_calc.compute(cube)

    # LE (latent heat flux)
    le_calc = LatentHeatFlux(LatentHeatFluxConfig())
    cube = le_calc.compute(cube)

    # Closure check
    residual = cube.data["R_n"] - cube.data["H"] - cube.data["G"] - cube.data["LE"]

    fig, axes = plt.subplots(1, 4, figsize=(16, 4))
    cube.data["H"].plot(ax=axes[0], cmap="viridis")
    axes[0].set_title("Sensible Heat H (W/m²)")
    cube.data["G"].plot(ax=axes[1], cmap="viridis")
    axes[1].set_title("Soil Heat Flux G (W/m²)")
    cube.data["LE"].plot(ax=axes[2], cmap="viridis")
    axes[2].set_title("Latent Heat LE (W/m²)")
    residual.plot(ax=axes[3], cmap="RdBu_r", center=0)
    axes[3].set_title("Closure Residual (W/m²)")
    plt.tight_layout()
    out = Path(__file__).with_suffix(".png")
    plt.savefig(out, dpi=150)
    print(f"Saved: {out}")


if __name__ == "__main__":
    main()
