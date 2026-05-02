"""Product Organizer for METRIC ETa model.

This module provides functions to organize METRIC output products into
a structured directory hierarchy with metadata.

The expected output structure is:
    /products/
        /NDVI/
            NDVI_LC08_20200105_amirkabir.tif
            ...
        /ETrF/
            ETrF_LC08_20200105_amirkabir.tif
            ...
        /metadata/
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
    Organize METRIC output products into structured directories.
    
    This class handles:
    - Scanning output directories for products
    - Creating product-specific subdirectories
    - Moving products to appropriate folders
    - Generating metadata for each product
    """
    
    # Product type patterns for identification
    PRODUCT_PATTERNS = {
        'ETaDaily': r'ETaDaily.*\.tif$',
        'ETinst': r'ETinst.*\.tif$',
        'ETrF': r'ETrF.*\.tif$',
        'LE': r'LE.*\.tif$',
        'ETqualityClass': r'ETqualityClass.*\.tif$',
        'ETaClassified': r'ETaClassified.*\.tif$',
        'CWSI': r'CWSI.*\.tif$',
        'Rn': r'Rn.*\.tif$',
        'G': r'G.*\.tif$',
        'H': r'H.*\.tif$',
        'NDVI': r'NDVI.*\.tif$',
        'EVI': r'EVI.*\.tif$',
        'NDWI': r'NDWI.*\.tif$',
        'MNDWI': r'MNDWI.*\.tif$',
        'LAI': r'LAI.*\.tif$',
        'SAVI': r'SAVI.*\.tif$',
        'FVC': r'FVC.*\.tif$',
        'LST': r'LST.*\.tif$',
        'Albedo': r'Albedo.*\.tif$',
        'RGB': r'RGB.*\.tif$',
    }
    
    def __init__(
        self,
        output_dir: str,
        aoi_name: str = "AOI",
        create_metadata: bool = True
    ):
        """
        Initialize ProductOrganizer.
        
        Args:
            output_dir: Base output directory containing products
            aoi_name: Area of Interest name for file naming
            create_metadata: Whether to create metadata JSON files
        """
        self.output_dir = Path(output_dir)
        self.aoi_name = aoi_name
        self.create_metadata = create_metadata
        self.products_dir = self.output_dir / "products"
        self.metadata_dir = self.products_dir / "metadata"
        
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
        return organized
    
    def _create_directory_structure(self) -> None:
        """Create the products directory structure."""
        # Create main products directory
        self.products_dir.mkdir(parents=True, exist_ok=True)
        
        # Create metadata directory
        if self.create_metadata:
            self.metadata_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories for each product type
        for product_type in self.PRODUCT_PATTERNS.keys():
            product_dir = self.products_dir / product_type
            product_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Created directory structure in {self.products_dir}")
    
    def _scan_products(self) -> Dict[str, List[Path]]:
        """
        Scan output directory for product files.
        
        Returns:
            Dictionary mapping product types to lists of file paths
        """
        products = {}
        
        # Scan all .tif files in output directory and subdirectories
        for tif_file in self.output_dir.rglob("*.tif"):
            # Skip files already in products directory
            if "products" in tif_file.parts:
                continue
            
            # Identify product type
            product_type = self._identify_product_type(tif_file.name)
            
            if product_type:
                if product_type not in products:
                    products[product_type] = []
                products[product_type].append(tif_file)
        
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
            if re.search(pattern, filename):
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
        
        for src_file in files:
            try:
                # Generate new filename following naming convention
                new_filename = self._generate_product_filename(src_file.name, product_type)
                dst_file = product_dir / new_filename
                
                # Move file to product directory
                shutil.move(str(src_file), str(dst_file))
                organized_files.append(str(dst_file))
                
                logger.info(f"Moved {src_file.name} -> {product_type}/{new_filename}")
                
                # Create metadata if enabled
                if self.create_metadata:
                    self._create_product_metadata(dst_file, product_type)
                    
            except Exception as e:
                logger.error(f"Failed to organize {src_file}: {e}")
                continue
        
        return organized_files
    
    def _generate_product_filename(self, original_filename: str, product_type: str) -> str:
        """
        Generate new filename following the naming convention:
        {product}_{4chars_itemID}_{AOI}.tif
        
        Args:
            original_filename: Original filename
            product_type: Product type
            
        Returns:
            New filename string
        """
        # Extract item ID (scene ID) from original filename
        # Example: ETaDaily_landsat8_L2SP_30_LC08_20200105_amirkabir.tif
        # We want the LC08 part (first 4 chars of scene ID)
        
        # Try to extract scene ID from filename
        scene_match = re.search(r'(LC\d{2})', original_filename)
        if scene_match:
            scene_prefix = scene_match.group(1)  # e.g., LC08
        else:
            # Try alternative pattern
            scene_match = re.search(r'(LT\d{2})', original_filename)
            if scene_match:
                scene_prefix = scene_match.group(1)
            else:
                scene_prefix = "unknown"
        
        # Extract date if present
        date_match = re.search(r'(\d{8})', original_filename)
        date_str = date_match.group(1) if date_match else "unknown"
        
        # Extract AOI name from original filename or use default
        aoi = self.aoi_name
        aoi_match = re.search(r'_(amirkabir|AOI|[\w]+)\.tif$', original_filename)
        if aoi_match:
            aoi = aoi_match.group(1)
        
        # Build new filename: {product}_{scene_prefix}_{date}_{aoi}.tif
        new_filename = f"{product_type}_{scene_prefix}_{date_str}_{aoi}.tif"
        
        return new_filename
    
    def _create_product_metadata(self, product_file: Path, product_type: str) -> None:
        """
        Create metadata JSON for a product file.
        
        Args:
            product_file: Path to the product file
            product_type: Type of product
        """
        try:
            import rasterio
            
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
                data = src.read(1)
                import numpy as np
                valid_data = data[~np.isnan(data)] if np.issubdtype(data.dtype, np.floating) else data
                
                if len(valid_data) > 0:
                    metadata['statistics'] = {
                        'min': float(np.min(valid_data)),
                        'max': float(np.max(valid_data)),
                        'mean': float(np.mean(valid_data)),
                        'std': float(np.std(valid_data)),
                    }
            
            # Save metadata to JSON
            metadata_file = self.metadata_dir / f"{product_file.stem}_metadata.json"
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2, default=str)
            
            logger.info(f"Created metadata: {metadata_file.name}")
            
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
            
            summary_file = self.metadata_dir / "organization_summary.json"
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