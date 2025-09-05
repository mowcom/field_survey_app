# Lessons Learned

A living document for the team to capture practical, repeatable lessons across desktop (QGIS), mobile (QField), and QFieldCloud.

## How To Contribute
- Add entries under the relevant sections below.
- Prefer crisp, action-oriented bullets; include commands, file paths, or API calls.
- When noting issues, include: context, symptom, root cause, fix, and how to avoid next time.
- Date your entries and sign with your handle (e.g., [2025‑09‑05] @alice).

## Architecture Recap
- Desktop build: CSV → GeoPackage (`scripts/prepare_wells_gpkg.py`) → QGIS project (`scripts/build_qgis_project.py`).
- Mobile app: QField consumes packaged `.qgz` + `.gpkg` from QFieldCloud.
- Environments: Separate QFieldCloud projects for dev (`field-wells-dev`) and prod (`field-wells-prod`).
- UI: Only three editable fields (Exists on site, Small leak, Viable for plugging). Context read-only fields and copy helpers (Lat, Lon, Google Maps Link).
- Data rules: SQLite triggers manage audit fields and visited, plus a Reset survey toggle.

## Technologies & SDKs
- QGIS / PyQGIS: project creation, renderer, edit form config, field aliases, virtual fields.
- SQLite / GeoPackage: schema, triggers (audit timestamps, visited rules, reset toggle), spatial index.
- Python stack: GeoPandas/Shapely for geometry, Pandas for CSV processing.
- QField (mobile): map UI (locate button), feature actions menu, offline-first patterns.
- QFieldCloud SDK: login, upload_file, list_remote_files, delete_files, package_latest, get_project, list_projects.

## Endpoints & Operations (QFieldCloud)
- SDK calls used:
  - `Client.login(username, password)`
  - `Client.list_projects()`
  - `Client.get_project(project_id)`
  - `Client.upload_file(project_id, FileTransferType.PROJECT, local, remote)`
  - `Client.list_remote_files(project_id, skip_metadata=False)`
  - `Client.delete_files(project_id, glob_patterns)` (used to prune legacy MBTiles)
  - `Client.package_latest(project_id)`
- Not (officially) exposed via SDK: setting the Project File (.qgz). Requires QFieldCloud UI after the first upload.

## Environment Management (Dev/Prod)
- Keep separate QFieldCloud projects and filenames: `wells_project_dev.qgz` / `wells_dev.gpkg` vs `wells_project.qgz` / `wells.gpkg`.
- First-time packaging per project requires setting the Project File in the UI, then clicking Package once.
- Promotion from dev → prod can be a fresh build or controlled copy of files (see `docs/dev_prod_environments.md`).

## UI/UX Lessons
- Limit the form to essential fields for speed and reliability.
- Use ValueMap Yes/No for integer fields to avoid string conversion errors; ensure you store 0/1.
- Provide copy helpers (Lat, Lon and Google Maps Link) directly in the form.
- QField’s locate button is part of the map UI (not the form); document where users find it.
- Having a Reset survey toggle dramatically reduces friction when reverting a feature to Not Visited.

## Data & Triggers
- Avoid reserved words in SQL (e.g., `exists`); quote as `"exists"` in triggers.
- Device-side triggers should:
  - Update `last_edit_utc` on insert/update.
  - Flip `visited` to 1 when any status changes from default.
  - Set `visited_at_utc` on first `visited=1`.
- Client-side default expression to flip `visited` enables immediate UI filtering before the trigger fires.

## Packaging & Deployments
- One command deploy: `python deploy.py --env dev|prod` builds and uploads.
- First-time packaging errors (`invalid_job`, `HTTP 404 ... /jobs//`) indicate the Project File is not set. Fix in UI once; subsequent deploys are smooth.
- Keep QFieldCloud Files tidy; delete legacy assets (e.g., MBTiles) to avoid confusion.

## Testing
- `python test_repo.py` validates: environment, data build, project build, and packaging zip creation.
- Tests intentionally avoid live packaging and credentials to remain fast and deterministic.

## Future Improvements (Ideas)
- Optional deploy prune: flag to remove stray remote files on each deploy.
- CI workflow to run tests on PRs and surface build artifacts.
- Optional offline MBTiles integration (opt-in), size-aware packaging.
- Basemap provider toggle (Google Satellite vs ESRI) via env flag.
- API support for setting Project File via SDK (track upstream; replace UI step when available).

---

## Team Entries (Add Yours Below)

### [2025-09-05] @agent (late-join)
- QFieldCloud Project File is a one-time UI setup. Without it, packaging returns `invalid_job` or `404 jobs//`. Documented a clear, repeatable step and added deploy logs.
- ValueMap config matters: using mapping dicts incorrectly can show `label` instead of `Yes/No`. Switched to a clean ValueMap storing 0/1.
- QField locate button can be “missing” if users stay in the form or deny location permissions. Clarified this in guides to reduce support churn.
- Reserved SQL words (`exists`) break triggers silently. Quote identifiers and add tests that exercise trigger paths.
- Less is more in mobile UI: three edits + a reset option cut friction and improved data consistency.

### Template for New Entries
- Date & Author:
- Area (QGIS/QField/SDK/Deploy/Data):
- Context:
- Symptom/Problem:
- Root Cause:
- Fix/Change:
- Prevention/Playbook:
- Related Files/Commands:
- Open Questions:

