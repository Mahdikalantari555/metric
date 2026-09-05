#!/usr/bin/env python3
"""Example 2: Surface Properties Demo.

Computes NDVI, albedo, emissivity, LST and roughness from a synthetic
Landsat-like scene and plots each product.

Run:
    conda activate geospatial
    python examples/02_surface_properties.py
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
from metric_et.surface.vegetation import VegetationIndices
from metric_et.surface.albedo import AlbedoCalculator
from metric_et.surface.emissivity import EmissivityCalculator
from metric_et.surface.temperature import LandSurfaceTemperature
from metric_et.surface.roughness import RoughnessCalculator


def build_synthetic_cube(size: int = 50) -> DataCube:
    np.random.seed(42)
    cube = DataCube()
    cube.add("blue",   xr.DataArray(np.random.rand(size, size).astype(np.float32), dims=["y", "x"]))
    cube.add("green",  xr.DataArray(np.random.rand(size, size).astype(np.float32), dims=["y", "x"]))
    cube.add("red",    xr.DataArray(np.random.rand(size, size).astype(np.float32), dims=["y", "x"]))
    cube.add("nir08",  xr.DataArray(np.random.rand(size, size).astype(np.float32), dims=["y", "x"]))
    cube.add("swir16", xr.DataArray(np.random.rand(size, size).astype(np.float32), dims=["y", "x"]))
    cube.add("swir22", xr.DataArray(np.random.rand(size, size).astype(np.float32), dims=["y", "x"]))
    cube.add("lwir11", xr.DataArray(285 + np.random.rand(size, size) * 20, dims=["y", "x"]))
    cube.metadata["sun_elevation"] = 45.0
    cube.metadata["sun_azimuth"] = 160.0
    return cube


def main() -> None:
    cube = build_synthetic_cube()

    # 1. Vegetation indices
    veg = VegetationIndices()
    cube = veg.compute(cube)

    # 2. Albedo
    alb = AlbedoCalculator(use_collection2=True, dark_pixel_correction=True)
    cube = alb.compute(cube)

    # 3. Emissivity
    emiss = EmissivityCalculator()
    cube = emiss.compute(cube)

    # 4. LST
    lst = LandSurfaceTemperature()
    cube = lst.compute(cube)

    # 5. Roughness
    rough = RoughnessCalculator()
    cube = rough.compute(cube)

    # Plot
    fig, axes = plt.subplots(2, 3, figsize=(14, 8))
    cube.data["ndvi"].plot(ax=axes[0, 0], cmap="RdYlGn", vmin=-1, vmax=1)
    axes[0, 0].set_title("NDVI")
    cube.data["lai"].plot(ax=axes[0, 1], cmap="viridis")
    axes[0, 1].set_title("LAI")
    cube.data["albedo"].plot(ax=axes[0, 2], cmap="viridis", vmin=0, vmax=0.5)
    axes[0, 2].set_title("Albedo")
    cube.data["emissivity"].plot(ax=axes[1, 0], cmap="viridis", vmin=0.9, vmax=1.0)
    axes[1, 0].set_title("Emissivity")
    cube.data["lst"].plot(ax=axes[1, 1], cmap="inferno")
    axes[1, 1].set_title("LST (K)")
    cube.data["z0m"].plot(ax=axes[1, 2], cmap="cividis")
    axes[1, 2].set_title("Roughness z0m (m)")
    plt.tight_layout()
    out = Path(__file__).with_suffix(".png")
    plt.savefig(out, dpi=150)
    print(f"Saved: {out}")


if __name__ == "__main__":
    main()
