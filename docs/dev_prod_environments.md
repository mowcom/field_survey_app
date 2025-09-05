# Dev/Prod Environment Guide

Clean, predictable environments for desktop (QGIS) and mobile (QField) with QFieldCloud.

## Overview
- Separate QFieldCloud projects: `field-wells-dev` (testing) and `field-wells-prod` (production).
- The repository builds a QGIS project and GeoPackage from OCC CSVs and deploys to the selected environment using `deploy.py`.
- Edits flow from devices → QFieldCloud → desktop pulls; monthly data updates flow desktop → QFieldCloud.

## Project Separation
- Dev and Prod use different QFieldCloud projects and different packaged files.
- Dev edits do not affect Prod unless you promote them intentionally.

## Naming & Files
- Dev project name: `field-wells-dev` → `qgis/wells_project_dev.qgz`, `qgis/wells_dev.gpkg`.
- Prod project name: `field-wells-prod` → `qgis/wells_project.qgz`, `qgis/wells.gpkg`.
- Layers in both:
  - Not Visited (visited=0) → visible by default
  - Surveyed (visited=1) → hidden by default
  - Wells (all) → hidden by default
  - Basemaps: Satellite (visible), OpenStreetMap (hidden)

## Desktop (QGIS) Workflow
1) Prepare data (if needed): `python scripts/prepare_wells_gpkg.py`
2) Build project (dev): `/Applications/QGIS.app/Contents/MacOS/bin/python3 scripts/build_qgis_project.py --env dev`
3) Build project (prod): `/Applications/QGIS.app/Contents/MacOS/bin/python3 scripts/build_qgis_project.py --env prod`
4) Open the `.qgz` and verify:
   - Only three editable fields: Exists on site, Small leak, Viable for plugging (Yes/No)
   - Context (County, Operator, Well type, Well name) visible below
   - Copy helpers (Lat, Lon) and (Google Maps Link)
   - Editing any field moves feature from Not Visited to Surveyed
   - Reset survey toggle reverts to Not Visited

## Mobile (QField) Workflow
- Locate button: available on the map toolbar (ensure device location permissions); recenter to GPS.
- Feature actions (open a well → actions menu):
  - Open in Google Maps (view)
  - Open in Google Maps (directions)
- Form: Only three Yes/No fields; context + copy helpers shown.
- Saving any edit immediately moves the well to Surveyed.

## Deployments
- Dev: `python deploy.py --env dev`
- Prod: `python deploy.py --env prod`
- Skip rebuild (only re-upload current project): `python deploy.py --skip-build --env dev`

## QFieldCloud Packaging (first-time per project)
First deployment for a project may require setting the Project File in the web UI.

Steps:
1) Upload via `deploy.py`.
2) In QFieldCloud web UI → Project → Files:
   - Set the uploaded `.qgz` as the Project File (Dev: `wells_project_dev.qgz`, Prod: `wells_project.qgz`).
3) Click Package and wait until the job completes.
4) In QField mobile, sync/download the project.

Notes:
- If you see API errors like `invalid_job` or `HTTP 404 ... /jobs//`, the project file likely isn’t set. Set it once in the UI, package, then future deploys will work reliably.

## Sync Flows
- Upstream (device → cloud): Use QField sync. Edits are written into the GeoPackage, including triggers for `visited` and timestamps.
- Downstream (cloud → desktop): Use QFieldCloud to download the GPKG, or pull via the Files tab.

## Monthly Data Update (desktop → cloud)
1) Place new CSVs in `data/raw/`.
2) `python scripts/prepare_wells_gpkg.py` (schema/trigger-safe; preserves field survey status/audit fields).
3) Build project and deploy to the target environment.

## Promotion Dev → Prod
Option A (rebuild):
- Run the same build against `--env prod` with the approved data snapshot.

Option B (copy package):
- Download the dev GPKG from QFieldCloud, verify, then deploy prod by copying `qgis/wells_dev.gpkg` to `qgis/wells.gpkg` and running `python deploy.py --env prod`.

## Credentials & Isolation
- Use the same QFieldCloud account or separate ones; both supported.
- Environment variables per shell session:
  - `export QFIELDCLOUD_USERNAME=...`
  - `export QFIELDCLOUD_PASSWORD=...`
- Avoid mixing dev and prod deploys in one terminal session without being explicit about `--env`.

## Testing & Health Checks
- Automated: `python test_repo.py` (does not require credentials)
  - Builds data and dev project
  - Packages dev project locally
- Manual: open the `.qgz`, verify layers and form behavior, then deploy.

## Troubleshooting
- Locate button missing on device:
  - Grant location permission; ensure you’re on the map screen (not form view).
- Packaging errors (404/invalid_job):
  - In QFieldCloud UI, set the Project File to the uploaded `.qgz` and click Package once.
- Edits not moving to Surveyed:
  - Ensure `visited` default expression and triggers are applied; redeploy/build if needed.
- Can’t revert a record:
  - Use the `Reset survey` toggle, set to Yes, Save.

