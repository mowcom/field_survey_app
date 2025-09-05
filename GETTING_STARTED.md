# Getting Started - Field Well Survey

Complete guide to setting up and using the Oklahoma well survey system.

## Overview

Offline-first mobile app for surveying orphan and STFD wells in Oklahoma using QField. Survey teams collect data on well locations, physical condition, and leak detection for regulatory compliance and plugging operations.

## Quick Setup

### 1. Environment Setup
```bash
conda env create -f environment.yml
conda activate field-app
```

### 2. Deploy to QFieldCloud
```bash
# Set credentials (one time setup)
export QFIELDCLOUD_USERNAME="your_username"
export QFIELDCLOUD_PASSWORD="your_password"

# Deploy everything (data + project + upload)
python deploy.py --env dev
```

That's it! The single `deploy.py` command handles:
- Processing CSV data into GeoPackage format
- Building QGIS project with forms and styling
- Uploading to QFieldCloud with timestamp updates

## Field Usage Workflow

### Mobile Setup
1. Install QField app on iPad/iPhone
2. Login with QFieldCloud account
3. Download project for offline use
4. App opens to Oklahoma map with all wells visible

### Well Survey Process
1. **Navigate** - Use map to locate target wells
2. **Identify** - Triangles = STFD (priority), Circles = Orphan wells
3. **Survey** - Tap well symbol → Fill out form → Save
4. **Record** - System tracks: Found location, Well exists, Leak detection
5. **Sync** - Upload collected data when back online

### Map Symbols
- **STFD wells (priority)**: Triangle pins - blue (gas), orange (oil), purple (other)
- **Orphan wells**: Circles - blue (gas), orange (oil), purple (other)

## System Architecture

- **Data Source**: Weekly CSV updates from Oklahoma Corporation Commission
- **Processing**: Python scripts convert CSV → GeoPackage with survey fields
- **Mobile App**: QField provides offline-capable form-based data collection
- **Sync**: QFieldCloud handles data synchronization and team collaboration
- **Forms**: Mobile-optimized survey forms with GPS integration

## File Structure

```
field_app/
├── deploy.py              # Single deployment script
├── data/raw/              # Place OCC CSV files here  
├── qgis/                  # Generated projects and data
├── scripts/               # Data processing utilities
└── docs/field_guide.md    # Field worker instructions
```

## Maintenance

### Monthly Data Updates
```bash
# Download new CSV files from OCC to data/raw/
# Run deployment (preserves existing survey data)
python deploy.py --env prod
```

### Troubleshooting
```bash
# Test environment
python test_repo.py

# Manual rebuild if needed  
python scripts/prepare_wells_gpkg.py
python deploy.py --skip-build --env dev
```

## Support

- **Field Guide**: `docs/field_guide.md` - Complete mobile workflow
- **Data Schema**: `docs/schema_and_triggers.md` - Database specification  
- **Test Suite**: `python test_repo.py` - Validate system health

The system is designed for simplicity: one command deploys everything, offline-first mobile collection, and automatic data preservation during updates.