"""Unified METRIC Workflow Script.

This script integrates the complete METRIC workflow:
1. Download Landsat data from Planetary Computer
2. Calculate ET for all downloaded scenes
3. Interpolate/Extrapolate ET values
4. Sort products and create metadata

The workflow follows the final version described in the todo:
- Download from Planetary Computer
- Calculate ET for all downloaded scenes
- Interpolate and extrapolate for all scenes
- Sort products and create metadata
"""

import os
import shutil
import sys
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional

if 'PROJ_LIB' in os.environ:
    del os.environ['PROJ_LIB']

# Add metric_et to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'metric_et'))

from metric_et import METRICPipeline
from metric_et.io.planetary_computer_fetcher import PlanetaryComputerLandsatFetcher
from metric_et.output.product_organizer import organize_products
from metric_et.et.extrapolation import ETExtrapolator, create_extrapolator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add detailed console logging
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)
logging.getLogger().addHandler(console_handler)

logger.info("=" * 60)
logger.info("run_metric_workflow.py - STARTING")
logger.info("=" * 60)


class METRICWorkflow:
    """
    Unified workflow for METRIC ETa processing.
    
    This class orchestrates the complete workflow:
    1. Fetch Landsat scenes from Planetary Computer
    2. Calculate ET for each scene
    3. Interpolate/Extrapolate ET time series
    4. Organize products and create metadata
    """
    
    def __init__(
        self,
        roi_path: str,
        output_dir: str,
        start_date: str,
        end_date: str,
        aoi_name: str = None,
        max_cloud_cover: float = 50.0,
        source_crs: str = "EPSG:4326",
        interpolation_method: str = "weighted",
        extrapolation_days: int = 14,
        output_categories: Optional[List[str]] = None,
        products: Optional[List[str]] = None,
        save_scenes: bool = True,
        visualization: bool = False,
        min_coverage_ratio: float = 0.95
    ):
        """
        Initialize METRIC workflow.

        Args:
            roi_path: Path to ROI file (GeoJSON .geojson/.json or Shapefile .shp)
            output_dir: Base output directory
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            aoi_name: Area of Interest name for file naming
            max_cloud_cover: Maximum cloud cover percentage
            source_crs: CRS of input ROI (use UTM zone for better accuracy)
            interpolation_method: Method for ET interpolation ('linear' or 'weighted')
            extrapolation_days: Number of days to extrapolate beyond last scene
            output_categories: List of output category names to include. None uses standard preset.
            products: List of product names to generate. None = all products.
            save_scenes: Whether to retain the scenes/ folder after processing.
                         When False, scenes/ is deleted after product organization.
            visualization: Whether to emit overview_<date>.png and et_map_<date>.png.
                           Default False.
        """
        self.roi_path = roi_path
        # Derive AOI name from the ROI file basename (e.g. "test/Extent.geojson" -> "Extent")
        self.aoi_name = aoi_name or os.path.splitext(os.path.basename(roi_path))[0]
        self.output_dir = Path(output_dir).resolve()
        # Create output directory early to store temporary files if needed
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self._roi_geojson = None  # Will store the GeoJSON dict for later use
        
        # Validate ROI file (supports both GeoJSON and Shapefile)
        if not os.path.isfile(self.roi_path):
            raise FileNotFoundError(f"ROI file not found: {self.roi_path}")
        
        roi_ext = os.path.splitext(self.roi_path)[1].lower()
        
        if roi_ext in ('.geojson', '.json'):
            # Validate GeoJSON file
            try:
                with open(self.roi_path, 'r') as f:
                    roi_data = json.load(f)
            except Exception as e:
                raise ValueError(f"Failed to read ROI GeoJSON file '{self.roi_path}': {e}")

            # Basic GeoJSON structure validation - support all GeoJSON types
            if not isinstance(roi_data, dict):
                raise ValueError("ROI GeoJSON must be a JSON object")
            valid_toplevel = (
                "Feature", "FeatureCollection",
                "Polygon", "MultiPolygon", "GeometryCollection",
                "Point", "LineString", "MultiPoint", "MultiLineString"
            )
            roi_type = roi_data.get("type")
            if roi_type not in valid_toplevel:
                raise ValueError(
                    f"ROI GeoJSON has unsupported top-level type '{roi_type}'. "
                    f"Supported: {valid_toplevel}"
                )
            
            # Ensure there is at least one valid Polygon/MultiPolygon geometry
            def _has_valid_geometry(obj):
                if isinstance(obj, dict):
                    t = obj.get("type")
                    if t in ("Polygon", "MultiPolygon"):
                        return True
                    if t == "GeometryCollection":
                        return any(_has_valid_geometry(g) for g in obj.get("geometries", []))
                    if t == "Feature":
                        return _has_valid_geometry(obj.get("geometry", {}))
                    if t == "FeatureCollection":
                        return any(_has_valid_geometry(feat) for feat in obj.get("features", []))
                return False

            if not _has_valid_geometry(roi_data):
                raise ValueError("ROI GeoJSON does not contain a valid Polygon or MultiPolygon geometry")
            
            self._roi_geojson = roi_data
            
        elif roi_ext == '.shp':
            # Read Shapefile and convert to GeoJSON geometry
            try:
                import geopandas as gpd
                from shapely.geometry import shape, mapping
                from shapely.ops import unary_union
                
                gdf = gpd.read_file(self.roi_path)
                if len(gdf) == 0:
                    raise ValueError(f"Shapefile '{self.roi_path}' contains no features")
                
                # Union all geometries from the Shapefile
                if len(gdf) == 1:
                    combined_geom = gdf.geometry.iloc[0]
                else:
                    combined_geom = unary_union(gdf.geometry.tolist())
                
                # Convert to GeoJSON dict (just the geometry, not FeatureCollection)
                self._roi_geojson = mapping(combined_geom)
                
                # Validate the geometry
                if self._roi_geojson.get("type") not in ("Polygon", "MultiPolygon"):
                    raise ValueError("Converted Shapefile does not contain valid Polygon/MultiPolygon geometry")
                
                # Save as temporary GeoJSON file in output directory
                temp_geojson_path = self.output_dir / "temp_roi.geojson"
                with open(temp_geojson_path, 'w') as f:
                    json.dump(self._roi_geojson, f)
                self.roi_path = str(temp_geojson_path)
                logger.info(f"Loaded Shapefile ROI: {self.roi_path} ({len(gdf)} features)")
            except ImportError:
                raise ImportError(
                    f"geopandas is required to read Shapefile '{self.roi_path}'. "
                    "Install it with: pip install geopandas"
                )
            except Exception as e:
                raise ValueError(f"Failed to read ROI Shapefile '{self.roi_path}': {e}")
        else:
            raise ValueError(
                f"Unsupported ROI file format: '{roi_ext}'. "
                f"Supported formats: .geojson, .json, .shp"
            )
        
        self.start_date = start_date
        self.end_date = end_date
        self.aoi_name = aoi_name
        self.max_cloud_cover = max_cloud_cover
        self.source_crs = source_crs
        self.interpolation_method = interpolation_method
        self.extrapolation_days = extrapolation_days
        from metric_et.config.settings import OUTPUT_PRESETS
        if output_categories is None:
            self.output_categories = OUTPUT_PRESETS.get("standard", ["et_core", "energy_balance", "surface_props"])
        else:
            self.output_categories = output_categories
        self.products = products
        self.save_scenes = save_scenes
        self.visualization = visualization
        self.min_coverage_ratio = min_coverage_ratio

        # Create output subdirectories
        self.scenes_dir = self.output_dir / "scenes"
        self.scenes_dir.mkdir(parents=True, exist_ok=True)
        # Transient staging dir replaces the old per-date et_output/result_<date> folders.
        # Products land flat here, then are organized into output/products/.
        self.staging_dir = self.output_dir / "_work"
        self.staging_dir.mkdir(parents=True, exist_ok=True)
        # Final products root (populated from staging after organization).
        self.products_dir = self.output_dir / "products"

        logger.info(f"Initialized METRIC workflow")
        logger.info(f"ROI: {self.roi_path}")
        logger.info(f"Output directory: {output_dir}")
        logger.info(f"Date range: {start_date} to {end_date}")
        logger.info(f"AoI name: {aoi_name}")
        logger.info(f"Max cloud cover: {self.max_cloud_cover}%")
        logger.info(f"Source CRS: {self.source_crs}")
        logger.info(f"Interpolation method: {self.interpolation_method}")
        logger.info(f"Extrapolation days: {self.extrapolation_days}")
        logger.info(f"Output categories: {self.output_categories}")
        logger.info(f"Save scenes: {self.save_scenes}")
        logger.info(f"Visualization: {self.visualization}")
        logger.info(f"Scenes directory: {self.scenes_dir}")
        logger.info(f"Staging directory: {self.staging_dir}")
    
    def run(self) -> Dict:
        """
        Run the complete METRIC workflow.
        
        Returns:
            Dictionary with workflow results and statistics
        """
        logger.info("=" * 60)
        logger.info("STARTING UNIFIED METRIC WORKFLOW")
        logger.info("=" * 60)
        
        results = {
            'scenes_fetched': 0,
            'scenes_processed': 0,
            'scenes_failed': 0,
            'interpolation_dates': 0,
            'extrapolation_dates': 0,
            'products_organized': 0,
        }
        errors = []
        
        try:
            # Step 1: Fetch Landsat scenes
            logger.info("=" * 60)
            logger.info("STEP 1: Fetching Landsat scenes from Planetary Computer")
            logger.info("=" * 60)
            logger.info(f"Scenes directory: {self.scenes_dir}")
            
            scenes = self._fetch_scenes()
            results['scenes_fetched'] = len(scenes)
            logger.info(f"STEP 1 COMPLETE: Fetched {len(scenes)} scenes")
            
            if not scenes:
                logger.error("No scenes found. Workflow aborted.")
                return results
            
            logger.info(f"Fetched {len(scenes)} scenes")
            
            # Step 2: Calculate ET for all scenes
            logger.info("=" * 60)
            logger.info("STEP 2: Calculating ET for all scenes")
            logger.info("=" * 60)
            logger.info(f"Staging directory: {self.staging_dir}")

            processed_scenes = self._calculate_et_all(scenes)
            results['scenes_processed'] = len(processed_scenes)
            results['scenes_failed'] = len(scenes) - len(processed_scenes)
            logger.info(f"STEP 2 COMPLETE: Processed {len(processed_scenes)} scenes, {results['scenes_failed']} failed")

            if not processed_scenes:
                logger.error("No scenes processed successfully. Workflow aborted.")
                return results

            # Step 2b: Compute temporal stress indices from accumulated NDVI/LST
            logger.info("=" * 60)
            logger.info("STEP 2b: Computing temporal stress indices")
            logger.info("=" * 60)
            self._compute_temporal_indices(processed_scenes)
            logger.info("STEP 2b COMPLETE: Temporal indices computed")

            # Step 3: Interpolate and extrapolate ET FIRST
            # We must interpolate BEFORE organizing products because we need
            # to find ETrF files in the result_* directories first
            logger.info("=" * 60)
            logger.info("STEP 3: Interpolating and extrapolating ET")
            logger.info("=" * 60)
            
            interp_result, extrap_result = self._interpolate_et(processed_scenes)
            if interp_result:
                results['interpolation_dates'] = len(interp_result.get('dates', []))
                logger.info(f"Interpolated {results['interpolation_dates']} dates")
            if extrap_result:
                results['extrapolation_dates'] = len(extrap_result.get('dates', []))
                logger.info(f"Extrapolated {results['extrapolation_dates']} dates")
            logger.info(f"STEP 3 COMPLETE: Interpolation/extrapolation done")
            
            # Step 4: Organize ALL products (scene + interpolated)
            logger.info("=" * 60)
            logger.info("STEP 4: Organizing products and creating metadata")
            logger.info("=" * 60)

            organized = self._organize_products()
            results['products_organized'] = sum(len(v) for v in organized.values()) if organized else 0
            logger.info(f"STEP 4 COMPLETE: Organized {results['products_organized']} products")

            # Step 5: Finalize layout — promote staging products, relocate metadata,
            # handle visualization PNGs, optionally drop scenes, clean up staging.
            logger.info("=" * 60)
            logger.info("STEP 5: Finalizing output layout")
            logger.info("=" * 60)

            self._finalize_layout()

            # Optionally remove raw scene data
            if not self.save_scenes:
                logger.info("save_scenes=False: removing scenes directory")
                import shutil
                shutil.rmtree(self.scenes_dir, ignore_errors=True)

            # Summary
            logger.info("=" * 60)
            logger.info("WORKFLOW COMPLETED SUCCESSFULLY")
            logger.info("=" * 60)
            logger.info(f"Scenes fetched: {results['scenes_fetched']}")
            logger.info(f"Scenes processed: {results['scenes_processed']}")
            logger.info(f"Scenes failed: {results['scenes_failed']}")
            logger.info(f"Interpolation dates: {results['interpolation_dates']}")
            logger.info(f"Extrapolation dates: {results['extrapolation_dates']}")
            logger.info(f"Products organized: {results['products_organized']}")
            logger.info(f"Output directory: {self.output_dir}")

            # Save workflow summary
            self._save_workflow_summary(results, errors=errors)

            return results
            
        except Exception as e:
            logger.error(f"Workflow failed: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
    
    def _fetch_scenes(self) -> List[Dict]:
        """
        Fetch Landsat scenes from Planetary Computer.
        
        Returns:
            List of scene dictionaries
        """
        logger.info(f"Fetching scenes from {self.start_date} to {self.end_date}")
        logger.info(f"Max cloud cover: {self.max_cloud_cover}%")
        logger.info(f"Source CRS: {self.source_crs}")
        
        # Initialize fetcher
        fetcher = PlanetaryComputerLandsatFetcher(
            max_cloud_cover=self.max_cloud_cover,
            source_crs=self.source_crs,
        )
        
        # Load ROI (use pre-loaded GeoJSON from __init__)
        if self._roi_geojson is None:
            raise ValueError("ROI geometry not loaded. Check ROI file path and format.")
        
        # Normalize geometry
        roi_geometry = fetcher._normalize_geometry(self._roi_geojson)
        
        # Get ROI bounds for STAC query
        from shapely.geometry import shape
        roi_shapely = shape(roi_geometry)
        roi_bbox = list(roi_shapely.bounds)
        
        # Search for scenes
        start = datetime.strptime(self.start_date, '%Y-%m-%d')
        end = datetime.strptime(self.end_date, '%Y-%m-%d')
        
        # Use pystac_client for search
        search_params = {
            "collections": [fetcher.collection],
            "bbox": roi_bbox,
            "datetime": f"{start.isoformat()}/{end.isoformat()}",
            "limit": 100,
        }
        
        # Add platform filter for Landsat 8 and 9
        search_params["query"] = {
            "platform": {
                "in": ["landsat-8", "landsat-9"]
            }
        }
        
        try:
            search = fetcher.client.search(**search_params)
            items = list(search.items())
            logger.info(f"Found {len(items)} Landsat 8/9 scene(s) matching criteria")
        except Exception as e:
            logger.warning(f"STAC search with platform filter failed: {e}")
            # Fallback: search without platform filter
            del search_params["query"]
            search = fetcher.client.search(**search_params)
            items = list(search.items())
        
        # Filter by cloud cover
        filtered_items = []
        for item in items:
            cloud_cover = item.properties.get('eo:cloud_cover') or item.properties.get('cloud_cover', 0.0)
            if cloud_cover <= self.max_cloud_cover:
                filtered_items.append(item)
            else:
                logger.info(f"Filtered out {item.id}: cloud cover {cloud_cover}% > {self.max_cloud_cover}%")
        
        # Sort by date
        filtered_items.sort(key=lambda item: item.datetime)
        
        logger.info(f"Found {len(filtered_items)} scenes with cloud cover <= {self.max_cloud_cover}%")
        
        if not filtered_items:
            logger.warning("No Landsat 8/9 scenes found matching criteria")
            return []
        
        # Download each scene
        scenes = []
        for item in filtered_items:
            scene_date = item.properties["datetime"][:10]
            path = item.properties.get('landsat:wrs_path')
            row = item.properties.get('landsat:wrs_row')
            
            # Create scene directory
            scene_dir = self.scenes_dir / f"landsat_{scene_date.replace('-', '')}_{path}_{row}"
            scene_dir.mkdir(parents=True, exist_ok=True)
            
            try:
                # Skip download if all required bands + MTL.json already exist
                existing = fetcher._find_existing_scene(scene_dir)
                if existing is not None:
                    downloaded_files, mtl_path = existing
                    logger.info(f"Scene {item.id} already downloaded, skipping: {scene_dir}")
                else:
                    downloaded_files = fetcher.download_and_clip_bands(
                        item, roi_bbox, scene_dir, 30.0, self.min_coverage_ratio
                    )
                    mtl_path = fetcher._create_mtl_metadata(item, scene_dir)
                
                scenes.append({
                    "scene_id": item.id,
                    "date": scene_date,
                    "cloud_cover": item.properties.get('eo:cloud_cover'),
                    "path": path,
                    "row": row,
                    "directory": str(scene_dir),
                    "bands_downloaded": len(downloaded_files),
                    "mtl_file": str(mtl_path),
                    "band_files": downloaded_files
                })
                logger.info(f"Scene ready: {item.id} for {scene_date}")
                
            except Exception as e:
                logger.warning(f"Failed to download scene {item.id}: {e}")
                if scene_dir.exists():
                    shutil.rmtree(scene_dir, ignore_errors=True)
                    logger.info(f"Removed incomplete scene directory: {scene_dir}")
                continue
        
        logger.info(f"Successfully fetched {len(scenes)} scene(s)")
        return scenes
    
    def _calculate_et_all(self, scenes: List[Dict]) -> List[Dict]:
        """
        Calculate ET for all downloaded scenes.
        
        Args:
            scenes: List of scene dictionaries from _fetch_scenes()
            
        Returns:
            List of successfully processed scene dictionaries
        """
        logger.info("=" * 60)
        logger.info("_calculate_et_all() - STARTING")
        logger.info("=" * 60)
        logger.info(f"Processing {len(scenes)} scenes with METRIC pipeline")
        
        processed = []
        scene_num = 0
        
        for scene in scenes:
            scene_num += 1
            scene_id = scene['scene_id']
            scene_date = scene['date']
            scene_dir = scene['directory']
            
            logger.info("-" * 60)
            logger.info(f"Scene {scene_num}/{len(scenes)}: {scene_id}")
            logger.info(f"Scene date: {scene_date}")
            logger.info(f"Scene directory: {scene_dir}")
            
            try:
                # Configure pipeline
                config = {
                    'calibration': {
                        'method': 'automatic'
                    },
                    'output_products': self.products,
                    'output_categories': self.output_categories,
                    'aoi_name': self.aoi_name
                }
                logger.info(f"Pipeline config: {config}")
                
                # Run METRIC pipeline
                logger.info("Initializing METRICPipeline...")
                pipeline = METRICPipeline(config=config)
                
                # Transient per-scene staging directory (cleaned up in _finalize_layout).
                scene_output_dir = self.staging_dir / f"result_{scene_date.replace('-', '')}"
                logger.info(f"Scene output directory: {scene_output_dir}")

                # Run pipeline
                logger.info("Running pipeline.run()...")
                results = pipeline.run(
                    landsat_dir=scene_dir,
                    meteo_data={},  # Pipeline will fetch weather dynamically
                    output_dir=str(scene_output_dir),
                    roi_path=self.roi_path,
                    save_visualization=self.visualization
                )
                logger.info(f"Pipeline.run() completed, results: {results}")
                
                # Check if output directory has products
                if scene_output_dir.exists():
                    tif_files = list(scene_output_dir.glob("*.tif"))
                    logger.info(f"Scene {scene_id} produced {len(tif_files)} .tif files")
                    for tif_file in tif_files:
                        logger.info(f"  - {tif_file.name}")
                    if len(tif_files) == 0:
                        logger.warning(f"Scene {scene_id} - no .tif files in output directory!")
                else:
                    logger.warning(f"Scene {scene_id} - output directory does not exist: {scene_output_dir}")
                
                scene['et_output_dir'] = str(scene_output_dir)
                scene['et_results'] = {k: str(v) for k, v in results.items()} if results else {}
                scene['_cube'] = pipeline.data  # Store cube for temporal index computation
                
                processed.append(scene)
                logger.info(f"Successfully processed {scene_date} ({scene_id})")
                
            except Exception as e:
                import traceback
                logger.error(f"Failed to process scene {scene_id} for {scene_date}: {e}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                continue
        
        logger.info(f"Successfully processed {len(processed)} out of {len(scenes)} scenes")
        
        # Log failed scenes
        if len(processed) < len(scenes):
            failed_scenes = [s['scene_id'] for s in scenes if s not in processed]
            logger.warning(f"Failed scenes: {failed_scenes}")
        
        logger.info("_calculate_et_all() - COMPLETED")
        return processed

    def _compute_temporal_indices(self, processed_scenes: List[Dict]) -> None:
        """Compute temporal stress indices (TCI, VCI, VHI) from accumulated NDVI/LST.

        Accumulates ndvi and lst from each scene dict, builds min/max stacks,
        then computes and attaches vci, tci, vhi DataArrays back to each scene's DataCube.
        TCI uses the last scene's LST as the instantaneous value.
        """
        import numpy as np
        import xarray as xr
        from metric_et.surface.temporal_stress import TCI, VCI, VHI

        if not processed_scenes:
            logger.warning("No processed scenes for temporal indices")
            return

        # Gather ndvi and lst from each scene's DataCube
        ndvi_stacks = []
        lst_stacks = []
        for scene in processed_scenes:
            cube = scene.get('_cube')
            if cube is None:
                continue
            if 'ndvi' in cube.bands() and 'lst' in cube.bands():
                ndvi_stacks.append(cube.get('ndvi').values)
                lst_stacks.append(cube.get('lst').values)

        if len(ndvi_stacks) < 1 or len(lst_stacks) < 1:
            logger.warning("Insufficient scenes with ndvi/lst for temporal indices")
            return

        ndvi_stack = np.stack(ndvi_stacks, axis=0)
        lst_stack = np.stack(lst_stacks, axis=0)

        ndvi_min = np.nanmin(ndvi_stack, axis=0)
        ndvi_max = np.nanmax(ndvi_stack, axis=0)
        lst_min = np.nanmin(lst_stack, axis=0)
        lst_max = np.nanmax(lst_stack, axis=0)

        # Create DataArrays for min/max
        first_cube = next((s['_cube'] for s in processed_scenes if '_cube' in s), None)
        if first_cube is None:
            logger.warning("No valid cube found for temporal index coords")
            return

        dims = first_cube.get('ndvi').dims
        coords = first_cube.get('ndvi').coords

        ndvi_min_da = xr.DataArray(ndvi_min, dims=dims, coords=coords)
        ndvi_max_da = xr.DataArray(ndvi_max, dims=dims, coords=coords)
        lst_min_da = xr.DataArray(lst_min, dims=dims, coords=coords)
        lst_max_da = xr.DataArray(lst_max, dims=dims, coords=coords)

        # Attach min/max to each scene's cube
        for scene in processed_scenes:
            cube = scene.get('_cube')
            if cube is None:
                continue
            cube.add('ndvi_min', ndvi_min_da)
            cube.add('ndvi_max', ndvi_max_da)
            cube.add('lst_min', lst_min_da)
            cube.add('lst_max', lst_max_da)

        # Compute TCI using last scene's LST as instantaneous value
        last_scene = processed_scenes[-1]
        last_cube = last_scene.get('_cube')
        if last_cube and 'lst' in last_cube.bands():
            tci_calc = TCI()
            tci_result = tci_calc.compute(
                last_cube.get('lst'), lst_min_da, lst_max_da
            )
            last_cube.add('tci', tci_result)
            logger.info(f"TCI computed for last scene, valid pixels: {np.sum(np.isfinite(tci_result.values))}")

        # Compute VCI using last scene's NDVI
        if last_cube and 'ndvi' in last_cube.bands():
            vci_calc = VCI()
            vci_result = vci_calc.compute(
                last_cube.get('ndvi'), ndvi_min_da, ndvi_max_da
            )
            last_cube.add('vci', vci_result)
            logger.info(f"VCI computed for last scene, valid pixels: {np.sum(np.isfinite(vci_result.values))}")

        # Compute VHI from TCI and VCI on last scene
        if last_cube and 'tci' in last_cube.bands() and 'vci' in last_cube.bands():
            vhi_calc = VHI()
            vhi_result = vhi_calc.compute(
                last_cube.get('vci'), last_cube.get('tci')
            )
            last_cube.add('vhi', vhi_result)
            logger.info(f"VHI computed for last scene, valid pixels: {np.sum(np.isfinite(vhi_result.values))}")

        logger.info(f"Temporal indices computed across {len(processed_scenes)} scenes")

    def _interpolate_et(self, processed_scenes: List[Dict]) -> tuple:
        """
        Interpolate and extrapolate ET for processed scenes.
        
        Args:
            processed_scenes: List of successfully processed scenes
            
        Returns:
            Tuple of (interpolation_result, extrapolation_result)
        """
        if len(processed_scenes) < 2:
            logger.warning("Need at least 2 scenes for interpolation")
            return None, None
        
        logger.info(f"Interpolating ET for {len(processed_scenes)} scenes")
        
        try:
            # Import interpolation modules
            from metric_et.et.extrapolation import ETExtrapolator, create_extrapolator
            import rasterio
            import numpy as np
            from pathlib import Path
            
            # Get CRS from first scene's ETrF file for coordinate transformation
            first_scene = processed_scenes[0]
            first_output_dir = Path(first_scene['et_output_dir'])
            etrf_files = list(first_output_dir.glob("ETrF_*.tif"))
            
            source_crs = None
            if etrf_files:
                with rasterio.open(etrf_files[0]) as src:
                    source_crs = str(src.crs)
            
            # Initialize extrapolator with CRS info
            extrapolator = create_extrapolator({
                "extrapolation_days": self.extrapolation_days,
                "interpolation_method": self.interpolation_method,
                "min_et_daily": 0.0,
                "max_et_daily": 20.0,
                "etrf_min": 0.0,
                "etrf_max": 1.5,
                "source_crs": source_crs
            })
            
            # Load ETrF scenes for interpolation
            etrf_scenes = []
            scene_dates = []
            
            for scene in processed_scenes:
                scene_output_dir = Path(scene['et_output_dir'])
                
                # Find ETrF file
                etrf_files = list(scene_output_dir.glob("ETrF_*.tif"))
                if not etrf_files:
                    logger.warning(f"No ETrF file found in {scene_output_dir}")
                    continue
                
                etrf_file = etrf_files[0]
                scene_date = scene['date']
                
                # Load ETrF raster
                with rasterio.open(etrf_file) as src:
                    etrf_data = src.read(1)
                    etrf_data = np.where(etrf_data == src.nodata, np.nan, etrf_data)
                
                # Parse date
                date = datetime.strptime(scene_date, '%Y-%m-%d')
                
                etrf_scenes.append((date, etrf_data))
                scene_dates.append(date)
            
            if len(etrf_scenes) < 2:
                logger.warning("Need at least 2 valid ETrF scenes for interpolation")
                return None, None
            
            # Sort by date
            etrf_scenes.sort(key=lambda x: x[0])
            scene_dates.sort()
            
            # Fetch ET0 data for interpolation/extrapolation
            logger.info("Fetching ET0 data for interpolation period")
            
            first_date = scene_dates[0]
            last_date = scene_dates[-1] + timedelta(days=self.extrapolation_days)
            
            start_date_str = first_date.strftime('%Y-%m-%d')
            end_date_str = last_date.strftime('%Y-%m-%d')
            
            # Get bbox from first scene
            first_scene = processed_scenes[0]
            first_output_dir = Path(first_scene['et_output_dir'])
            etrf_files = list(first_output_dir.glob("ETrF_*.tif"))
            
            if etrf_files:
                with rasterio.open(etrf_files[0]) as src:
                    bounds = src.bounds
                    bbox = [bounds.left, bounds.bottom, bounds.right, bounds.top]
            else:
                bbox = [51.0, 35.0, 52.0, 36.0]  # Default Tehran area
            
            try:
                et0_data = extrapolator.fetch_et0_historical(
                    bbox=bbox,
                    start_date=start_date_str,
                    end_date=end_date_str
                )
            except Exception as e:
                logger.warning(f"Failed to fetch ET0 data: {e}")
                # Generate synthetic ET0
                import pandas as pd
                dates = pd.date_range(start=first_date, end=last_date, freq='D')
                et0_values = 5.0 + 2.5 * np.sin(2 * np.pi * (np.arange(len(dates)) - 105) / 365)
                et0_data = __import__('xarray').DataArray(
                    et0_values,
                    dims=['time'],
                    coords={'time': dates},
                    attrs={'units': 'mm/day'}
                )
            
            # Perform interpolation
            logger.info("Performing ET interpolation")
            interp_result = extrapolator.interpolate(
                etrf_scenes=etrf_scenes,
                et0_data=et0_data,
                method=self.interpolation_method,
                gap_threshold=30
            )
            
            # Perform extrapolation
            logger.info("Performing ET extrapolation")
            last_scene = etrf_scenes[-1]
            last_date = last_scene[0]
            last_etrf = last_scene[1]
            
            # Get ET0 for forecast period
            forecast_start = last_date + timedelta(days=1)
            forecast_end = last_date + timedelta(days=self.extrapolation_days)
            
            try:
                et0_forecast = et0_data.sel(
                    time=slice(forecast_start.strftime('%Y-%m-%d'), 
                              forecast_end.strftime('%Y-%m-%d'))
                )
            except Exception as e:
                logger.warning(f"Could not select forecast ET0: {e}")
                et0_forecast = None
            
            extrap_result = None
            if et0_forecast is not None and len(et0_forecast) > 0:
                extrap_result = extrapolator.extrapolate(
                    etrf_last=last_etrf,
                    et0_forecast=et0_forecast
                )
            
            # Save interpolated/extrapolated results
            if interp_result:
                logger.info(f"Saving {len(interp_result.get('dates', []))} interpolated files")
                self._save_interpolated_results(interp_result, "interpolated")
            
            if extrap_result:
                logger.info(f"Saving {len(extrap_result.get('dates', []))} extrapolated files")
                self._save_interpolated_results(extrap_result, "extrapolated")
            
            logger.info("Interpolation and extrapolation completed")
            return interp_result, extrap_result
            
        except Exception as e:
            import traceback
            error_msg = f"Interpolation/extrapolation failed: {e}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            # errors list is owned by run(); avoid NameError here and let run() handle reporting
            return None, None
    
    def _save_interpolated_results(self, result: Dict, prefix: str) -> None:
        """
        Save interpolated or extrapolated results to ETaDaily product folder.
        Files are saved with _interpolated or _extrapolated suffix.
        
        Args:
            result: Interpolation/extrapolation result dictionary
            prefix: Prefix for filenames ('interpolated' or 'extrapolated')
        """
        import rasterio
        import numpy as np
        from pathlib import Path
        
        if not result or 'dates' not in result:
            return
        
        dates = result['dates']
        eta_daily = result.get('ETa_daily')
        
        if eta_daily is None or len(dates) == 0:
            return
        
        # Get reference raster for spatial info
        # Use first scene's ETrF file
        first_scene = list(self.staging_dir.glob("*/ETrF_*.tif"))[0]

        with rasterio.open(first_scene) as src:
            crs = src.crs
            transform = src.transform
            height = src.height
            width = src.width

        # Save directly to ETaDaily product folder
        eta_daily_product_dir = self.staging_dir / "products" / "ETaDaily"
        eta_daily_product_dir.mkdir(parents=True, exist_ok=True)
        
        # Save each date's result
        for i, date in enumerate(dates):
            if i >= len(eta_daily):
                break
            
            eta_data = eta_daily[i]
            
            date_str = date.strftime('%Y%m%d') if hasattr(date, 'strftime') else str(date).replace('-', '')
            
            # Save in ETaDaily folder with _interpolated or _extrapolated suffix
            output_file = eta_daily_product_dir / f"ETaDaily_{prefix}_{date_str}_{self.aoi_name}.tif"
            
            with rasterio.open(
                output_file,
                'w',
                driver='GTiff',
                height=height,
                width=width,
                count=1,
                dtype='float32',
                crs=crs,
                transform=transform,
                compress='lzw',
                nodata=np.nan
            ) as dst:
                dst.write(eta_data.astype('float32'), 1)
            
            logger.info(f"Saved {prefix} ETa for {date_str}: {output_file.name}")
    
    def _organize_products(self) -> Dict:
        """
        Organize all products and create metadata.
        Metadata is saved in each product's folder.
        
        Returns:
            Dictionary mapping product types to lists of organized file paths
        """
        logger.info("Organizing products and creating metadata")
        
        try:
            # Organize ET output products (metadata_in_product_folder=True)
            organized = organize_products(
                output_dir=str(self.staging_dir),
                aoi_name=self.aoi_name,
                create_metadata=True
            )

            logger.info(f"Organized {sum(len(v) for v in organized.values())} products")
            return organized
            
        except Exception as e:
            logger.error(f"Product organization failed: {e}")
            return {}

    def _finalize_layout(self) -> None:
        """
        Promote organized products from staging to the final output/products/
        folder, relocate scene metadata to products/metadata/, move visualization
        PNGs to products/visualizations/, and remove the transient staging dir.
        """
        import shutil

        staging_products = self.staging_dir / "products"

        # 1. Promote products to final output/products/
        if staging_products.exists():
            if self.products_dir.exists():
                shutil.rmtree(self.products_dir)
            shutil.move(str(staging_products), str(self.products_dir))
            logger.info(f"Promoted products -> {self.products_dir}")

        # 2. Relocate scene metadata (metadata_*.json) to products/metadata/
        #    with META_ prefix and .geojson extension.
        metadata_dir = self.products_dir / "metadata"
        metadata_dir.mkdir(parents=True, exist_ok=True)
        for meta_file in self.staging_dir.rglob("metadata_*.json"):
            new_name = "META_" + meta_file.stem[len("metadata"):] + ".geojson"
            dest = metadata_dir / new_name
            shutil.move(str(meta_file), str(dest))
            logger.info(f"Relocated scene metadata: {meta_file.name} -> metadata/{new_name}")

        # 3. Move visualization PNGs to products/visualizations/
        viz_dir = self.products_dir / "visualizations"
        for pattern in ("overview_*.png", "et_map_*.png"):
            for png_file in self.staging_dir.rglob(pattern):
                if not viz_dir.exists():
                    viz_dir.mkdir(parents=True, exist_ok=True)
                dest = viz_dir / png_file.name
                shutil.move(str(png_file), str(dest))
                logger.info(f"Moved visualization: {png_file.name} -> visualizations/")

        # 4. Remove transient staging dir
        shutil.rmtree(self.staging_dir, ignore_errors=True)
        logger.info(f"Removed staging directory: {self.staging_dir}")

    def _organize_interpolated_products(self) -> Dict:
        """
        Organize only ETaDaily products in the interpolated directory.
        Interpolation should only be applied to ETaDaily, not other products.
        
        Returns:
            Dictionary with 'ETaDaily' key mapping to list of organized file paths
        """
        logger.info("Organizing interpolated ETaDaily products only")
        
        try:
            from metric_et.output.product_organizer import ProductOrganizer
            
            # Only organize ETaDaily (interpolation only applies to ETaDaily)
            organizer = ProductOrganizer(
                output_dir=str(self.interpolated_dir),
                aoi_name=self.aoi_name,
                create_metadata=True
            )
            
            # Override PRODUCT_PATTERNS to only include ETaDaily
            organizer.PRODUCT_PATTERNS = {
                'ETaDaily': r'ETa.*\.tif$',
            }
            
            result = organizer.organize()
            logger.info(f"Organized interpolated products: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Interpolated product organization failed: {e}")
            return {}
    
    def _save_workflow_summary(self, results: Dict, errors: Optional[List[str]] = None) -> None:
        """
        Save workflow summary to JSON file.
        
        Args:
            results: Workflow results dictionary
            errors: Optional list of error messages encountered during workflow
        """
        summary = {
            'workflow_completion_time': datetime.now().isoformat(),
            'roi_path': self.roi_path,
            'output_dir': str(self.output_dir),
            'date_range': {
                'start': self.start_date,
                'end': self.end_date
            },
            'aoi_name': self.aoi_name,
            'max_cloud_cover': self.max_cloud_cover,
            'source_crs': self.source_crs,
            'interpolation_method': self.interpolation_method,
            'extrapolation_days': self.extrapolation_days,
            'include_surface_properties': self.include_surface,
            'results': results,
            'errors': errors or []
        }
        
        summary_file = self.output_dir / "workflow_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        logger.info(f"Workflow summary saved: {summary_file}")


def main():
    """Main function for command-line usage."""
    import argparse
    
    logger.info("=" * 60)
    logger.info("run_metric_workflow.py main() - STARTING")
    logger.info("=" * 60)
    
    parser = argparse.ArgumentParser(
        description='Run unified METRIC workflow for ETa processing'
    )
    
    parser.add_argument(
        '--roi', type=str, required=True,
        help='Path to ROI file (GeoJSON .geojson/.json or Shapefile .shp)'
    )
    parser.add_argument(
        '--output', type=str, required=True,
        help='Output directory'
    )
    parser.add_argument(
        '--start-date', type=str, required=True,
        help='Start date (YYYY-MM-DD)'
    )
    parser.add_argument(
        '--end-date', type=str, required=True,
        help='End date (YYYY-MM-DD)'
    )
    parser.add_argument(
        '--aoi-name', type=str, default='AOI',
        help='Area of Interest name for file naming'
    )
    parser.add_argument(
        '--max-cloud', type=float, default=50.0,
        help='Maximum cloud cover percentage (default: 50.0)'
    )
    parser.add_argument(
        '--source-crs', type=str, default='EPSG:4326',
        help='CRS of input ROI (default: EPSG:4326)'
    )
    parser.add_argument(
        '--interpolation-method', type=str, default='weighted',
        choices=['linear', 'weighted'],
        help='Interpolation method (default: weighted)'
    )
    parser.add_argument(
        '--extrapolation-days', type=int, default=14,
        help='Number of days to extrapolate (default: 14)'
    )
    parser.add_argument(
        '--output-categories', type=str, default=None,
        help='Comma-separated list of output categories (e.g. "et_core,spectral_indices,stress_indices"). '
             'Available: et_core, energy_balance, quality, surface_props, radiation, spectral_indices, stress_indices. '
             'Default: standard preset.'
    )
    parser.add_argument(
        '--products', type=str, default=None,
        help='Comma-separated list of products to generate (e.g., "ETaDaily,ETrF,NDVI,LST"). '
             'If not specified, all products are generated.'
    )
    parser.add_argument(
        '--save-scenes', action=argparse.BooleanOptionalAction, default=True,
        help='Keep the scenes/ folder after processing (default: on). '
             'Use --no-save-scenes to delete it after product organization.'
    )
    parser.add_argument(
        '--visualization', action=argparse.BooleanOptionalAction, default=False,
        help='Emit overview_<date>.png and et_map_<date>.png visualizations '
             '(default: off). Use --visualization to enable.'
    )

    args = parser.parse_args()

    # Parse products list
    products = None
    if args.products:
        products = [p.strip() for p in args.products.split(',')]

    # Create and run workflow
    workflow = METRICWorkflow(
        roi_path=args.roi,
        output_dir=args.output,
        start_date=args.start_date,
        end_date=args.end_date,
        aoi_name=args.aoi_name,
        max_cloud_cover=args.max_cloud,
        source_crs=args.source_crs,
        interpolation_method=args.interpolation_method,
        extrapolation_days=args.extrapolation_days,
        output_categories=[c.strip() for c in args.output_categories.split(',')] if args.output_categories else None,
        products=products,
        save_scenes=args.save_scenes,
        visualization=args.visualization
    )
    
    results = workflow.run()
    
    logger.info("=" * 60)
    logger.info("METRIC WORKFLOW COMPLETED")
    logger.info("=" * 60)
    logger.info(f"Scenes fetched: {results['scenes_fetched']}")
    logger.info(f"Scenes processed: {results['scenes_processed']}")
    logger.info(f"Scenes failed: {results['scenes_failed']}")
    logger.info(f"Interpolation dates: {results['interpolation_dates']}")
    logger.info(f"Extrapolation dates: {results['extrapolation_dates']}")
    logger.info(f"Products organized: {results['products_organized']}")
    logger.info("=" * 60)
    
    print("\n" + "=" * 60)
    print("METRIC WORKFLOW COMPLETED")
    print("=" * 60)
    print(f"Scenes fetched: {results['scenes_fetched']}")
    print(f"Scenes processed: {results['scenes_processed']}")
    print(f"Scenes failed: {results['scenes_failed']}")
    print(f"Interpolation dates: {results['interpolation_dates']}")
    print(f"Extrapolation dates: {results['extrapolation_dates']}")
    print(f"Products organized: {results['products_organized']}")
    print("=" * 60)


if __name__ == "__main__":
    main()