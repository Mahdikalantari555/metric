"""Cloud Masking module for Landsat data.

This module provides cloud and cloud shadow detection functionality
using the Landsat QA pixel band.
"""

from typing import Optional, Tuple, Union

import numpy as np
import xarray as xr

from ..core.datacube import DataCube


class CloudMaskerError(Exception):
    """Base exception for CloudMasker errors."""
    pass


class CloudMasker:
    """
    Cloud and shadow detection using Landsat QA pixel band.
    
    This class implements Fmask-like cloud detection using the QA pixel band
    from Landsat Collection 2 Level-2 data.
    
    Attributes:
        cloud_confidence_threshold: Minimum confidence level for cloud detection
        dilate_pixels: Number of pixels to dilate cloud mask
        
    Example:
        >>> masker = CloudMasker()
        >>> mask = masker.create_mask(cube.get('qa_pixel'))
        >>> clear_cube = masker.apply_mask(cube, mask)
    """
    
    # QA pixel bit flags for Landsat 8/9 Collection 2
    # See: https://www.usgs.gov/landsat-missions/landsat-collection-2-level-2-quality-assessment-band
    QA_DILATED_CLOUD_BIT = 1
    QA_CLOUD_BIT = 3
    QA_CLOUD_SHADOW_BIT = 4
    QA_SNOW_BIT = 5
    QA_CLEAR_BIT = 6
    WATER_BIT = 7
    
    # Cloud confidence levels (bits 8-9)
    CONFIDENCE_LOW = 0
    CONFIDENCE_MEDIUM = 1
    CONFIDENCE_HIGH = 2
    CONFIDENCE_LCD = 3  # Low confidence cloud detection
    
    def __init__(
        self,
        cloud_confidence_threshold: int = CONFIDENCE_MEDIUM,
        dilate_pixels: int = 3,
        include_snow: bool = False,
        include_water: bool = True,
    ):
        """
        Initialize the CloudMasker.
        
        Args:
            cloud_confidence_threshold: Minimum cloud confidence level
                0 = Low, 1 = Medium, 2 = High, 3 = LCD
            dilate_pixels: Number of pixels to dilate cloud mask
            include_snow: Whether to mask snow as cloud
            include_water: Whether to treat water as clear (True) or cloud (False)
        """
        self.cloud_confidence_threshold = cloud_confidence_threshold
        self.dilate_pixels = dilate_pixels
        self.include_snow = include_snow
        self.include_water = include_water
    
    def create_mask(
        self,
        qa_pixel: Union[xr.DataArray, np.ndarray],
        confidence_override: Optional[int] = None,
    ) -> xr.DataArray:
        """
        Create a cloud mask from the QA pixel band.
        
        Args:
            qa_pixel: QA pixel band data array
            confidence_override: Optional override for cloud confidence threshold
            
        Returns:
            Boolean DataArray where True = clear, False = cloud/shadow
            
        Raises:
            CloudMaskerError: If input data is invalid
        """
        if qa_pixel is None:
            raise CloudMaskerError("QA pixel band is required")
        
        # Convert to numpy array with proper dtype
        if isinstance(qa_pixel, xr.DataArray):
            qa_values = qa_pixel.values
            # Ensure proper integer type for bit operations
            if qa_values.dtype.kind not in ['u', 'i']:
                qa_values = qa_values.astype(np.uint32)
            coords = qa_pixel.coords
            dims = qa_pixel.dims
        else:
            qa_values = np.asarray(qa_pixel)
            # Ensure proper integer type for bit operations
            if qa_values.dtype.kind not in ['u', 'i']:
                qa_values = qa_values.astype(np.uint32)
            coords = None
            dims = None
        
        # Check for fill (bit 0): fill pixels are never clear
        fill = (qa_values >> 0) & 1
        
        # Get confidence level from bits 8-9
        confidence = (qa_values >> 8) & 0b11
        
        # Check for dilated cloud (bit 1)
        dilated_cloud = (qa_values >> self.QA_DILATED_CLOUD_BIT) & 1
        
        # Check for cloud (bit 3)
        cloud = (qa_values >> self.QA_CLOUD_BIT) & 1
        
        # Check for cloud shadow (bit 4)
        cloud_shadow = (qa_values >> self.QA_CLOUD_SHADOW_BIT) & 1
        
        # Check for snow (bit 5)
        snow = (qa_values >> self.QA_SNOW_BIT) & 1
        
        # Check for water (bit 7)
        water = (qa_values >> self.WATER_BIT) & 1
        
        # Determine cloud confidence threshold
        threshold = confidence_override if confidence_override is not None else self.cloud_confidence_threshold
        
        # Cloud/shadow bits are authoritative; confidence only refines reporting.
        is_cloud = (cloud == 1) | (dilated_cloud == 1)
        
        # Initialize mask as clear (True)
        mask = np.ones(qa_values.shape, dtype=bool)
        # Fill (no-data) pixels are never clear
        mask = mask & (fill == 0)

        # Mark clouds and shadows as not clear
        mask = mask & ~is_cloud
        mask = mask & (cloud_shadow == 0)
        
        # Handle snow
        if not self.include_snow:
            mask = mask & (snow == 0)
        
        # Handle water: water is only clear where it is not already
        # cloud/shadow/snow/dilated-cloud. Never let water resurrect a bad pixel.
        if self.include_water:
            bad = is_cloud | (cloud_shadow == 1) | (dilated_cloud == 1) | (cloud == 1)
            if not self.include_snow:
                bad = bad | (snow == 1)
            water_clear = (water == 1) & ~bad
            mask = mask | water_clear
        else:
            # Water is masked
            mask = mask & (water == 0)
        
        # Dilate cloud mask to catch edge pixels
        if self.dilate_pixels > 0:
            mask = self._dilate_mask(mask, self.dilate_pixels)
        
        # Create output DataArray
        if coords is not None:
            result = xr.DataArray(mask, coords=coords, dims=dims)
        else:
            result = xr.DataArray(mask)
        
        return result
    
    def apply_mask(
        self,
        cube: DataCube,
        mask: xr.DataArray,
        fill_value: float = np.nan,
    ) -> DataCube:
        """
        Apply a cloud mask to a DataCube.
        
        Args:
            cube: Input DataCube
            mask: Cloud mask (True = clear, False = cloud)
            fill_value: Value to use for masked pixels
            
        Returns:
            New DataCube with masked data
            
        Raises:
            CloudMaskerError: If cube and mask dimensions don't match
        """
        if mask.shape != (cube.y_dim, cube.x_dim):
            raise CloudMaskerError(
                f"Mask shape {mask.shape} doesn't match cube shape "
                f"({cube.y_dim}, {cube.x_dim})"
            )
        
        # Create new DataCube
        masked_cube = DataCube()
        masked_cube.crs = cube.crs
        masked_cube.transform = cube.transform
        masked_cube.acquisition_time = cube.acquisition_time
        masked_cube.metadata = cube.metadata.copy()
        
        # Apply mask to each band
        for band_name, band_data in cube.data.items():
            if isinstance(band_data, xr.DataArray):
                # Apply mask, preserving coordinates
                masked_data = band_data.where(mask, other=fill_value)
                masked_cube.add(band_name, masked_data)
            else:
                masked_cube.add(band_name, band_data)
        
        return masked_cube
    
    def compute_cloud_coverage(self, cube: DataCube) -> float:
        """
        Compute the percentage of cloud cover in a DataCube.
        
        Args:
            cube: Input DataCube with 'qa_pixel' band
            
        Returns:
            Cloud coverage as percentage (0-100)
            
        Raises:
            CloudMaskerError: If qa_pixel band not found
        """
        qa_pixel = cube.get('qa_pixel')
        if qa_pixel is None:
            raise CloudMaskerError("qa_pixel band not found in DataCube")
        
        mask = self.create_mask(qa_pixel)
        
        # Calculate percentage of clear pixels
        total_pixels = mask.size
        clear_pixels = np.sum(mask)
        cloud_pixels = total_pixels - clear_pixels
        
        coverage = (cloud_pixels / total_pixels) * 100
        
        return float(coverage)
    
    def _dilate_mask(self, mask: np.ndarray, iterations: int) -> np.ndarray:
        """
        Dilate the cloud mask (False/clear regions become False where nearby
        cloud pixels exist). ``mask`` is True=clear; we dilate the cloud
        region (~mask) and invert.
        """
        if iterations <= 0:
            return mask

        cloud = ~np.asarray(mask, dtype=bool)
        dilated = cloud.copy()

        # Prefer scipy when available.
        try:
            from scipy.ndimage import binary_dilation

            structure = np.ones((3, 3), dtype=bool)
            dilated = binary_dilation(cloud, structure=structure, iterations=iterations)
        except ImportError:
            # Fast 8-neighbourhood fallback.
            for _ in range(iterations):
                nxt = dilated.copy()
                # orthogonal + diagonal shifts
                nxt[1:, :] |= dilated[:-1, :]
                nxt[:-1, :] |= dilated[1:, :]
                nxt[:, 1:] |= dilated[:, :-1]
                nxt[:, :-1] |= dilated[:, 1:]
                nxt[1:, 1:] |= dilated[:-1, :-1]
                nxt[:-1, :-1] |= dilated[1:, 1:]
                nxt[1:, :-1] |= dilated[:-1, 1:]
                nxt[:-1, 1:] |= dilated[1:, :-1]
                dilated = nxt

        return ~dilated
    
    def detect_cloud_shadow(
        self,
        nir: xr.DataArray,
        cloud_mask: xr.DataArray,
        sun_elevation: float,
        sun_azimuth: float,
    ) -> xr.DataArray:
        """
        Detect cloud shadows based on NIR darkening.
        
        This is a simplified shadow detection based on the assumption
        that cloud shadows appear as dark spots in NIR band.
        
        Args:
            nir: Near-infrared band DataArray
            cloud_mask: Cloud mask (True = clear)
            sun_elevation: Sun elevation angle in degrees
            sun_azimuth: Sun azimuth angle in degrees
            
        Returns:
            Shadow mask (True = shadow)
        """
        if not isinstance(nir, xr.DataArray):
            nir_values = nir
        else:
            nir_values = nir.values
        
        # Calculate local threshold for shadow detection
        # Shadow pixels have NIR values below local mean
        kernel_size = 7
        
        # Simple threshold-based shadow detection
        nir_mean = np.nanmean(nir_values)
        nir_std = np.nanstd(nir_values)
        
        # Shadow threshold (1 std below mean)
        shadow_threshold = nir_mean - 1.5 * nir_std
        
        # Create initial shadow mask
        shadow_mask = nir_values < shadow_threshold
        
        # Remove areas that are already identified as cloud
        shadow_mask = shadow_mask & cloud_mask.values
        
        # Dilate slightly
        shadow_mask = self._dilate_mask(shadow_mask, 1)
        
        # Create DataArray
        if isinstance(cloud_mask, xr.DataArray):
            result = xr.DataArray(
                shadow_mask,
                coords=cloud_mask.coords,
                dims=cloud_mask.dims
            )
        else:
            result = xr.DataArray(shadow_mask)
        
        return result
    
    def get_cloud_confidence_levels(self) -> dict:
        """
        Get the cloud confidence level mapping.
        
        Returns:
            Dictionary mapping confidence levels to descriptions
        """
        return {
            self.CONFIDENCE_LOW: "Low confidence - may be cloud or clear",
            self.CONFIDENCE_MEDIUM: "Medium confidence",
            self.CONFIDENCE_HIGH: "High confidence",
            self.CONFIDENCE_LCD: "Low confidence cloud detection",
        }


def create_cloud_mask(
    qa_pixel: Union[xr.DataArray, np.ndarray],
    cloud_confidence: int = CloudMasker.CONFIDENCE_MEDIUM,
    dilate_pixels: int = 3,
) -> xr.DataArray:
    """
    Convenience function to create a cloud mask.
    
    Args:
        qa_pixel: QA pixel band data
        cloud_confidence: Cloud confidence threshold
        dilate_pixels: Number of pixels to dilate
        
    Returns:
        Cloud mask (True = clear, False = cloud)
    """
    masker = CloudMasker(cloud_confidence_threshold=cloud_confidence, dilate_pixels=dilate_pixels)
    return masker.create_mask(qa_pixel)


# Alias for CloudMasker
CloudMask = CloudMasker
