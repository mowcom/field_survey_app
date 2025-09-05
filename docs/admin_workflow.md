# Admin Monthly Update Workflow (spec)

Goal: Refresh master `wells.gpkg` from monthly Excel/CSV without losing field edits.

## Inputs
- Orphan CSV (monthly)
- STFD CSV (monthly)

## Steps (QGIS / Model)
1. Load both CSVs as tables.
2. Add `source_list` column (ORPHAN / STFD), normalize columns to schema names.
3. Create points from X (lon) / Y (lat) with EPSG:4326.
4. Merge into a single temporary layer; cast API to TEXT as `well_id`.
5. Update existing features in `wells.gpkg` by `well_id` with non-field attributes only:
   - Do not overwrite: found, exists, small_leak, viable_leak, visited, visited_at_utc, last_edit_utc.
6. Append new wells (not present in `wells.gpkg`).
7. Run QA checks:
   - Null or duplicate `well_id`
   - Missing geometry
   - Coordinates outside Oklahoma bbox
8. Save/replace `wells` layer in GeoPackage.

## Outputs
- Updated `wells.gpkg` ready for publish.

## Notes
- Consider building this as a QGIS Graphical Model for repeatability.
- Keep a dated backup of prior GeoPackage for rollback.
