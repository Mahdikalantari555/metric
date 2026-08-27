# METRIC Automation Sentinel

A comprehensive remote sensing web application for automated farm monitoring and evapotranspiration calculation using Sentinel-2 satellite data from Microsoft Planetary Computer.

## Overview

METRIC Automation Sentinel extends the traditional METRIC (Mapping Evapotranspiration with a Residual-Based Calibration) model to provide automated, daily processing of agricultural fields using Sentinel-2 satellite imagery. The system handles farm registration, automatic scene detection, data retrieval, METRIC processing, and result storage with minimal manual intervention.

## Key Features

- **Automated Sentinel-2 Data Ingestion**: Automatic fetching from Microsoft Planetary Computer using STAC API
- **Farm Registration System**: Register and manage multiple areas of interest with GeoJSON boundaries
- **Daily Automation**: Fully automated processing with cron (Linux) or Task Scheduler (Windows)
- **Multi-Farm Support**: Process hundreds of farms in a single automated run
- **Scene Monitoring**: Automatic detection of new satellite scenes for registered farms
- **Comprehensive Logging**: Detailed logs for monitoring, debugging, and audit trails
- **Flexible Output**: GeoTIFF, NetCDF, CSV statistics, and visualization products
- **Docker Ready**: Containerized deployment option for cloud environments

## Project Structure

```
sentinel/
├── app.py           # CLI entry point for farm registration and processing
├── config.py        # Configuration management
├── fetcher.py       # Sentinel-2 data fetching from Planetary Computer
├── pipeline.py      # METRIC processing pipeline for Sentinel data
└── runner.py        # Execution engine for historical and daily processing

automation/
├── app.py           # Main CLI for automated processing
├── farm_manager.py  # Farm registry and configuration
├── workflow_runner.py # Execution engine
├── scene_monitor.py # Scene detection
└── run_daily.bat    # Windows batch file for Task Scheduler

metric_et/           # Core METRIC ET processing engine (see metric_et/README.md)
├── pipeline/        # METRIC pipeline implementation
├── et/              # ET calculation modules
├── surface/         # Surface property calculations
├── energy_balance/  # Energy balance components
├── calibration/     # Anchor pixel calibration
└── io/              # Input/output handling
```

## Quick Start

### 1. Installation

```bash
# Clone repository
git clone <repository-url>
cd METRIC

# Create conda environment
conda env create -f environment.yml
conda activate metric-env

# Install in development mode
pip install -e .
```

### 2. Register a Farm

```bash
python -m sentinel.app --mode register \
    --aoi-name "myfarm" \
    --roi "/path/to/farm_boundary.geojson" \
    --start "2025-01-01" \
    --end "2025-12-31"
```

### 3. Run Historical Processing (Optional)

```bash
python -m automation.app --mode historical --aoi-name "myfarm"
```

### 4. Setup Daily Automation

#### Linux (cron):
```bash
# Create wrapper script
echo '#!/bin/bash
cd /opt/metric-automation-sentinel
source /opt/conda/etc/profile.d/conda.sh
conda activate metric-env
python -m automation.app --mode daily >> automation/logs/cron.log 2>&1
echo "$(date '\''+%Y-%m-%d %H:%M:%S'\'') - Daily run completed" >> automation/logs/cron.log' > run_daily.sh

chmod +x run_daily.sh

# Add to crontab (runs daily at 2 AM)
(crontab -l 2>/dev/null; echo "0 2 * * * /opt/metric-automation-sentinel/run_daily.sh") | crontab -
```

#### Windows (Task Scheduler):
1. Edit `automation/run_daily.bat` to set correct path
2. Create scheduled task:
   - Action: Start program `cmd.exe`
   - Arguments: `/c "C:\path\to\METRIC\automation\run_daily.bat"`
   - Trigger: Daily at 2:00 AM

## Core Components

### Sentinel Module (`sentinel/`)
Handles Sentinel-2 specific operations:
- **Fetcher**: Retrieves Sentinel-2 data from Microsoft Planetary Computer
- **Pipeline**: Applies METRIC algorithm to Sentinel-2 data
- **Runner**: Manages historical and daily processing workflows
- **App**: CLI for farm registration and manual processing

### Automation Module (`automation/`)
Manages automated workflows:
- **Farm Manager**: Registry and configuration of monitored farms
- **Workflow Runner**: Executes processing workflows
- **Scene Monitor**: Detects new available satellite scenes
- **App**: Main automation CLI (daily, historical, status modes)

### Core METRIC Engine (`metric_et/`)
The underlying METRIC ET processing engine (detailed documentation in `metric_et/README.md`):
- Energy balance calculations (Rn, G, H, LE)
- Anchor pixel calibration
- ET computation (instantaneous and daily)
- Quality assessment and flagging
- Multiple output formats (GeoTIFF, NetCDF, CSV)

## Entry Points

| Command | Description |
|---------|-------------|
| `python -m sentinel.app --mode register` | Register a new farm/ROI |
| `python -m sentinel.app --mode historical` | Run historical processing for a farm |
| `python -m automation.app --mode daily` | Run daily processing for all enabled farms |
| `python -m automation.app --mode status` | Check processing status of all farms |
| `python -m automation.app --mode list` | List all registered farms |
| `python -m automation.app --mode check-scenes` | Check available scenes for a farm |

## Output Products

For each processed scene, the system generates:
- **GeoTIFF Files**: ET_daily, ET_inst, ETrF, LE, H, Rn, G, dT
- **Statistics CSV**: Pixel statistics for each output band
- **Visualizations**: Color-coded maps and time series plots
- **Metadata JSON**: Processing parameters, calibration coefficients, timestamps
- **Log Files**: Detailed processing logs for monitoring

## Deployment Guide

For comprehensive server deployment instructions including system requirements, installation steps, and automation setup, see [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md).

## Related Documentation

- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Server deployment and automation setup
- [METRIC_Automation_Documentation.md](METRIC_Automation_Documentation.md) - Detailed automation system documentation
- [metric_et/README.md](metric_et/README.md) - Core METRIC ET processing engine documentation
- [METRIC_ET_Comprehensive_Documentation.md](METRIC_ET_Comprehensive_Documentation.md) - Full technical documentation of METRIC algorithm

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- University of Idaho for the original METRIC methodology
- Microsoft Planetary Computer for Sentinel-2 data access
- USGS for Landsat data products (used in validation)
- Open source community for the Python ecosystem

**Version**: 1.0.0  
**Last Updated**: 2026-05-16
