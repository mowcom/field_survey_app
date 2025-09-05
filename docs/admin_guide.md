# Admin Guide

How to manage data, publish to QFieldCloud, and run monthly updates.

## Daily/weekly
- Open QGIS, pull the latest `wells.gpkg` from QFieldCloud if needed.
- Review edits and timestamps; export CSV/shapefile as required.
- Publish updates to QFieldCloud using QField Sync (see `docs/qfieldcloud_checklist.md`).

## Monthly update
- Follow `docs/admin_workflow.md` to merge the new Orphan/STFD CSVs.
- Rebuild `wells.gpkg` without overwriting field status/audit fields.
- Run QA checks (null/duplicate `well_id`, geometry present, OK bbox).
- Republish the project to QFieldCloud.

## Basemaps
- Online basemaps only (Satellite + OpenStreetMap). Offline MBTiles are not used in this build.

## Project configuration
- Forms, filters, and actions are specified in `docs/qgis_ui_spec.md`.
- Symbology is defined in `docs/style_guide.md`.
