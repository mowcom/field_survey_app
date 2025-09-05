# Agent Quick Reference

Simplified deployment for future agents.

## Environment Setup
```bash
conda activate field-app
export QFIELDCLOUD_USERNAME="<username>"
export QFIELDCLOUD_PASSWORD="<password>"
```

## Deploy Everything (Simple)
```bash
# Deploy to dev
python deploy.py --env dev

# Deploy to production  
python deploy.py --env prod
```

That's it! The deploy script handles:
- Building GeoPackage from CSV data
- Creating QGIS project with simple styling
- Adding standard OSM + satellite basemaps
- Uploading to QFieldCloud
- Triggering project packaging

## Manual Steps (if needed)
```bash
# Build data only
python scripts/prepare_wells_gpkg.py

# Build project only
python scripts/build_qgis_project.py --env dev

# Deploy without rebuilding
python deploy.py --skip-build --env dev
```

## Styling Overview
- **Single layer** with Gas/Oil/Other + STFD/Orphan categories
- **Shape differentiation** - Pins for STFD, circles for Orphan
- **Consistent colors** - Gas blue, Oil orange, Other purple across both shapes
- **All layers visible by default** (no toggling required)
