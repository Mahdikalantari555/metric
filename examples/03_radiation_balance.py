#!/usr/bin/env python3
"""Example 3: Radiation Balance Demo.

Computes net radiation R_n = R_ns - R_nl on a synthetic scene.

Run:
    conda activate geospatial
    python examples/03_radiation_balance.py
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
from metric_et.radiation.net_radiation import NetRadiationCalculator


def main() -> None:
    np.random.seed(0)
    h, w = 50, 50

    # Net shortwave and longwave are the inputs to NetRadiation.
    # In a full run they come from ShortwaveRadiation / LongwaveRadiation,
    # but here we synthesize them directly to avoid unrelated validators.
    cube = DataCube()
    cube.add("R_ns", xr.DataArray(400 + np.random.rand(h, w) * 100, dims=["y", "x"]))
    cube.add("R_nl", xr.DataArray(40 + np.random.rand(h, w) * 30, dims=["y", "x"]))

    rn = NetRadiationCalculator(clip_negative=True)
    cube = rn.compute(cube)

    fig, axes = plt.subplots(1, 3, figsize=(14, 4))
    cube.data["R_ns"].plot(ax=axes[0], cmap="viridis")
    axes[0].set_title("Net Shortwave R_ns (W/m²)")
    cube.data["R_nl"].plot(ax=axes[1], cmap="viridis")
    axes[1].set_title("Net Longwave R_nl (W/m²)")
    cube.data["R_n"].plot(ax=axes[2], cmap="viridis")
    axes[2].set_title("Net Radiation R_n (W/m²)")
    plt.tight_layout()
    out = Path(__file__).with_suffix(".png")
    plt.savefig(out, dpi=150)
    print(f"Saved: {out}")


if __name__ == "__main__":
    main()
