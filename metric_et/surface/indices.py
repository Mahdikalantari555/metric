"""Stress indices: CWSI_LST and TVDI from NDVI-LST feature space."""

from typing import Optional

import numpy as np
import xarray as xr

from ..core.datacube import DataCube


def _bin_quantiles(
    ndvi: np.ndarray,
    lst: np.ndarray,
    ndvi_min: float,
    ndvi_max: float,
    bin_width: float,
    quantile: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Compute per-bin quantile of LST conditioned on NDVI.

    Returns (bin_centers, q_values) for bins with at least one valid sample.
    """
    edges = np.arange(ndvi_min, ndvi_max + bin_width, bin_width)
    centers = (edges[:-1] + edges[1:]) / 2.0
    valid_mask = np.isfinite(ndvi) & np.isfinite(lst)
    ndvi_v = ndvi[valid_mask]
    lst_v = lst[valid_mask]

    q_centers = []
    q_values = []
    for i in range(len(centers)):
        lo = edges[i]
        hi = edges[i + 1]
        # last bin inclusive of max
        if i == len(centers) - 1:
            sel = (ndvi_v >= lo) & (ndvi_v <= hi)
        else:
            sel = (ndvi_v >= lo) & (ndvi_v < hi)
        bin_lst = lst_v[sel]
        if bin_lst.size == 0:
            continue
        q = float(np.quantile(bin_lst, quantile))
        q_centers.append(centers[i])
        q_values.append(q)

    return np.array(q_centers), np.array(q_values)


class CWSILSTCalculator:
    """Crop Water Stress Index from NDVI-LST feature space (binning method).

    Edges are estimated per NDVI bin via quantiles and interpolated
    back to pixel NDVI.

    Formula:
        CWSI_LST = (LST - LST_wet) / (LST_dry - LST_wet)
    """

    def __init__(
        self,
        wet_quantile: float = 0.05,
        dry_quantile: float = 0.95,
        ndvi_bin_width: float = 0.02,
        ndvi_min: float = 0.2,
        ndvi_max: float = 0.9,
        clip: bool = True,
    ):
        self.wet_quantile = wet_quantile
        self.dry_quantile = dry_quantile
        self.ndvi_bin_width = ndvi_bin_width
        self.ndvi_min = ndvi_min
        self.ndvi_max = ndvi_max
        self.clip = clip

    def compute_cwsi_lst(
        self,
        lst: xr.DataArray,
        ndvi: xr.DataArray,
    ) -> xr.DataArray:
        lst_v = lst.values.astype(float)
        ndvi_v = ndvi.values.astype(float)

        wet_centers, wet_vals = _bin_quantiles(
            ndvi_v, lst_v, self.ndvi_min, self.ndvi_max, self.ndvi_bin_width, self.wet_quantile
        )
        dry_centers, dry_vals = _bin_quantiles(
            ndvi_v, lst_v, self.ndvi_min, self.ndvi_max, self.ndvi_bin_width, self.dry_quantile
        )

        if wet_centers.size < 2 or dry_centers.size < 2:
            raise ValueError("Not enough valid NDVI bins to estimate CWSI_LST edges")

        # Interpolate wet/dry edges to per-pixel NDVI (extrapolate with edge values)
        flat_ndvi = ndvi_v.ravel()
        # Use np.interp which handles sorted x
        wet_edge_flat = np.interp(flat_ndvi, wet_centers, wet_vals, left=wet_vals[0], right=wet_vals[-1])
        dry_edge_flat = np.interp(flat_ndvi, dry_centers, dry_vals, left=dry_vals[0], right=dry_vals[-1])

        wet_edge = wet_edge_flat.reshape(lst_v.shape)
        dry_edge = dry_edge_flat.reshape(lst_v.shape)

        with np.errstate(divide="ignore", invalid="ignore"):
            denom = dry_edge - wet_edge
            # avoid zero division
            denom = np.where(denom == 0, np.nan, denom)
            cwsi = (lst_v - wet_edge) / denom

        # Mask invalid inputs
        cwsi = np.where(np.isfinite(lst_v) & np.isfinite(ndvi_v), cwsi, np.nan)

        if self.clip:
            cwsi = np.clip(cwsi, 0.0, 1.0)

        da = xr.DataArray(cwsi, dims=lst.dims, coords=lst.coords)
        da.name = "cwsi_lst"
        da.attrs = {
            "long_name": "Crop Water Stress Index (NDVI-LST feature space)",
            "units": "dimensionless",
            "range": "[0, 1]",
            "method": "binning + per-bin quantile + interp",
            "wet_quantile": self.wet_quantile,
            "dry_quantile": self.dry_quantile,
            "ndvi_bin_width": self.ndvi_bin_width,
            "ndvi_min": self.ndvi_min,
            "ndvi_max": self.ndvi_max,
        }
        return da

    def compute(self, cube: DataCube) -> DataCube:
        if "lst" not in cube.bands():
            raise ValueError("lst not found in DataCube. Compute LST first.")
        if "ndvi" not in cube.bands():
            raise ValueError("ndvi not found in DataCube. Compute NDVI first.")
        lst = cube.get("lst")
        ndvi = cube.get("ndvi")
        cwsi = self.compute_cwsi_lst(lst, ndvi)
        cube.add("cwsi_lst", cwsi)
        return cube


class TVDICalculator:
    """Temperature Vegetation Dryness Index.

    Dry edge: LST_max = a + b * NDVI fit to per-bin dry quantiles via polyfit.
    Wet edge: LST_min = quantile(LST, wet_quantile) (global).
    Formula: TVDI = (LST - LST_min) / (LST_max - LST_min)
    """

    def __init__(
        self,
        dry_quantile: float = 0.95,
        wet_quantile: float = 0.05,
        ndvi_bin_width: float = 0.02,
        ndvi_min: float = 0.2,
        ndvi_max: float = 0.9,
        clip: bool = True,
    ):
        self.dry_quantile = dry_quantile
        self.wet_quantile = wet_quantile
        self.ndvi_bin_width = ndvi_bin_width
        self.ndvi_min = ndvi_min
        self.ndvi_max = ndvi_max
        self.clip = clip

    def compute_tvdi(
        self,
        lst: xr.DataArray,
        ndvi: xr.DataArray,
    ) -> xr.DataArray:
        lst_v = lst.values.astype(float)
        ndvi_v = ndvi.values.astype(float)

        valid_lst = lst_v[np.isfinite(lst_v)]
        if valid_lst.size == 0:
            raise ValueError("No valid LST pixels for TVDI")

        lst_min = float(np.quantile(valid_lst, self.wet_quantile))

        centers, p95 = _bin_quantiles(
            ndvi_v, lst_v, self.ndvi_min, self.ndvi_max, self.ndvi_bin_width, self.dry_quantile
        )
        if centers.size < 2:
            raise ValueError("Not enough valid NDVI bins to fit TVDI dry edge")

        # Fit dry edge: LST_max = a + b * NDVI
        # polyfit returns [b, a]
        b, a = np.polyfit(centers, p95, 1)

        lst_max = a + b * ndvi_v

        with np.errstate(divide="ignore", invalid="ignore"):
            denom = lst_max - lst_min
            denom = np.where(denom == 0, np.nan, denom)
            tvdi = (lst_v - lst_min) / denom

        tvdi = np.where(np.isfinite(lst_v) & np.isfinite(ndvi_v), tvdi, np.nan)

        if self.clip:
            tvdi = np.clip(tvdi, 0.0, 1.0)

        da = xr.DataArray(tvdi, dims=lst.dims, coords=lst.coords)
        da.name = "tvdi"
        da.attrs = {
            "long_name": "Temperature Vegetation Dryness Index",
            "units": "dimensionless",
            "range": "[0, 1]",
            "method": "per-bin dry quantile + polyfit",
            "dry_quantile": self.dry_quantile,
            "wet_quantile": self.wet_quantile,
            "ndvi_bin_width": self.ndvi_bin_width,
            "ndvi_min": self.ndvi_min,
            "ndvi_max": self.ndvi_max,
            "dry_edge_a": float(a),
            "dry_edge_b": float(b),
            "lst_min": lst_min,
        }
        return da

    def compute(self, cube: DataCube) -> DataCube:
        if "lst" not in cube.bands():
            raise ValueError("lst not found in DataCube. Compute LST first.")
        if "ndvi" not in cube.bands():
            raise ValueError("ndvi not found in DataCube. Compute NDVI first.")
        lst = cube.get("lst")
        ndvi = cube.get("ndvi")
        tvdi = self.compute_tvdi(lst, ndvi)
        cube.add("tvdi", tvdi)
        return cube


# Aliases
CWSI_LST = CWSILSTCalculator
TVDI = TVDICalculator
