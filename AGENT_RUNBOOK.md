Agent Runbook (Codex CLI)

Purpose: Minimal, repeatable steps to develop, test, and deploy this repo.

Environment
- Conda: `conda env create -f environment.yml && conda activate field-app`
- Credentials (only when deploying):
  - `export QFIELDCLOUD_USERNAME="<username>"`
  - `export QFIELDCLOUD_PASSWORD="<password>"`

Core Commands
- Deploy (dev): `python deploy.py --env dev`
- Deploy (prod): `python deploy.py --env prod`
- Skip rebuild + deploy: `python deploy.py --skip-build --env dev`
- Build data only: `python scripts/prepare_wells_gpkg.py`
- Build QGIS project only: `python scripts/build_qgis_project.py --env dev`
- Tests: `python test_repo.py`

Assumptions
- QGIS is installed when building the project via PyQGIS (macOS path is commonly `/Applications/QGIS.app/Contents/MacOS/bin/python3`).
- No MapTiler integration is used; basemaps are OpenStreetMap + ESRI Satellite (online).
- GeoPackage audit/visited rules are handled by SQLite triggers (not QGIS defaults).

Validation Flow (quick)
1) `python test_repo.py`
2) `python scripts/prepare_wells_gpkg.py`
3) `python scripts/build_qgis_project.py --env dev`
4) `python deploy.py --env dev`

Troubleshooting
- Missing CSVs: place OCC files in `data/raw/`.
- QGIS not found: run the PyQGIS path explicitly for `build_qgis_project.py`.
- QFieldCloud auth: ensure both `QFIELDCLOUD_USERNAME` and `QFIELDCLOUD_PASSWORD` are exported.

Notes
- Keep symbols simple: STFD=triangles, Orphan=circles; colors by well type (Gas blue, Oil orange, Other purple).
- All layers/basemaps visible by default; no scale rules or labels.
