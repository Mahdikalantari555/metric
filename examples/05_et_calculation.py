#!/usr/bin/env python3
"""Example 5: ET Calculation Demo.

Converts LE → instantaneous ET → daily ET on a synthetic scene.

Run:
    conda activate geospatial
    python examples/05_et_calculation.py
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
from metric_et.et.instantaneous_et import InstantaneousET
from metric_et.et.daily_et import DailyET, DailyETConfig


def main() -> None:
    np.random.seed(99)
    h, w = 50, 50

    cube = DataCube()
    cube.add("LE", xr.DataArray(50 + np.random.rand(h, w) * 350, dims=["y", "x"]))
    cube.add(
        "ETr_inst",
        xr.DataArray(np.random.rand(h, w) * 0.1 + 0.05, dims=["y", "x"]),
    )

    # Instantaneous ET
    iet = InstantaneousET()
    cube = iet.compute(cube)

    # Daily ET
    etr_daily = np.full((h, w), 5.0)
    det = DailyET(DailyETConfig())
    et_daily = det.calculate_daily_et(cube.data["ETrF"], etr_daily)

    fig, axes = plt.subplots(1, 3, figsize=(14, 4))
    cube.data["ET_inst"].plot(ax=axes[0], cmap="Blues", vmin=0, vmax=0.5)
    axes[0].set_title("Instantaneous ET (mm/hr)")
    cube.data["ETrF"].plot(ax=axes[1], cmap="RdYlGn", vmin=0, vmax=1.5)
    axes[1].set_title("ETrF")
    axes[2].imshow(et_daily, cmap="Blues", vmin=0, vmax=12)
    axes[2].set_title("Daily ET (mm/day)")
    axes[2].axis("off")
    plt.tight_layout()
    out = Path(__file__).with_suffix(".png")
    plt.savefig(out, dpi=150)
    print(f"Saved: {out}")


if __name__ == "__main__":
    main()
