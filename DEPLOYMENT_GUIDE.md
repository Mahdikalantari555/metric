# METRIC Automation Sentinel - Server Deployment Guide

This guide provides comprehensive instructions for deploying the METRIC Automation Sentinel system on a production server with automated daily processing via cron (Linux) or Task Scheduler (Windows).

---

## Table of Contents

1. [System Requirements](#1-system-requirements)
2. [Server Installation](#2-server-installation)
3. [Farm Registration](#3-farm-registration)
4. [Automated Daily Processing](#4-automated-daily-processing)
   - [Windows (Task Scheduler)](#41-windows-task-scheduler)
   - [Linux (cron)](#42-linux-cron)
5. [Monitoring and Maintenance](#5-monitoring-and-maintenance)
6. [Troubleshooting](#6-troubleshooting)

---

## 1. System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| OS | Windows Server 2019 / Ubuntu 20.04 | Windows Server 2022 / Ubuntu 22.04 |
| CPU | 4 cores | 8+ cores |
| RAM | 16 GB | 32+ GB |
| Storage | 100 GB SSD | 500+ GB SSD |
| Python | 3.9+ | 3.10+ |
| Network | 10 Mbps | 50+ Mbps |

### Required Python Packages

All dependencies are specified in `environment.yml`. Key packages include:
- `numpy`, `xarray`, `rasterio` - Core scientific computing
- `geopandas`, `shapely` - Vector data handling
- `pystac-client`, `planetary-computer` - Sentinel-2 data access
- `loguru`, `pyyaml` - Logging and configuration

---

## 2. Server Installation

### Step 1: Clone the Repository

```bash
# Linux
cd /opt
sudo git clone https://github.com/yourorg/metric-automation-sentinel.git
sudo chown -R $USER:$USER metric-automation-sentinel
cd metric-automation-sentinel

# Windows (PowerShell as Administrator)
cd C:\
git clone https://github.com/yourorg/metric-automation-sentinel.git
```

### Step 2: Create Conda Environment

```bash
# Linux/Windows (Anaconda Prompt)
conda env create -f environment.yml
conda activate metric-env
```

### Step 3: Install in Development Mode

```bash
pip install -e .
```

### Step 4: Verify Installation

```bash
python -c "import metric_et, sentinel; print('Installation successful!')"
```

### Step 5: Create Required Directories

```bash
# Linux
mkdir -p automation/logs
mkdir -p data_storage

# Windows
mkdir automation\logs
mkdir data_storage
```

---

## 3. Farm Registration

Register each farm/area of interest once before running automated processing:

```bash
python -m sentinel.app \
    --mode register \
    --aoi-name myfarm \
    --roi /path/to/roi.geojson \
    --start 2025-01-01 \
    --end 2025-12-31
```

### ROI File Format

GeoJSON Feature or FeatureCollection with polygon geometry:

```json
{
  "type": "Feature",
  "geometry": {
    "type": "Polygon",
    "coordinates": [[[51.0, 35.0], [51.5, 35.0], [51.5, 35.5], [51.0, 35.5], [51.0, 35.0]]]
  },
  "properties": {
    "name": "My Farm"
  }
}
```

---

## 4. Automated Daily Processing

### 4.1 Windows (Task Scheduler)

#### Method 1: Using the Provided Batch File

The `automation/run_daily.bat` file is pre-configured for Windows Task Scheduler.

1. **Edit the batch file** to match your installation path:
   ```batch
   cd /d E:\RSGIS\SatAgrySys\METRIC
   ```

2. **Open Task Scheduler** (`taskschd.msc`)

3. **Create Basic Task**:
   - **Name**: `METRIC_Daily_Automation`
   - **Trigger**: Daily, 02:00 AM
   - **Action**: Start a program
     - Program: `cmd.exe`
     - Arguments: `/c "E:\RSGIS\SatAgrySys\METRIC\automation\run_daily.bat"`
   - **Finish**

#### Method 2: PowerShell Command

```powershell
$action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument '/c "E:\RSGIS\SatAgrySys\METRIC\automation\run_daily.bat"'
$trigger = New-ScheduledTaskTrigger -Daily -At 2am
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

Register-ScheduledTask -TaskName "METRIC_Daily_Automation" -Action $action -Trigger $trigger -Settings $settings
```

### 4.2 Linux (cron)

#### Step 1: Create a Wrapper Script

Create `run_daily.sh` in the project root:

```bash
#!/bin/bash
# METRIC Automation Daily Runner
# Run from project directory

cd /opt/metric-automation-sentinel

# Activate conda environment
source /opt/conda/etc/profile.d/conda.sh
conda activate metric-env

# Run daily processing
python -m automation.app --mode daily >> automation/logs/cron.log 2>&1

# Log completion
echo "$(date '+%Y-%m-%d %H:%M:%S') - Daily run completed" >> automation/logs/cron.log
```

Make it executable:

```bash
chmod +x run_daily.sh
```

#### Step 2: Add to Crontab

```bash
crontab -e
```

Add the following line to run at 2:00 AM daily:

```cron
0 2 * * * /opt/metric-automation-sentinel/run_daily.sh
```

#### Step 3: Verify Crontab

```bash
crontab -l
```

---

## 5. Monitoring and Maintenance

### Log Files

| File | Description |
|------|-------------|
| `automation/logs/automation.log` | Main application log |
| `automation/logs/daily_summary.log` | CSV summary of daily runs |
| `automation/logs/cron.log` | Cron execution log (Linux) |
| `automation/logs/{farm_name}.log` | Per-farm detailed logs |

### Status Check Commands

```bash
# List all registered farms
python -m automation.app --mode list

# Check farm status
python -m automation.app --mode status

# Check available scenes for a farm
python -m automation.app --mode check-scenes --aoi-name myfarm
```

### Disk Space Management

```bash
# Linux - Check disk usage
du -sh data_storage/*/scenes/

# Clean old scenes (keep last 30 days)
find data_storage/*/scenes/ -type d -mtime +30 -exec rm -rf {} +
```

### Health Check Script

Create `healthcheck.py`:

```python
#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from automation import FarmManager

def main():
    fm = FarmManager()
    farms = fm.get_enabled_farms()
    
    print(f"Total enabled farms: {len(farms)}")
    for farm in farms:
        print(f"  - {farm['aoi_name']}: last processed {farm.get('last_processed_date', 'Never')}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

---

## 6. Troubleshooting

### Common Issues

#### Issue: "No scenes found"

**Solution**:
```bash
# Check available scenes manually
python -m automation.app --mode check-scenes --aoi-name myfarm
```

#### Issue: "Task Scheduler not running"

**Solution**:
```cmd
# Check task status
schtasks /query /tn "METRIC_Daily_Automation"

# Run manually
schtasks /run /tn "METRIC_Daily_Automation"
```

#### Issue: "Out of disk space"

**Solution**:
```bash
# Clean old scenes
find data_storage/*/scenes/ -type d -mtime +30 -exec rm -rf {} +
```

#### Issue: "Conda command not found" (Linux cron)

**Solution**: Use full path to conda in the wrapper script:
```bash
export PATH="/opt/conda/bin:$PATH"
```

### Log Analysis

```bash
# Linux - Check recent errors
grep -i "error\|exception" automation/logs/automation.log | tail -20

# Windows - PowerShell
Select-String -Path "automation\logs\automation.log" -Pattern "error|exception" | Select-Object -Last 20
```

---

## Quick Reference

### Essential Commands

```bash
# Register a farm
python -m sentinel.app --mode register --aoi-name myfarm --roi roi.geojson --start 2025-01-01 --end 2025-12-31

# Run historical processing
python -m automation.app --mode historical --aoi-name myfarm

# Run daily processing
python -m automation.app --mode daily

# Check status
python -m automation.app --mode status

# List farms
python -m automation.app --mode list
```

### Cron Quick Setup

```bash
# Edit crontab
crontab -e

# Add this line for 2 AM daily run
0 2 * * * cd /opt/metric-automation-sentinel && /opt/conda/envs/metric-env/bin/python -m automation.app --mode daily >> automation/logs/cron.log 2>&1
```

---

**Document Version**: 1.0  
**Last Updated**: 2026-05-16