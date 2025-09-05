# Agent Quick Reference

Simplified deployment for future agents.

## Environment Setup
```bash
conda activate field-app
export QFIELDCLOUD_USERNAME="<username>"
export QFIELDCLOUD_PASSWORD="<password>"
```

## Deploy
```bash
# Dev
python deploy.py --env dev

# Production  
python deploy.py --env prod
```

That's it! `deploy.py` builds data + project and uploads to QFieldCloud.

First-time packaging (one-time per project):
- In QFieldCloud web UI → Project → Files, set the `.qgz` as the Project File (Dev: `wells_project_dev.qgz`, Prod: `wells_project.qgz`) and click Package once.

## Manual (if needed)
```bash
# Build data only
python scripts/prepare_wells_gpkg.py

# Build project only
/Applications/QGIS.app/Contents/MacOS/bin/python3 scripts/build_qgis_project.py --env dev

# Deploy without rebuilding
python deploy.py --skip-build --env dev
```

## UI Overview
- Edit only: Exists on site, Small leak, Viable for plugging (Yes/No)
- Read-only context: County, Operator, Well type, Well name
- Links: Lat, Lon and Google Maps Link
- Layers: Not Visited visible by default; Surveyed/All Wells hidden
- Basemaps: Satellite (visible) + OpenStreetMap (hidden)
