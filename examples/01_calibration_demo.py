#!/usr/bin/env python3
"""Example 1: METRIC dT Calibration Demo.

Run:
    conda activate geospatial
    python examples/01_calibration_demo.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np

from metric_et.calibration.dt_calibration import DTCalibration


def main() -> None:
    cal = DTCalibration.create()

    # ------------------------------------------------------------------
    # Anchor-pixel inputs (replace with real values from your scene)
    # ------------------------------------------------------------------
    result = cal.calibrate(
        ts_cold=300.0,          # Cold-pixel LST (K) — well-watered vegetation
        ts_hot=325.0,           # Hot-pixel LST (K)  — dry bare soil
        air_temperature=298.0,  # 2-m air temperature (K)
        rn_hot=450.0,           # Net radiation at hot pixel (W/m²)
        g_hot=22.5,             # Soil heat flux at hot pixel (W/m²)
        et0_daily=5.0,          # Daily reference ET (mm/day)
        rs_inst=600.0,          # Incoming shortwave at overpass (W/m²)
        rs_daily=20.0,          # Daily shortwave integral (MJ/m²/day)
        rn_cold=500.0,          # Net radiation at cold pixel (W/m²)
        g_cold=25.0,            # Soil heat flux at cold pixel (W/m²)
    )

    print("=== Calibration Result ===")
    print(f"  status      : {result.status.value}")
    print(f"  a (slope)   : {result.a_coefficient:.2f} W/m²/K")
    print(f"  b (intercept): {result.b_coefficient:.2f} K")
    print(f"  dT_cold     : {result.dT_cold:.2f} K  (target ≈ 0)")
    print(f"  dT_hot      : {result.dT_hot:.2f} K  (target 15–25)")
    print(f"  valid       : {result.valid}")
    if result.errors:
        print(f"  errors      : {result.errors}")


if __name__ == "__main__":
    main()
