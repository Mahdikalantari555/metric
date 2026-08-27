# METRIC Automation Sentinel - API Guide

This guide provides comprehensive documentation for the command-line interfaces (CLI) for processing both Sentinel-2 and Landsat satellite data using the METRIC (Mapping Evapotranspiration with Internalized Calibration) model.

## Table of Contents

1. [Sentinel-2 Processing](#1-sentinel-2-processing)
2. [Landsat Processing](#2-landsat-processing)
3. [Automation System Commands](#3-automation-system-commands)
4. [Output Products](#4-output-products)
5. [Quick Reference](#5-quick-reference)

---

## 1. Sentinel-2 Processing

The Sentinel-2 processing system automatically fetches data from Microsoft Planetary Computer and processes it using the METRIC algorithm.

### 1.1 Register a Farm

Register a new area of interest (farm) for processing:

```bash
python -m sentinel.app --mode register \
    --aoi-name "farm_name" \
    --roi "/path/to/farm_boundary.geojson" \
    --start "2025-01-01" \
    --end "2025-12-31"
```

**Parameters:**
| Parameter | Required | Description |
|-----------|----------|-------------|
| `--aoi-name` | Yes | Area of Interest / Farm name (unique identifier) |
| `--roi` | Yes | Path to ROI file (GeoJSON format) |
| `--start` | Yes | Start date (YYYY-MM-DD) |
| `--end` | Yes | End date (YYYY-MM-DD) |

### 1.2 Run Historical Processing

Process all available Sentinel-2 scenes for a registered farm:

```bash
python -m sentinel.app --mode historical --aoi-name "farm_name"
```

### 1.3 Run Daily Processing

Process all enabled farms for the current day (for automated runs):

```bash
python -m automation.app --mode daily
```

### 1.4 List Registered Farms

```bash
python -m sentinel.app --mode list
```

### 1.5 Check Farm Status

```bash
python -m sentinel.app --mode status
```

### 1.6 Check Available Scenes

Check available scenes without downloading:

```bash
python -m sentinel.app --mode check-scenes --aoi-name "farm_name"
```

---

## 2. Landsat Processing

The Landsat processing system uses the `metric` CLI for processing local Landsat data.

### 2.1 Process Multiple Scenes

Process all Landsat scenes in a directory:

```bash
metric process -i /path/to/landsat_scenes/ -o /path/to/output/ -s 2025-09-15 -e 2025-12-04
```

**Parameters:**
| Parameter | Required | Description |
|-----------|----------|-------------|
| `-i, --input-dir` | Yes | Input data directory containing Landsat scenes |
| `-o, --output-dir` | Yes | Output directory for processed results |
| `-s, --start-date` | No | Start date (YYYY-MM-DD) |
| `-e, --end-date` | No | End date (YYYY-MM-DD) |
| `--scene` | No | Process specific scene ID |
| `--cloud-threshold` | No | Maximum cloud cover percentage (default: 30) |
| `--calibration` | No | Calibration mode: auto, hot-cold, manual (default: auto) |
| `--dry-run` | No | Preview without processing |
| `--config` | No | Configuration file path (YAML or JSON) |
| `-v, --verbose` | No | Enable verbose logging |
| `--log-file` | No | Custom log file path |

### 2.2 Process Single Scene

```bash
metric process-scene --scene /path/to/landsat_scene/ --output /path/to/output/
```

### 2.3 Process with Custom Options

```bash
metric process -i data/ -o output/ --cloud-threshold 20 --calibration hot-cold --dry-run
```

### 2.4 Additional METRIC Commands

```bash
# Manage anchor pixels
metric anchors --list
metric anchors --set-cold --scene /path/to/scene/
metric anchors --set-hot --scene /path/to/scene/

# Export results
metric export --input /path/to/results/ --format netcdf --output /path/to/export/

# Create visualizations
metric visualize --input /path/to/ET_daily.tif --output /path/to/viz/ --colormap viridis

# Show processing summary
metric summary --input /path/to/output/
```

---

## 3. Automation System Commands

The automation system provides unified commands for managing farm processing workflows.

### 3.1 Register a New Farm

```bash
python -m automation.app --mode register \
    --aoi-name myfarm \
    --roi /path/to/roi.geojson \
    --start 2025-01-01 \
    --end 2025-12-31
```

### 3.2 Run Historical Processing

```bash
python -m automation.app --mode historical --aoi-name myfarm
```

### 3.3 Run Daily Processing

```bash
python -m automation.app --mode daily
```

### 3.4 Check Status

```bash
python -m automation.app --mode status
```

### 3.5 List All Farms

```bash
python -m automation.app --mode list
```

### 3.6 Enable/Disable a Farm

```bash
# Enable a farm
python -m automation.app --mode set-enabled --aoi-name myfarm --enabled true

# Disable a farm
python -m automation.app --mode set-enabled --aoi-name myfarm --enabled false
```

### 3.7 Check Available Scenes

```bash
python -m automation.app --mode check-scenes --aoi-name myfarm
```

---

## 4. Output Products

Both Sentinel-2 and Landsat processing produce the same output products:

### 4.1 GeoTIFF Files

| File | Description | Units |
|------|-------------|-------|
| `ET_daily.tif` | Daily evapotranspiration | mm/day |
| `ET_inst.tif` | Instantaneous ET at satellite overpass | mm/hr |
| `ETrF.tif` | Reference ET fraction | - |
| `LE.tif` | Latent heat flux | W/m² |
| `H.tif` | Sensible heat flux | W/m² |
| `Rn.tif` | Net radiation | W/m² |
| `G.tif` | Soil heat flux | W/m² |
| `dT.tif` | Temperature difference | K |

### 4.2 Statistics CSV

`statistics.csv` - Pixel statistics for each output band:
- mean, std, min, max, median

### 4.3 Visualizations

- Color-coded ET maps
- Time series plots
- Scatter plots (ET vs NDVI, ET vs temperature)

### 4.4 Metadata

- `metadata.json` - Processing parameters, calibration coefficients, timestamps
- `processing_log.txt` - Detailed processing log

---

## 5. Quick Reference

### Sentinel-2 Quick Commands

```bash
# Register and process a farm
python -m sentinel.app --mode register --aoi-name myfarm --roi roi.geojson --start 2025-01-01 --end 2025-12-31
python -m sentinel.app --mode historical --aoi-name myfarm

# Daily automated processing
python -m automation.app --mode daily
```

### Landsat Quick Commands

```bash
# Process multiple scenes
metric process -i data/ -o output/ -s 2025-09-15 -e 2025-12-04

# Process single scene
metric process-scene --scene data/LC08_L1TP_166038_2025_09_15/ --output output/
```

### Automation Quick Commands

```bash
# Full workflow
python -m automation.app --mode register --aoi-name myfarm --roi roi.geojson --start 2025-01-01 --end 2025-12-31
python -m automation.app --mode historical --aoi-name myfarm
python -m automation.app --mode daily  # for automated runs
```

---

## Document Information

**Version**: 1.0  
**Last Updated**: 2026-05-16