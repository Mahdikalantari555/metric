"""Product Organizer for METRIC ETa model.

This module provides functions to organize METRIC output products into
a structured directory hierarchy with metadata.

The expected output structure is:
    /products/
        /ETaDaily/
            ETaDaily_LC08_20200105_amirkabir.tif
            ETaDaily_LC08_20200105_amirkabir_metadata.json
            ...
        /ETrF/
            ETrF_LC08_20200105_amirkabir.tif
            ETrF_LC08_20200105_amirkabir_metadata.json
            ...
        /NDVI/
            NDVI_LC08_20200105_amirkabir.tif
            NDVI_LC08_20200105_amirkabir_metadata.json
            ...
"""

import os
import json
import shutil
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from loguru import logger


class ProductOrganizer:
    """
    Organize METRIC ETa products into structured directories.
    
    This class handles:
    - Scanning output directories for products
    - Creating product-specific subdirectories
    - Moving products to appropriate folders
    - Generating metadata for each product
    """
    
    # Product type patterns for identification
    # Key: product folder name, Value: regex pattern to match filename
    PRODUCT_PATTERNS = {
        'ETaDaily': r'^(ETaDaily|ETa)_.+_\d{8}_',  # Matches ETaDaily_*.tif, ETaDaily_interpolated_*.tif
        'ETinst': r'^ETinst_',
        'ETrF': r'^ETrF_',
        'LE': r'^LE_',
        'ETqualityClass': r'^ETqualityClass_',
        'ETaClassified': r'^ETaClassified_',
        'CWSI': r'^CWSI_',
        'Rn': r'^Rn_',
        'G': r'^G_',
        'H': r'^H_',
        'NDVI': r'^NDVI_',
        'EVI': r'^EVI_',
        'LAI': r'^LAI_',
        'SAVI': r'^SAVI_',
        'FVC': r'^FVC_',
        'LST': r'^LST_',
        'Albedo': r'^Albedo_',
        'RGB': r'^RGB_',
        'AirTemp': r'^AirTemp_',
        'NDWI': r'^NDWI_',
    }
    
    def __init__(
        self,
        output_dir: str,
        aoi_name: str = "AOI",
        create_metadata: bool = True,
        metadata_in_product_folder: bool = True
    ):
        """
        Initialize ProductOrganizer.
        
        Args:
            output_dir: Base output directory containing products
            aoi_name: Area of Interest name for file naming
            create_metadata: Whether to create metadata JSON files
            metadata_in_product_folder: If True, save metadata in each product's folder.
                                                If False, save in a central metadata folder.
        """
        self.output_dir = Path(output_dir)
        self.aoi_name = aoi_name
        self.create_metadata = create_metadata
        self.metadata_in_product_folder = metadata_in_product_folder
        self.products_dir = self.output_dir / "products"
        self.metadata_dir = self.products_dir / "metadata" if not metadata_in_product_folder else None
    
    def organize(self) -> Dict[str, List[str]]:
        """
        Organize all products in the output directory.
        
        Returns:
            Dictionary mapping product types to lists of organized file paths
        """
        logger.info(f"Starting product organization in {self.output_dir}")
        
        # Create products directory structure
        self._create_directory_structure()
        
        # Scan for products
        products = self._scan_products()
        
        if not products:
            logger.warning(f"No products found in {self.output_dir}")
            logger.warning("DEBUG: Check if .tif files exist in subdirectories")
            # Debug: list all tif files found
            all_tifs = list(self.output_dir.rglob("*.tif"))
            logger.warning(f"DEBUG: Total .tif files found in output_dir: {len(all_tifs)}")
            for tif in all_tifs[:10]:  # Show first 10
                logger.warning(f"  - {tif}")
            return {}
        
        logger.info(f"Found {sum(len(v) for v in products.values())} products to organize")
        
        # Organize each product type
        organized = {}
        for product_type, files in products.items():
            organized[product_type] = self._organize_product_type(product_type, files)
        
        # Create summary metadata
        if self.create_metadata:
            self._create_summary_metadata(organized)
        
        logger.info(f"Product organization complete. Products saved to {self.products_dir}")
        logger.info(f"Organized products: {list(organized.keys())}")
        for pt, files in organized.items():
            logger.info(f"  {pt}: {len(files)} files")
        
        return organized
    
    def _create_directory_structure(self) -> None:
        """Create the products directory structure."""
        # Create main products directory
        self.products_dir.mkdir(parents=True, exist_ok=True)
        
        # Create metadata directory (only if not using per-product folders)
        if self.create_metadata and not self.metadata_in_product_folder:
            self.metadata_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories for each product type
        for product_type in self.PRODUCT_PATTERNS.keys():
            product_dir = self.products_dir / product_type
            product_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Created directory structure in {self.products_dir}")
        logger.info(f"Product folders created: {list(self.PRODUCT_PATTERNS.keys())}")
    
    def _scan_products(self) -> Dict[str, List[Path]]:
        """
        Scan output directory for product files.
        
        Returns:
            Dictionary mapping product types to lists of file paths
        """
        products = {}
        
        # Debug: Count all tif files first
        all_tif_files = list(self.output_dir.rglob("*.tif"))
        logger.debug(f"Total .tif files found: {len(all_tif_files)}")
        
        # Scan all .tif files in output directory and subdirectories
        for tif_file in self.output_dir.rglob("*.tif"):
            # Skip files already in products directory
            if "products" in tif_file.parts:
                continue
            
            # Skip PNG and JSON files
            if tif_file.suffix.lower() != '.tif':
                continue
            
            # Identify product type
            product_type = self._identify_product_type(tif_file.name)
            
            if product_type:
                if product_type not in products:
                    products[product_type] = []
                products[product_type].append(tif_file)
                logger.debug(f"Found {product_type}: {tif_file.name}")
            else:
                logger.debug(f"Unrecognized product file: {tif_file.name}")
        
        # Summary log
        if products:
            logger.info(f"Scan complete: Found products in {len(products)} categories")
            for pt, files in products.items():
                logger.info(f"  {pt}: {len(files)} files")
        else:
            logger.warning("No recognizable products found during scan")
        
        return products
    
    def _identify_product_type(self, filename: str) -> Optional[str]:
        """
        Identify the product type from filename.
        
        Args:
            filename: Name of the file
            
        Returns:
            Product type string or None if not recognized
        """
        for product_type, pattern in self.PRODUCT_PATTERNS.items():
            if re.match(pattern, filename, re.IGNORECASE):
                return product_type
        return None
    
    def _organize_product_type(self, product_type: str, files: List[Path]) -> List[str]:
        """
        Organize files for a specific product type.
        
        Args:
            product_type: Type of product (e.g., 'NDVI', 'ETrF')
            files: List of file paths to organize
            
        Returns:
            List of organized file paths
        """
        organized_files = []
        product_dir = self.products_dir / product_type
        
        # Ensure product directory exists
        product_dir.mkdir(parents=True, exist_ok=True)
        
        for src_file in files:
            try:
                # Skip if file doesn't exist (might have been moved already)
                if not src_file.exists():
                    logger.warning(f"File already moved or doesn't exist: {src_file}")
                    continue
                
                dst_file = product_dir / src_file.name
                
                # Handle case where destination already exists
                if dst_file.exists():
                    logger.warning(f"Destination already exists, skipping: {dst_file.name}")
                    continue
                
                # Move file to product directory
                shutil.move(str(src_file), str(dst_file))
                organized_files.append(str(dst_file))
                
                logger.info(f"Moved {src_file.name} -> products/{product_type}/")
                
                # Create metadata if enabled
                if self.create_metadata:
                    self._create_product_metadata(dst_file, product_type)
                    
            except Exception as e:
                logger.error(f"Failed to organize {src_file}: {e}")
                continue
        
        return organized_files
    
    def _create_product_metadata(self, product_file: Path, product_type: str) -> None:
        """
        Create metadata JSON for a product file.
        
        Args:
            product_file: Path to the product file
            product_type: Type of product
        """
        try:
            import rasterio
            import numpy as np
            
            metadata = {
                'product_name': product_file.stem,
                'product_type': product_type,
                'file_path': str(product_file),
                'file_size_bytes': product_file.stat().st_size,
                'creation_date': datetime.now().isoformat(),
            }
            
            # Read raster metadata using rasterio
            with rasterio.open(str(product_file)) as src:
                metadata['width'] = src.width
                metadata['height'] = src.height
                metadata['crs'] = str(src.crs)
                metadata['bounds'] = {
                    'left': src.bounds.left,
                    'bottom': src.bounds.bottom,
                    'right': src.bounds.right,
                    'top': src.bounds.top,
                }
                metadata['transform'] = src.transform.to_gdal()
                metadata['dtype'] = src.dtypes[0]
                metadata['nodata'] = src.nodata
                
                # Calculate statistics if possible
                try:
                    data = src.read(1)
                    if np.issubdtype(data.dtype, np.floating):
                        valid_data = data[~np.isnan(data)]
                    else:
                        valid_data = data[data != src.nodata] if src.nodata is not None else data.flatten()
                    
                    if len(valid_data) > 0:
                        metadata['statistics'] = {
                            'min': float(np.min(valid_data)),
                            'max': float(np.max(valid_data)),
                            'mean': float(np.mean(valid_data)),
                            'std': float(np.std(valid_data)),
                        }
                except Exception as stat_err:
                    logger.warning(f"Could not calculate statistics: {stat_err}")
            
            # Save metadata to JSON in the product folder (metadata_in_product_folder=True)
            metadata_file = product_file.parent / f"{product_file.stem}_metadata.json"
            
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2, default=str)
            
            logger.debug(f"Created metadata: {metadata_file.name}")
            
        except Exception as e:
            logger.error(f"Failed to create metadata for {product_file.name}: {e}")
    
    def _create_summary_metadata(self, organized: Dict[str, List[str]]) -> None:
        """
        Create summary metadata for all organized products.
        
        Args:
            organized: Dictionary of organized products
        """
        try:
            summary = {
                'organization_date': datetime.now().isoformat(),
                'source_directory': str(self.output_dir),
                'products_directory': str(self.products_dir),
                'aoi_name': self.aoi_name,
                'product_counts': {k: len(v) for k, v in organized.items()},
                'total_products': sum(len(v) for v in organized.values()),
            }
            
            # Save summary in products directory
            summary_file = self.products_dir / "organization_summary.json"
            with open(summary_file, 'w') as f:
                json.dump(summary, f, indent=2, default=str)
            
            logger.info(f"Created organization summary: {summary_file.name}")
            
        except Exception as e:
            logger.error(f"Failed to create summary metadata: {e}")


def organize_products(
    output_dir: str,
    aoi_name: str = "AOI",
    create_metadata: bool = True
) -> Dict[str, List[str]]:
    """
    Convenience function to organize products in output directory.
    
    Args:
        output_dir: Base output directory containing products
        aoi_name: Area of Interest name
        create_metadata: Whether to create metadata JSON files
        
    Returns:
        Dictionary mapping product types to lists of organized file paths
    """
    organizer = ProductOrganizer(
        output_dir=output_dir,
        aoi_name=aoi_name,
        create_metadata=create_metadata
    )
    return organizer.organize()


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python product_organizer.py <output_dir> [aoi_name]")
        sys.exit(1)
    
    output_dir = sys.argv[1]
    aoi_name = sys.argv[2] if len(sys.argv) > 2 else "AOI"
    
    result = organize_products(output_dir, aoi_name)
    
    print(f"\nOrganization complete!")
    print(f"Products organized: {sum(len(v) for v in result.values())}")
    for product_type, files in result.items():
        print(f"  {product_type}: {len(files)} files")