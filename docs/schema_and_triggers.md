# Data schema and trigger rules (spec)

Authoritative, offline-first schema for `wells.gpkg` and device-side rules.

## Layer
- Table name: `wells`
- Geometry: POINT (EPSG:4326)

## Fields
- Identity and source
  - `well_id` TEXT NOT NULL UNIQUE  (from `API`, stored as text)
  - `source_list` TEXT NOT NULL  (`ORPHAN` | `STFD`)
  - `dataset_date` TEXT  ISO8601 date the source file represents (optional)
- Location (carried through for analysis)
  - `X` REAL (lon), `Y` REAL (lat)  kept as attributes; geometry is authoritative
- Core carryover attributes (nullable where absent)
  - `well_type` TEXT (WellType)
  - `well_status` TEXT (WellStatus)
  - `orphan_date` TEXT (ISO8601; ORPHAN only)
  - `incident_no` TEXT (STFD only)
  - `well_name` TEXT, `well_number` TEXT
  - `operator_name` TEXT, `operator_number` TEXT
  - `county_name` TEXT, `county_no` INTEGER
  - PLSS: `sec` INTEGER, `township` TEXT, `township_dir` TEXT, `range` TEXT, `range_dir` TEXT, `pm` TEXT
  - Quarters: `quarter` TEXT, `quarter_quarter` TEXT, `quarter_q_q_q` TEXT, `quarter_q_q_q_q` TEXT
  - Footage: `footage_ns` TEXT, `ns` TEXT, `footage_ew` TEXT, `ew` TEXT
- Field collection status (coded integers)
  - `found` SMALLINT  (-1 Unknown, 0 No, 1 Yes) [hidden in UI]
  - `exists` SMALLINT  (-1 Unknown, 0 No, 1 Yes) [UI shows Yes/No only]
  - `small_leak` SMALLINT  (0 No, 1 Yes)
  - `viable_leak` SMALLINT  (0 No, 1 Yes)
  - `visited` SMALLINT  (0 Not Visited, 1 Visited)
- Audit
  - `last_edit_utc` TEXT (ISO8601 UTC)
  - `visited_at_utc` TEXT (ISO8601 UTC; set when visited first becomes 1)

## Indexes and constraints
- UNIQUE index on `well_id`
- Spatial index on geometry
- Optional btree index on `visited`

## Business rules (device-side)
- Update `last_edit_utc` on every INSERT/UPDATE
- If any status field deviates from default, force `visited = 1`
- If `visited` flips 0→1 and `visited_at_utc` is NULL, set `visited_at_utc`
- UI only exposes: `exists`, `small_leak`, `viable_leak`. `found` remains for compatibility but hidden.

## Trigger definitions (to be applied to the GeoPackage)
Note: Stored here for reference; applied during build.

```sql
-- 1) Ensure visited reflects status change and audit timestamps on INSERT
CREATE TRIGGER IF NOT EXISTS wells_insert
AFTER INSERT ON wells
FOR EACH ROW
BEGIN
  UPDATE wells SET
    last_edit_utc = strftime('%Y-%m-%dT%H:%M:%fZ','now'),
    visited = CASE
      WHEN (COALESCE(NEW."found", -1) != -1
         OR COALESCE(NEW."exists", -1) != -1
         OR COALESCE(NEW.small_leak, 0) != 0
         OR COALESCE(NEW.viable_leak, 0) != 0)
      THEN 1 ELSE COALESCE(NEW.visited, 0) END,
    visited_at_utc = CASE
      WHEN (COALESCE(NEW.visited, 0) = 0) AND (
           COALESCE(NEW."found", -1) != -1 OR COALESCE(NEW."exists", -1) != -1 OR
           COALESCE(NEW.small_leak, 0) != 0 OR COALESCE(NEW.viable_leak, 0) != 0)
      THEN strftime('%Y-%m-%dT%H:%M:%fZ','now')
      ELSE NEW.visited_at_utc END
  WHERE well_id = NEW.well_id;
END;

-- 2) Enforce audit/visited rules on UPDATE
CREATE TRIGGER IF NOT EXISTS wells_update
AFTER UPDATE ON wells
FOR EACH ROW
BEGIN
  UPDATE wells SET
    last_edit_utc = strftime('%Y-%m-%dT%H:%M:%fZ','now'),
    visited = CASE
      WHEN (COALESCE(NEW."found", -1) != -1
         OR COALESCE(NEW."exists", -1) != -1
         OR COALESCE(NEW.small_leak, 0) != 0
         OR COALESCE(NEW.viable_leak, 0) != 0)
      THEN 1 ELSE COALESCE(NEW.visited, 0) END,
    visited_at_utc = CASE
      WHEN (COALESCE(OLD.visited,0) = 0 AND COALESCE(NEW.visited,0) = 1 AND OLD.visited_at_utc IS NULL)
      THEN strftime('%Y-%m-%dT%H:%M:%fZ','now')
      ELSE NEW.visited_at_utc END
  WHERE well_id = NEW.well_id;
END;
```

## Enumerations (Value Maps)
- found: -1 Unknown, 0 No, 1 Yes
- exists: -1 Unknown, 0 No, 1 Yes
- small_leak: 0 No, 1 Yes
- viable_leak: 0 No, 1 Yes
- visited: 0 Not Visited, 1 Visited

## Notes
- Dates as TEXT in ISO8601 simplify cross-tool compatibility (QGIS/QField/SQLite).
- `well_id` retained as TEXT to avoid scientific notation issues on large API values.
