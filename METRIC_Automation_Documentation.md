# METRIC Automation System - Complete Implementation Documentation

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Architecture](#2-architecture)
3. [Component Specifications](#3-component-specifications)
4. [Installation & Setup](#4-installation--setup)
5. [Usage Guide](#5-usage-guide)
6. [Configuration](#6-configuration)
7. [Scheduling & Automation](#7-scheduling--automation)
8. [Logging System](#8-logging-system)
9. [API Reference](#9-api-reference)
10. [Data Management](#10-data-management)
11. [Troubleshooting](#11-troubleshooting)
12. [Examples](#12-examples)
13. [Technical Specifications](#13-technical-specifications)

---

## 1. System Overview

### 1.1 What is the METRIC Automation System?

The METRIC Automation System is a comprehensive Python-based framework designed to automate the processing of Landsat satellite imagery for evapotranspiration (ETa) estimation using the METRIC (Mapping Evapotranspiration with a Residual-Based Calibration) model. The system eliminates manual intervention by:

- **Automatically fetching** Landsat scenes from Microsoft Planetary Computer
- **Processing** scenes through the complete METRIC pipeline
- **Interpolating** and extrapolating ET values between satellite overpasses
- **Managing** multiple farms/AOIs simultaneously
- **Scheduling** daily automatic processing via Windows Task Scheduler

### 1.2 Key Features

| Feature | Description |
|---------|-------------|
| **Multi-farm Support** | Manage unlimited number of farms/AOIs from a single installation |
| **Historical Processing** | Batch process all available scenes within a date range |
| **Daily Automation** | Scheduled processing for new scene detection and processing |
| **Cloud-native Data** | Direct integration with Microsoft Planetary Computer |
| **Comprehensive Logging** | Detailed per-farm and aggregate logging |
| **ROI Flexibility** | Support for GeoJSON and Shapefile ROI formats |
| **Product Organization** | Automatic sorting of outputs into organized folder structures |
| **Metadata Generation** | JSON metadata files for each processed product |

### 1.3 System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         METRIC Automation System                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐     │
│  │                        app.py (CLI Entry Point)                      │     │
│  │                                                                       │     │
│  │   Modes: register | historical | daily | status | list |           │     │
│  │          set-enabled | check-scenes                                  │     │
│  └─────────────────────────────────────────────────────────────────────┘     │
│                                      │                                        │
│                                      ▼                                        │
│  ┌────────────────┬────────────────┬────────────────┬─────────────────┐     │
│  │                │                │                │                 │     │
│  ▼                ▼                ▼                ▼                 ▼     │
│ ┌──────────┐ ┌──────────┐ ┌──────────────┐ ┌──────────────┐ ┌─────────┐ │
│ │ Farm      │ │ Workflow │ │ Scene        │ │ Logger       │ │ Config  │ │
│ │ Manager   │ │ Runner   │ │ Monitor      │ │ Config       │ │ Loader  │ │
│ └──────────┘ └──────────┘ └──────────────┘ └──────────────┘ └─────────┘ │
│       │              │               │                                        │
│       │              │               │                                        │
│       ▼              ▼               ▼                                        │
│ ┌──────────┐ ┌──────────────────────────────┐  ┌────────────────────────┐  │
│ │          │ │                              │  │                        │  │
│ │ Data_     │ │     run_metric_workflow.py  │  │   Planetary Computer   │  │
│ │ Storage/  │ │                              │  │                        │  │
│ │ {farm}/   │ │   ┌────────────────────┐    │  │   Landsat Collection   │  │
│ │           │ │   │ Landsat Fetcher    │────┼──▶  2 Level-2 Data       │  │
│ │ config.json │ │   └────────────────────┘    │  │                        │  │
│ │           │ │   ┌────────────────────┐    │  │                        │  │
│ │ ETaDaily/ │ │   │ METRIC Pipeline    │    │  └────────────────────────┘  │
│ │           │ │   └────────────────────┘    │                                │
│ │ ETrF/     │ │   ┌────────────────────┐    │                                │
│ │           │ │   │ ET Interpolator    │────┼──▶ Interpolated/             │
│ │ NDVI/     │ │   └────────────────────┘    │      Extrapolated ETa        │
│ └──────────┘ │   ┌────────────────────┐    │                                │
│              │   │ Product Organizer   │    │                                │
│              │   └────────────────────┘    │                                │
│              └──────────────────────────────┘                                │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.4 Processing Modes

| Mode | Purpose | Typical Use Case |
|------|---------|------------------|
| `register` | Register a new farm/AOI | Initial setup |
| `historical` | Process all scenes in a date range | Catch-up processing |
| `daily` | Check and process new scenes | Scheduled automation |
| `status` | View farm processing status | Monitoring |
| `list` | List all registered farms | Quick overview |
| `set-enabled` | Enable/disable a farm | Pause processing |
| `check-scenes` | Preview available scenes | Planning |

---

## 2. Architecture

### 2.1 Component Overview

The automation system consists of five core modules:

#### 2.1.1 `app.py` - Main CLI Entry Point

The central orchestrator that:
- Parses command-line arguments
- Initializes all components
- Dispatches to appropriate mode handlers
- Manages global logging

**Responsibilities:**
- User interface handling
- Mode routing
- Error handling and reporting
- Exit code management

#### 2.1.2 `farm_manager.py` - Farm Registry

Manages farm configurations stored in `Data_Storage/`:

**Key Classes:**
- `FarmManager`: Main farm management class
- `FarmValidationError`: Custom exception for validation failures

**Key Responsibilities:**
- Farm registration (creating `config.json`)
- Configuration validation
- Farm scanning and enumeration
- Enable/disable management
- Last processed date tracking

#### 2.1.3 `workflow_runner.py` - Execution Engine

Executes the METRIC workflow for farms:

**Key Classes:**
- `WorkflowRunner`: Workflow execution wrapper
- `WorkflowResult`: Dataclass for execution results

**Key Responsibilities:**
- Command building for `run_metric_workflow.py`
- Subprocess management
- Result capturing and parsing
- Dry-run mode support

#### 2.1.4 `scene_monitor.py` - Scene Detection

Monitors Planetary Computer for available scenes:

**Key Classes:**
- `SceneMonitor`: Scene monitoring and detection
- `SceneInfo`: Dataclass for scene metadata

**Key Responsibilities:**
- STAC API queries to Planetary Computer
- Cloud cover filtering
- New scene detection since last processed date
- ROI loading (GeoJSON/Shapefile)

#### 2.1.5 `logger_config.py` - Logging Infrastructure

Comprehensive logging with rotation:

**Key Functions:**
- `setup_logging()`: Initialize rotating file handlers
- `get_farm_logger()`: Farm-specific logger
- `DailySummaryLogger`: CSV-based summary logging

### 2.2 Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Data Flow Diagram                                  │
└─────────────────────────────────────────────────────────────────────────────┘

User Command
     │
     ▼
┌─────────────────┐
│  app.py         │  Parse arguments, setup logging
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ FarmManager     │  Load config.json from Data_Storage/{aoi_name}/
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ SceneMonitor    │──▶ Planetary Computer STAC API
│                 │    Query available scenes
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ WorkflowRunner  │  Build & execute subprocess
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│                    run_metric_workflow.py                    │
│                                                              │
│  ┌──────────────┐   ┌──────────────┐   ┌───────────────┐  │
│  │ Planetary    │──▶│ METRIC       │──▶│ Product       │  │
│  │ Computer     │   │ Pipeline     │   │ Organizer     │  │
│  │ Fetcher      │   │              │   │               │  │
│  └──────────────┘   └──────────────┘   └───────────────┘  │
│                            │                                  │
│                            ▼                                  │
│                     ┌──────────────┐                         │
│                     │ ET           │                         │
│                     │ Interpolator │                         │
│                     └──────────────┘                         │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────┐
│ Output          │  Save to Data_Storage/{aoi_name}/
│ Files           │  ├── ETaDaily/
└─────────────────┘  ├── ETrF/
                     ├── NDVI/
                     └── metadata/
```

---

## 3. Component Specifications

### 3.1 Farm Configuration Structure

Each farm is defined by a `config.json` file:

```json
{
    "aoi_name": "amirkabir",
    "roi_path": "e:/data/amirkabir/roi.geojson",
    "output_dir": "e:/RSGIS/SatAgrySys/et/Automation test/Data_Storage/amirkabir",
    "historical_range": {
        "start": "2025-09-01",
        "end": "2025-12-31"
    },
    "enabled": true,
    "last_processed_date": "2025-12-15",
    "registration_date": "2026-05-06",
    "max_cloud_cover": 50.0,
    "source_crs": "EPSG:4326",
    "interpolation_method": "weighted",
    "extrapolation_days": 14
}
```

**Configuration Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `aoi_name` | string | Yes | Unique farm identifier |
| `roi_path` | string | Yes | Path to ROI file (.geojson, .json, or .shp) |
| `output_dir` | string | Yes | Base output directory |
| `historical_range.start` | string | No | Start date for historical processing |
| `historical_range.end` | string | No | End date for historical processing |
| `enabled` | boolean | Yes | Whether farm is active |
| `last_processed_date` | string | No | Last successful processing date |
| `registration_date` | string | Auto | Date of farm registration |
| `max_cloud_cover` | float | Yes | Maximum cloud cover % (0-100) |
| `source_crs` | string | Yes | CRS of ROI file |
| `interpolation_method` | string | No | 'linear' or 'weighted' |
| `extrapolation_days` | int | No | Days to extrapolate beyond last scene |

### 3.2 Scheduler Configuration

Located at `automation/config/scheduler.json`:

```json
{
    "version": "1.0",
    "scheduler": {
        "type": "windows_task_scheduler",
        "daily_time": "02:00",
        "enabled": true
    },
    "processing": {
        "max_concurrent_farms": 1,
        "retry_failed_scenes": true,
        "max_retries": 3,
        "retry_delay_hours": 6
    },
    "defaults": {
        "max_cloud_cover": 50.0,
        "interpolation_method": "weighted",
        "extrapolation_days": 14,
        "source_crs": "EPSG:4326"
    },
    "data_storage": {
        "path": "e:/RSGIS/SatAgrySys/et/Automation test/Data_Storage"
    },
    "paths": {
        "metric_root": "e:/RSGIS/SatAgrySys/METRIC"
    }
}
```

### 3.3 Scene Detection Logic

The `SceneMonitor` class implements the following detection algorithm:

```
Algorithm: has_new_scenes(farm_config)
─────────────────────────────────────────
Input: farm_config with last_processed_date
Output: (has_new_scenes: bool, scenes: List[SceneInfo])

1. Determine date range:
   from_date = last_processed_date OR historical_range.start
   to_date = TODAY

2. Load ROI geometry from farm_config.roi_path

3. Calculate ROI bounding box:
   bbox = [minx, miny, maxx, maxy]

4. Query Planetary Computer STAC API:
   collections = ["landsat-c2-l2"]
   bbox = calculated bbox
   datetime = "{from_date}/{to_date}"
   query.platform["in"] = ["landsat-8", "landsat-9"]

5. Filter scenes by cloud cover:
   keep if cloud_cover <= farm_config.max_cloud_cover

6. Sort scenes by date ascending

7. Return scenes list
```

---

## 4. Installation & Setup

### 4.1 Prerequisites

| Requirement | Version | Purpose |
|-------------|---------|---------|
| Python | 3.9+ | Runtime environment |
| Conda | 4.12+ | Package management |
| Windows | 10+ | Operating system |
| Network | Internet | Planetary Computer access |

### 4.2 Conda Environment Setup

```bash
# 1. Navigate to METRIC directory
cd E:\RSGIS\SatAgrySys\METRIC

# 2. Create conda environment
conda env create -f environment.yml

# 3. Activate environment
conda activate metric-env

# 4. Install METRIC package in development mode
pip install -e .
```

### 4.3 Directory Structure Setup

```
E:\RSGIS\SatAgrySys\
├── METRIC/                          # METRIC installation
│   ├── automation/                  # Automation modules
│   │   ├── app.py                   # CLI entry point
│   │   ├── farm_manager.py          # Farm registry
│   │   ├── workflow_runner.py       # Workflow executor
│   │   ├── scene_monitor.py         # Scene detection
│   │   ├── logger_config.py         # Logging
│   │   ├── config/
│   │   │   └── scheduler.json       # Scheduler config
│   │   ├── logs/                    # Log files
│   │   │   ├── automation.log
│   │   │   ├── daily_summary.log
│   │   │   └── {farm}_*.log
│   │   └── run_daily.bat            # Batch file for Task Scheduler
│   └── metric_et/                   # Core METRIC package
│
└── Data_Storage/                    # Farm data (separate location)
    ├── farm001/
    │   ├── config.json
    │   ├── scenes/                  # Downloaded Landsat
    │   ├── et_output/               # METRIC results
    │   │   ├── products/
    │   │   │   ├── ETaDaily/
    │   │   │   ├── ETrF/
    │   │   │   └── NDVI/
    │   │   └── result_YYYYMMDD/     # Individual scene outputs
    │   └── workflow_summary.json
    └── farm002/
        └── ...
```

### 4.4 Windows Task Scheduler Setup

#### Method 1: GUI Wizard

1. Open Task Scheduler: `taskschd.msc`
2. Click **Create Basic Task...**
3. Name: `METRIC_Daily_Automation`
4. Trigger: **Daily** at 2:00 AM
5. Action: **Start a program**
   - Program: `cmd.exe`
   - Arguments: `/c "E:\RSGIS\SatAgrySys\METRIC\automation\run_daily.bat"`
6. Complete wizard

#### Method 2: PowerShell

```powershell
# Create scheduled task
$action = New-ScheduledTaskAction `
    -Execute "cmd.exe" `
    -Argument '/c "E:\RSGIS\SatAgrySys\METRIC\automation\run_daily.bat"'

$trigger = New-ScheduledTaskTrigger `
    -Daily `
    -At 2am

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable

Register-ScheduledTask `
    -TaskName "METRIC_Daily_Automation" `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Description "Daily METRIC ETa automation processing"
```

#### Method 3: Command Line

```cmd
schtasks /create /tn "METRIC_Daily_Automation" ^
    /tr "cmd /c \"E:\RSGIS\SatAgrySys\METRIC\automation\run_daily.bat\"" ^
    /sc daily /st 02:00 ^
    /ru SYSTEM ^
    /f
```

---

## 5. Usage Guide

### 5.1 Quick Start Commands

#### Register a New Farm

```bash
python automation/app.py --mode register ^
    --aoi-name amirkabir ^
    --roi e:/data/amirkabir/roi.geojson ^
    --start 2025-09-01 ^
    --end 2025-12-31
```

**Expected Output:**
```
METRIC Automation System
Data Storage: e:/RSGIS/SatAgrySys/et/Automation test/Data_Storage
METRIC Root: E:/RSGIS/SatAgrySys/METRIC
Mode: register
INFO - Successfully registered farm: amirkabir
INFO -   ROI: e:/data/amirkabir/roi.geojson
INFO -   Historical range: 2025-09-01 to 2025-12-31
```

#### Run Historical Processing

```bash
python automation/app.py --mode historical --aoi-name amirkabir
```

**Expected Output:**
```
====================================================================
Starting historical processing for amirkabir
====================================================================
Date range: 2025-09-01 to 2025-12-31
...
====================================================================
✓ amirkabir: Success (1234.5s) - 15 scenes
INFO - Updated last_processed_date to 2025-12-31
```

#### Run Daily Processing (Automated)

```bash
python automation/app.py --mode daily
```

**Expected Output:**
```
====================================================================
STARTING DAILY PROCESSING
====================================================================
Time: 2026-05-06 02:00:00
====================================================================
Found 2 enabled farms

Processing farm: amirkabir
Found 1 new scenes: ['landsat-8_2026-05-04_p166_r38']
Workflow completed successfully (456.7s)
✓ amirkabir: Success (456.7s) - 1 scenes

Processing farm: test_farm
No new scenes found
✓ test_farm: No new scenes

====================================================================
DAILY PROCESSING SUMMARY
====================================================================
Total farms: 2
Successful: 2
Failed: 0
New scenes found: 1
Scenes processed: 1
Duration: 456.7s
====================================================================
```

#### Check Farm Status

```bash
python automation/app.py --mode status
```

**Expected Output:**
```
======================================================================
FARM STATUS
======================================================================
AOI Name                 Enabled    Last Processed   Historical Range         
----------------------------------------------------------------------
amirkabir                ✓          2025-12-31       2025-09-01 to 2025-12-31
test_farm                ✓          Never            None
======================================================================
Total: 2 farms
```

#### List All Farms

```bash
python automation/app.py --mode list
```

#### Check Available Scenes

```bash
python automation/app.py --mode check-scenes --aoi-name amirkabir
```

**Expected Output:**
```
Checking scenes for amirkabir...
Found 5 scenes for amirkabir
Date range: 2025-12-01 to 2026-05-06
--------------------------------------------------
landsat-8_2025-12-03_p166_r38
landsat-8_2025-12-19_p166_r38
landsat-8_2026-01-04_p166_r38
landsat-8_2026-01-20_p166_r38
landsat-8_2026-02-05_p166_r38
```

#### Enable/Disable a Farm

```bash
# Disable
python automation/app.py --mode set-enabled --aoi-name amirkabir --enabled false

# Enable
python automation/app.py --mode set-enabled --aoi-name amirkabir --enabled true
```

### 5.2 Command Line Arguments Reference

| Argument | Required | Choices | Description |
|----------|----------|---------|-------------|
| `--mode` | Yes | see modes above | Operation mode |
| `--aoi-name` | For farm operations | - | Farm/AOI identifier |
| `--roi` | For register | - | Path to ROI file |
| `--start` | For register | YYYY-MM-DD | Historical start date |
| `--end` | For register | YYYY-MM-DD | Historical end date |
| `--enabled` | For set-enabled | true/false | Enable/disable farm |
| `--data-storage` | No | path | Data storage location |
| `--metric-root` | No | path | METRIC installation path |
| `--dry-run` | No | flag | Preview without execution |
| `--verbose` | No | flag | Enable debug logging |

### 5.3 Exit Codes

| Code | Meaning |
|------|--------|
| 0 | Success |
| 1 | Error (generic) |
| 2 | Invalid arguments |
| 130 | Interrupted by user (Ctrl+C) |

---

## 6. Configuration

### 6.1 Farm Configuration (config.json)

Created automatically by `register` mode. Can be manually edited:

```json
{
    "aoi_name": "example_farm",
    "roi_path": "e:/data/example/roi.geojson",
    "output_dir": "e:/RSGIS/SatAgrySys/et/Automation test/Data_Storage/example_farm",
    "historical_range": {
        "start": "2025-01-01",
        "end": "2025-12-31"
    },
    "enabled": true,
    "last_processed_date": null,
    "registration_date": "2026-05-06",
    "max_cloud_cover": 50.0,
    "source_crs": "EPSG:4326",
    "interpolation_method": "weighted",
    "extrapolation_days": 14
}
```

### 6.2 Scheduler Configuration (scheduler.json)

Controls global automation behavior:

| Section | Field | Default | Description |
|---------|-------|---------|-------------|
| scheduler | type | windows_task_scheduler | Scheduler type |
| scheduler | daily_time | 02:00 | Time to run daily automation |
| scheduler | enabled | true | Enable/disable scheduler |
| processing | max_concurrent_farms | 1 | Parallel farm processing |
| processing | retry_failed_scenes | true | Retry failed scenes |
| processing | max_retries | 3 | Maximum retry attempts |
| processing | retry_delay_hours | 6 | Delay between retries |
| defaults | max_cloud_cover | 50.0 | Default cloud threshold |
| defaults | interpolation_method | weighted | ET interpolation method |
| defaults | extrapolation_days | 14 | Days to extrapolate |
| defaults | source_crs | EPSG:4326 | Default ROI CRS |

### 6.3 ROI File Formats

#### GeoJSON Feature

```json
{
    "type": "Feature",
    "geometry": {
        "type": "Polygon",
        "coordinates": [[
            [51.0, 35.0],
            [51.5, 35.0],
            [51.5, 35.5],
            [51.0, 35.5],
            [51.0, 35.0]
        ]]
    },
    "properties": {
        "name": "My Farm"
    }
}
```

#### GeoJSON FeatureCollection

```json
{
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {...},
            "properties": {...}
        }
    ]
}
```

#### Shapefile

Standard ESRI Shapefile format (.shp) with associated files (.shx, .dbf, .prj).

---

## 7. Scheduling & Automation

### 7.1 Scheduling Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Windows Task Scheduler                        │
│                                                                 │
│  Task: METRIC_Daily_Automation                                  │
│  Trigger: Daily at 02:00 AM                                     │
│  Action: cmd.exe /c "automation\run_daily.bat"                 │
│  User: SYSTEM (or current user)                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    run_daily.bat                                │
│                                                                 │
│  @echo off                                                      │
│  cd /d E:\RSGIS\SatAgrySys\METRIC                               │
│  python automation/app.py --mode daily                          │
│  echo [%DATE% %TIME%] Completed: %ERRORLEVEL% >> logs\cron.log │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    app.py --mode daily                          │
│                                                                 │
│  1. Load all farm configurations                                │
│  2. For each enabled farm:                                      │
│     a. Check Planetary Computer for new scenes                   │
│     b. If new scenes found → run workflow                       │
│  3. Update last_processed_date for each farm                    │
│  4. Generate daily summary log                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 7.2 Scheduling Best Practices

| Practice | Recommendation |
|----------|----------------|
| **Run Time** | 2:00-4:00 AM (off-peak hours) |
| **Frequency** | Daily (Landsat 8/9 8-day cycle) |
| **User Account** | SYSTEM or dedicated service account |
| **Logging** | Always log to file for debugging |
| **Notifications** | Configure email alerts on failure |

### 7.3 Batch File (run_daily.bat)

```batch
@echo off
REM METRIC Automation System - Daily Processing Batch File
REM
REM This batch file is used by Windows Task Scheduler to run the
REM daily METRIC automation workflow.

REM Change to METRIC root directory
cd /d E:\RSGIS\SatAgrySys\METRIC

REM Run the daily automation
python automation/app.py --mode daily

REM Log completion with timestamp
echo [%DATE% %TIME%] Daily automation completed with exit code %ERRORLEVEL% >> automation\logs\cron.log
```

### 7.4 Monitoring Scheduled Tasks

```cmd
# Check if task exists
schtasks /query /tn "METRIC_Daily_Automation"

# View task details
schtasks /query /tn "METRIC_Daily_Automation" /v /fo LIST

# Run task manually
schtasks /run /tn "METRIC_Daily_Automation"

# Delete task
schtasks /delete /tn "METRIC_Daily_Automation" /f

# View recent runs in Event Viewer
eventvwr.msc
# Navigate to: Application > Source: "Scheduled Tasks"
```

---

## 8. Logging System

### 8.1 Log File Structure

| File | Purpose | Contents |
|------|---------|----------|
| `automation.log` | Main application log | All operations |
| `daily_summary.log` | CSV summary | Daily processing metrics |
| `{farm}.log` | Farm-specific log | Detailed farm operations |
| `{farm}_results.log` | Farm results CSV | Per-farm results |
| `cron.log` | Batch execution log | Task scheduler entries |

### 8.2 Log Format

**Main Log (automation.log):**
```
2026-05-06 02:00:01 - main - INFO - Starting daily processing
2026-05-06 02:00:02 - amirkabir - INFO - Checking for new scenes...
2026-05-06 02:00:15 - amirkabir - INFO - Found 1 new scene: landsat-8_2026-05-04
2026-05-06 02:00:16 - amirkabir - INFO - Starting workflow for 2026-05-04
2026-05-06 02:15:30 - amirkabir - INFO - Workflow completed successfully
2026-05-06 02:15:31 - main - INFO - Daily processing completed: 1/1 farms successful
```

**Daily Summary CSV (daily_summary.log):**
```csv
date,mode,total_farms,successful,failed,scenes_found,scenes_processed,duration_sec,status
2026-05-06,daily,2,2,0,3,3,120.5,completed
2026-05-07,daily,2,1,1,1,1,90.3,partial
```

**Farm Results CSV ({farm}_results.log):**
```csv
timestamp,date,status,scenes_found,scenes_processed,notes
2026-05-06 02:00:15,2026-05-06,success,1,1,
2026-05-07 02:00:18,2026-05-07,no_scenes,0,0,
```

### 8.3 Log Rotation

Logs use `RotatingFileHandler` with:
- **Max size**: 10 MB per file
- **Backup count**: 5 files retained
- **Format**: `automation.log`, `automation.log.1`, ..., `automation.log.5`

### 8.4 Accessing Logs

```bash
# View recent automation log
type automation\logs\automation.log

# View last 50 lines (PowerShell)
Get-Content automation\logs\automation.log -Tail 50

# Search for errors
findstr /i "error" automation\logs\automation.log

# View daily summaries
type automation\logs\daily_summary.log

# View specific farm log
type automation\logs\amirkabir.log

# Watch log in real-time
powershell -Command "Get-Content automation\logs\automation.log -Wait -Tail 10"
```

---

## 9. API Reference

### 9.1 Python API Usage

```python
from automation import FarmManager, WorkflowRunner, SceneMonitor
```

#### 9.1.1 FarmManager

```python
from automation import FarmManager

# Initialize with custom data storage path
fm = FarmManager(data_storage_path="e:/RSGIS/SatAgrySys/et/Automation test/Data_Storage")

# Register a new farm
config = fm.register_farm(
    aoi_name="my_farm",
    roi_path="e:/data/my_farm/roi.geojson",
    start_date="2025-01-01",
    end_date="2025-12-31",
    max_cloud_cover=50.0
)

# Get farm configuration
farm = fm.get_farm("my_farm")
print(f"ROI: {farm['roi_path']}")
print(f"Last processed: {farm.get('last_processed_date')}")

# List all farms
farms = fm.scan_farms()
print(f"Total farms: {len(farms)}")

# Get enabled farms only
enabled = fm.get_enabled_farms()

# Update last processed date
fm.update_last_processed("my_farm", "2025-06-15")

# Enable/disable farm
fm.set_enabled("my_farm", False)

# Check if farm exists
if fm.is_enabled("my_farm"):
    print("Farm is enabled")
```

#### 9.1.2 WorkflowRunner

```python
from automation import WorkflowRunner

# Initialize
runner = WorkflowRunner(metric_root="E:/RSGIS/SatAgrySys/METRIC")

# Validate workflow script exists
valid, msg = runner.validate_workflow_script()
print(f"Workflow valid: {valid}")

# Run historical processing
farm = {
    "aoi_name": "my_farm",
    "roi_path": "e:/data/my_farm/roi.geojson",
    "output_dir": "e:/RSGIS/SatAgrySys/et/Automation test/Data_Storage/my_farm",
    "historical_range": {
        "start": "2025-01-01",
        "end": "2025-06-30"
    },
    "max_cloud_cover": 50.0
}

result = runner.run_historical(farm)
print(f"Success: {result.success}")
print(f"Duration: {result.duration_sec:.1f}s")
print(f"Scenes processed: {result.scenes_processed}")

# Run for specific dates
result = runner.run_for_dates(farm, ["2025-05-01", "2025-05-09"])

# Run daily (incremental)
result = runner.run_daily(farm, target_date="2025-06-15")

# Dry run (preview)
result = runner.run_daily(farm, dry_run=True)
```

#### 9.1.3 SceneMonitor

```python
from automation import SceneMonitor

# Initialize
monitor = SceneMonitor(max_cloud_cover=50.0)

# Check for new scenes
farm = {
    "aoi_name": "my_farm",
    "roi_path": "e:/data/my_farm/roi.geojson",
    "last_processed_date": "2025-05-01"
}

has_new, scenes = monitor.has_new_scenes(farm)
print(f"New scenes: {len(scenes)}")
for scene in scenes:
    print(f"  {scene}")

# Check available scenes in date range
scenes = monitor.check_new_scenes(
    farm,
    from_date="2025-01-01",
    to_date="2025-06-30"
)

# Get unprocessed scenes only
unprocessed = monitor.get_unprocessed_scenes(farm)

# Quick scene check (utility function)
from automation.scene_monitor import quick_scene_check

scenes = quick_scene_check(
    roi_path="e:/data/my_farm/roi.geojson",
    start_date="2025-01-01",
    end_date="2025-06-30",
    max_cloud_cover=50.0
)
```

### 9.2 SceneInfo Dataclass

```python
from automation.scene_monitor import SceneInfo

# SceneInfo attributes
scene = SceneInfo(
    scene_id="LC08_L2SP_166038_20230504_20230509_02_T1",
    date="2025-05-04",
    cloud_cover=15.3,
    path="166",
    row="038",
    platform="landsat-8"
)

print(scene)  # landsat-8_2025-05-04_p166_r038
```

### 9.3 WorkflowResult Dataclass

```python
from automation.workflow_runner import WorkflowResult

result = WorkflowResult(
    success=True,
    returncode=0,
    stdout="Processing complete",
    stderr="",
    duration_sec=456.7,
    scenes_processed=3
)

# Access attributes
print(result.summary)  # "Success (456.7s) - 3 scenes"
print(result.success)  # True
print(result.scenes_processed)  # 3
```

---

## 10. Data Management

### 10.1 Output Directory Structure

```
Data_Storage/
└── {aoi_name}/
    ├── config.json                    # Farm configuration
    ├── workflow_summary.json          # Last workflow summary
    │
    ├── scenes/                        # Downloaded Landsat data
    │   ├── landsat_20250901_166_038/
    │   │   ├── blue.tif
    │   │   ├── green.tif
    │   │   ├── red.tif
    │   │   ├── nir08.tif
    │   │   ├── swir16.tif
    │   │   ├── swir22.tif
    │   │   ├── lwir11.tif
    │   │   ├── qa.tif
    │   │   ├── qa_pixel.tif
    │   │   └── MTL.json
    │   └── landsat_20250917_166_038/
    │       └── ...
    │
    └── et_output/                     # METRIC processing results
        ├── products/
        │   ├── ETaDaily/
        │   │   ├── ETaDaily_20250901_amirkabir.tif
        │   │   ├── ETaDaily_interpolated_20250904_amirkabir.tif
        │   │   └── ...
        │   ├── ETrF/
        │   │   ├── ETrF_20250901_amirkabir.tif
        │   │   └── ...
        │   ├── NDVI/
        │   │   └── ...
        │   ├── RGB/
        │   │   └── ...
        │   └── metadata/
        │       ├── ETaDaily_20250901_amirkabir.json
        │       └── ...
        │
        ├── result_20250901/           # Individual scene outputs
        │   ├── ET_daily.tif
        │   ├── ET_inst.tif
        │   ├── ETrF.tif
        │   ├── LE.tif
        │   ├── H.tif
        │   ├── Rn.tif
        │   ├── G.tif
        │   └── dT.tif
        └── result_20250917/
            └── ...
```

### 10.2 Product File Naming

| Product | Pattern | Example |
|---------|---------|---------|
| Scene ETa | `ETaDaily_{YYYYMMDD}_{aoi}.tif` | `ETaDaily_20250901_amirkabir.tif` |
| Scene ETrF | `ETrF_{YYYYMMDD}_{aoi}.tif` | `ETrF_20250901_amirkabir.tif` |
| Interpolated | `ETaDaily_interpolated_{YYYYMMDD}_{aoi}.tif` | `ETaDaily_interpolated_20250904_amirkabir.tif` |
| Extrapolated | `ETaDaily_extrapolated_{YYYYMMDD}_{aoi}.tif` | `ETaDaily_extrapolated_20250930_amirkabir.tif` |

### 10.3 Metadata Files

Each product has an associated JSON metadata file:

```json
{
    "product_type": "ETaDaily",
    "filename": "ETaDaily_20250901_amirkabir.tif",
    "scene_date": "2025-09-01",
    "scene_id": "LC08_L2SP_166038_20250901_20250909_02_T1",
    "aoi_name": "amirkabir",
    "processing_time": "2026-05-06T02:15:30",
    "source": "Landsat 8 OLI/TIRS",
    "spatial_resolution": 30,
    "units": "mm/day",
    "nodata_value": -9999,
    "statistics": {
        "mean": 4.25,
        "std": 1.23,
        "min": 0.15,
        "max": 8.92,
        "valid_pixels": 12500
    },
    "calibration": {
        "cold_pixel": {"x": 150, "y": 200, "ETrF": 1.05},
        "hot_pixel": {"x": 300, "y": 400, "ETrF": 0.05}
    }
}
```

### 10.4 Workflow Summary

Stored in `workflow_summary.json`:

```json
{
    "workflow_completion_time": "2026-05-06T02:30:00",
    "roi_path": "e:/data/amirkabir/roi.geojson",
    "output_dir": "e:/RSGIS/SatAgrySys/et/Automation test/Data_Storage/amirkabir",
    "date_range": {
        "start": "2025-09-01",
        "end": "2025-12-31"
    },
    "aoi_name": "amirkabir",
    "max_cloud_cover": 50.0,
    "source_crs": "EPSG:4326",
    "interpolation_method": "weighted",
    "extrapolation_days": 14,
    "results": {
        "scenes_fetched": 15,
        "scenes_processed": 14,
        "scenes_failed": 1,
        "interpolation_dates": 60,
        "extrapolation_dates": 14,
        "products_organized": 450
    }
}
```

---

## 11. Troubleshooting

### 11.1 Common Issues

#### Issue: "No scenes found"

**Symptoms:**
```
Found 0 qualifying scenes for amirkabir
```

**Causes & Solutions:**

| Cause | Solution |
|-------|----------|
| No internet connection | Verify network access to Planetary Computer |
| ROI outside Landsat coverage | Check path/row for your region |
| Date range too short | Extend start/end dates |
| High cloud cover threshold too low | Increase `max_cloud_cover` in config |
| ROI file not found | Verify `roi_path` in config.json |

**Debugging:**
```bash
python automation/app.py --mode check-scenes --aoi-name amirkabir
```

#### Issue: "ROI file not found"

**Symptoms:**
```
ERROR - Failed to load ROI from e:/data/amirkabir/roi.geojson
```

**Solutions:**
1. Verify file path is correct (use forward slashes or raw strings)
2. Ensure file extension is `.geojson`, `.json`, or `.shp`
3. Check file permissions

#### Issue: "Workflow script not found"

**Symptoms:**
```
FileNotFoundError: Workflow script not found
```

**Solution:**
Ensure `metric_root` points to the correct METRIC installation directory.

#### Issue: "Task Scheduler not running"

**Debugging:**
```cmd
# Check task status
schtasks /query /tn "METRIC_Daily_Automation"

# View last run result
schtasks /query /tn "METRIC_Daily_Automation" /fo LIST

# Check Windows Event Viewer
eventvwr.msc
# Look for: Applications > Microsoft-Windows-TaskScheduler
```

#### Issue: "Out of disk space"

**Symptoms:**
```
ERROR - No space left on device
```

**Solutions:**
1. Clean up old scenes in `scenes/` folder
2. Delete intermediate processing files
3. Move data to larger drive
4. Increase `max_retries` to 1 in scheduler.json

### 11.2 Error Handling Flow

```
Exception Occurred
       │
       ▼
┌─────────────────┐
│ Log to farm    │  ──▶ {farm}.log
│ specific logger │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Log to main     │  ──▶ automation.log
│ application log │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Log to daily    │  ──▶ daily_summary.log (status=error)
│ summary CSV     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Return exit     │  ──▶ Exit code 1 (failure)
│ code 1          │
└─────────────────┘
```

### 11.3 Recovery Procedures

#### Recovery: Farm Stuck in Error State

```bash
# 1. Check what's wrong
python automation/app.py --mode status

# 2. Fix the issue (see above troubleshooting)

# 3. Reset last_processed_date to retry
python -c "from automation import FarmManager; fm = FarmManager(); c = fm.get_farm('amirkabir'); c['last_processed_date'] = None; fm.update_last_processed('amirkabir', None)"

# 4. Run daily processing again
python automation/app.py --mode daily
```

#### Recovery: Corrupted Config

```bash
# Delete and re-register
python automation/app.py --mode set-enabled --aoi-name bad_farm --enabled false

# Manually edit Data_Storage/bad_farm/config.json
# OR delete and re-register:
# 1. Backup output data
# 2. Delete Data_Storage/bad_farm/config.json
# 3. Re-register
python automation/app.py --mode register --aoi-name bad_farm --roi path/to/roi.geojson --start 2025-01-01 --end 2025-12-31
```

---

## 12. Examples

### 12.1 Complete Setup Example

```bash
# 1. Register a new farm
python automation/app.py --mode register ^
    --aoi-name tehrantest ^
    --roi e:/data/tehran/roi.geojson ^
    --start 2025-01-01 ^
    --end 2025-12-31

# 2. Run historical processing (one-time catch-up)
python automation/app.py --mode historical --aoi-name tehrantest

# 3. Setup daily automation
powershell -Command "New-ScheduledTaskAction -Execute 'cmd.exe' -Argument '/c \"E:\RSGIS\SatAgrySys\METRIC\automation\run_daily.bat\"' | ..."
```

### 12.2 Python Script Example

```python
#!/usr/bin/env python3
"""
Automated METRIC processing script.
Run this script daily via Task Scheduler.
"""

import sys
from pathlib import Path

# Add METRIC to path
sys.path.insert(0, str(Path(__file__).parent))

from automation import FarmManager, WorkflowRunner, SceneMonitor
from automation.logger_config import setup_logging, DailySummaryLogger

def main():
    # Setup logging
    logger = setup_logging(log_dir=Path(__file__).parent / "automation" / "logs")
    
    # Initialize components
    fm = FarmManager()
    runner = WorkflowRunner()
    monitor = SceneMonitor()
    summary = DailySummaryLogger()
    
    # Get enabled farms
    farms = fm.get_enabled_farms()
    
    total = len(farms)
    success = 0
    failed = 0
    
    for farm in farms:
        aoi = farm['aoi_name']
        logger.info(f"Processing {aoi}...")
        
        # Check for new scenes
        has_new, scenes = monitor.has_new_scenes(farm)
        
        if not has_new:
            logger.info(f"No new scenes for {aoi}")
            success += 1
            continue
        
        # Run workflow
        result = runner.run_for_dates(farm, [s.date for s in scenes])
        
        if result.success:
            # Update last processed
            latest = max([s.date for s in scenes])
            fm.update_last_processed(aoi, latest)
            success += 1
        else:
            failed += 1
        
        # Log summary
        summary.log_farm_result(
            date=datetime.now().strftime('%Y-%m-%d'),
            farm_id=aoi,
            status="success" if result.success else "error",
            scenes_found=len(scenes),
            scenes_processed=result.scenes_processed
        )
    
    # Log daily summary
    summary.log_summary(
        date=datetime.now().strftime('%Y-%m-%d'),
        mode="daily",
        total_farms=total,
        successful=success,
        failed=failed,
        scenes_found=0,
        scenes_processed=0,
        duration_sec=0,
        status="completed" if failed == 0 else "partial"
    )
    
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    from datetime import datetime
    sys.exit(main())
```

### 12.3 Multi-Farm Batch Processing

```python
from automation import FarmManager, WorkflowRunner
from datetime import datetime
import time

# Initialize
fm = FarmManager()
runner = WorkflowRunner()

# Get all farms
farms = fm.scan_farms()

# Process sequentially
for farm in farms:
    if not farm.get('enabled', True):
        print(f"Skipping disabled farm: {farm['aoi_name']}")
        continue
    
    print(f"\n{'='*60}")
    print(f"Processing: {farm['aoi_name']}")
    print(f"{'='*60}")
    
    start = time.time()
    result = runner.run_historical(farm)
    duration = time.time() - start
    
    if result.success:
        fm.update_last_processed(
            farm['aoi_name'],
            farm['historical_range']['end']
        )
        print(f"✓ Success: {result.scenes_processed} scenes in {duration:.1f}s")
    else:
        print(f"✗ Failed: {result.stderr[:200]}")
```

---

## 13. Technical Specifications

### 13.1 Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| Python | 3.9+ | Runtime |
| rasterio | 1.3+ | GeoTIFF handling |
| numpy | 1.21+ | Numerical operations |
| geopandas | 0.12+ | Vector data handling |
| pystac-client | 0.7+ | STAC API access |
| planetary-computer | 0.7+ | Planetary Computer SDK |
| xarray | 0.21+ | Multi-dimensional arrays |
| shapely | 2.0+ | Geometry operations |

### 13.2 System Resources

| Resource | Minimum | Recommended |
|----------|---------|--------------|
| RAM | 8 GB | 16 GB |
| Storage | 50 GB | 200 GB |
| CPU | 4 cores | 8 cores |
| Network | 10 Mbps | 50 Mbps |

### 13.3 Performance Estimates

| Operation | Time per Scene | Notes |
|-----------|---------------|-------|
| Scene download | 30-60s | Depends on scene size |
| METRIC processing | 2-5 min | Depends on ROI size |
| Product organization | 10-30s | Depends on file count |
| **Total per scene** | **3-7 min** | - |
| **Historical (100 scenes)** | **5-12 hours** | Sequential processing |

### 13.4 Network Requirements

| Endpoint | Port | Purpose |
|----------|------|---------|
| planetarycomputer.microsoft.com | 443 | STAC API, data download |
| landsatlook.usgs.gov | 443 | Backup Landsat access |
| api.open-meteo.com | 443 | Weather data (METRIC core) |

### 13.5 File Permissions

| Path | Required Permission |
|------|---------------------|
| `automation/` | Read/Write |
| `automation/logs/` | Read/Write |
| `automation/config/` | Read |
| `METRIC/` | Read/Execute |
| `Data_Storage/` | Read/Write |
| ROI files | Read |

---

## Appendix A: Glossary

| Term | Definition |
|------|------------|
| AOI | Area of Interest - The geographic region for processing |
| ETa | Actual Evapotranspiration - Water evaporated and transpired |
| ETrF | Reference ET Fraction - Ratio of ETa to reference ET |
| METRIC | Mapping Evapotranspiration with a Residual-Based Calibration |
| ROI | Region of Interest - See AOI |
| STAC | SpatioTemporal Asset Catalog - API specification for geospatial data |
| Landsat | USGS satellite constellation (L8/L9) |

## Appendix B: File Reference

### automation/app.py
Main CLI entry point handling all operation modes.

### automation/farm_manager.py
Farm registration and configuration management.

### automation/workflow_runner.py
Wraps `run_metric_workflow.py` for farm processing.

### automation/scene_monitor.py
Queries Planetary Computer for available scenes.

### automation/logger_config.py
Centralized logging with rotation and summaries.

### automation/config/scheduler.json
Global automation settings.

### automation/run_daily.bat
Windows Task Scheduler batch file.

### run_metric_workflow.py
Core METRIC processing workflow (executed by WorkflowRunner).

---

**Document Version:** 1.0  
**Last Updated:** 2026-05-06  
**METRIC Version:** 1.0.0  
**Automation System Version:** 1.0.0
