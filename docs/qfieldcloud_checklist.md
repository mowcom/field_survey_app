# QFieldCloud Publish Checklist

Use this checklist when publishing/refreshing the project to QFieldCloud.

Prechecks
- `python test_repo.py` passes (non-deploy tests are OK without credentials).
- `data/raw/` contains the latest OCC CSVs (if rebuilding).
- Project builds locally: `python scripts/build_qgis_project.py --env dev`.

Deployment
- Export credentials:
  - `export QFIELDCLOUD_USERNAME="<username>"`
  - `export QFIELDCLOUD_PASSWORD="<password>"`
- Deploy to dev: `python deploy.py --env dev`
- Verify QFieldCloud project updated and packaging completed.

Validation in QField
- Sync the project on device.
- Confirm basemaps (OSM + ESRI Satellite) and symbology (triangles/circles, Gas/Oil/Other colors).
- Open a few wells, update status, sync back.

Notes
- All layers visible by default; no scale rules or labels.
- Audit timestamps and visited flags are set by SQLite triggers in the GeoPackage.
