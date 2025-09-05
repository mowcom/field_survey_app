#!/usr/bin/env python3

import os
import re
import glob
import sqlite3
from datetime import datetime
from typing import Optional, Tuple

import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
RAW_DIR = os.path.join(PROJECT_ROOT, "data", "raw")
PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "processed")
OUT_GPKG = os.path.join(PROCESSED_DIR, "wells.gpkg")
LAYER_NAME = "wells"

CSV_PATTERNS = {
    "ORPHAN": os.path.join(RAW_DIR, "*orphan*.csv"),
    "STFD": os.path.join(RAW_DIR, "*stfd*.csv"),
}

DATE_RE = re.compile(r"(20\d{2}-\d{2}-\d{2})")


def parse_date_from_filename(path: str) -> Optional[str]:
    m = DATE_RE.search(os.path.basename(path))
    if m:
        return m.group(1)
    return None


def latest_by_date(pattern: str) -> Optional[str]:
    candidates = glob.glob(pattern)
    if not candidates:
        return None
    def sort_key(p: str) -> Tuple[int, str]:
        d = parse_date_from_filename(p)
        return (0 if d else 1, d or "", p)
    candidates.sort(key=sort_key, reverse=True)
    return candidates[0]


def load_csv(path: str, source_list: str, dataset_date: Optional[str]) -> pd.DataFrame:
    # Read with explicit dtypes to preserve API as text
    df = pd.read_csv(path, dtype={"API": str}, keep_default_na=False)

    # Standardize column names to our schema
    rename_map = {
        "API": "well_id",
        "WellType": "well_type",
        "WellStatus": "well_status",
        "OrphanDate": "orphan_date",
        "WellName": "well_name",
        "WellNumber": "well_number",
        "OperatorName": "operator_name",
        "OperatorNumber": "operator_number",
        "IncidentNo": "incident_no",
        "X": "X",
        "Y": "Y",
        "CountyName": "county_name",
        "CountyNo": "county_no",
        "Sec": "sec",
        "Township": "township",
        "TownshipDir": "township_dir",
        "Range": "range",
        "RangeDir": "range_dir",
        "PM": "pm",
        "Quarter": "quarter",
        "QuarterQuarter": "quarter_quarter",
        "QuarterQuarterQuarter": "quarter_q_q_q",
        "QuarterQuarterQuarterQuarter": "quarter_q_q_q_q",
        "FootageNS": "footage_ns",
        "NS": "ns",
        "FootageEW": "footage_ew",
        "EW": "ew",
    }
    df = df.rename(columns=rename_map)

    # Keep only columns we know + add missing ones later
    wanted = set(rename_map.values())
    keep_cols = [c for c in df.columns if c in wanted]
    df = df[keep_cols].copy()

    # Coerce basic types
    for c in ("X", "Y"):
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    if "county_no" in df.columns:
        df["county_no"] = pd.to_numeric(df["county_no"], errors="coerce").astype("Int64")
    if "sec" in df.columns:
        df["sec"] = pd.to_numeric(df["sec"], errors="coerce").astype("Int64")

    # Add source fields
    df["source_list"] = source_list
    if dataset_date:
        df["dataset_date"] = dataset_date

    # Ensure well_id is text and strip spaces
    df["well_id"] = df["well_id"].astype(str).str.strip()

    return df


def ensure_columns(df: pd.DataFrame) -> pd.DataFrame:
    # Add missing carryover columns
    carryover_cols = [
        "well_type","well_status","orphan_date","incident_no","well_name","well_number",
        "operator_name","operator_number","county_name","county_no","sec","township",
        "township_dir","range","range_dir","pm","quarter","quarter_quarter","quarter_q_q_q",
        "quarter_q_q_q_q","footage_ns","ns","footage_ew","ew","X","Y","dataset_date",
    ]
    for c in carryover_cols:
        if c not in df.columns:
            df[c] = pd.NA

    # Status fields defaults (align with app expectations)
    status_defaults = {
        "found": -1,        # -1=Unknown, 0=No, 1=Yes (kept but hidden in UI)
        "exists": -1,       # -1=Unknown, 0=No, 1=Yes (UI uses Yes/No only)
        "small_leak": 0,    # 0=No, 1=Yes
        "viable_leak": 0,   # 0=No, 1=Yes
        "visited": 0,       # 0=Not Visited, 1=Visited
    }
    for c, v in status_defaults.items():
        if c not in df.columns:
            df[c] = v

    # Audit fields and editor name
    for c in ("last_edit_utc", "visited_at_utc", "editor_name"):
        if c not in df.columns:
            df[c] = pd.NA

    # Optional attachments
    for c in ("photo_path", "voice_note"):
        if c not in df.columns:
            df[c] = pd.NA

    return df


def apply_triggers(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    # Unique index on well_id
    cur.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_wells_well_id
        ON wells (well_id);
        """
    )
    # Optional index on visited
    cur.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_wells_visited
        ON wells (visited);
        """
    )
    # Insert trigger: set audit timestamps and visited when status changes
    cur.execute(
        """
        CREATE TRIGGER IF NOT EXISTS wells_insert
        AFTER INSERT ON wells
        FOR EACH ROW
        BEGIN
          UPDATE wells SET
            last_edit_utc = strftime('%Y-%m-%dT%H:%M:%fZ','now'),
            visited = CASE
              WHEN (COALESCE(NEW.exists, -1) != -1
                 OR COALESCE(NEW.found, -1) != -1
                 OR COALESCE(NEW.small_leak, 0) != 0
                 OR COALESCE(NEW.viable_leak, 0) != 0)
              THEN 1 ELSE COALESCE(NEW.visited, 0) END,
            visited_at_utc = CASE
              WHEN (COALESCE(NEW.visited, 0) = 0) AND (
                   COALESCE(NEW.exists, -1) != -1 OR
                   COALESCE(NEW.found, -1) != -1 OR
                   COALESCE(NEW.small_leak, 0) != 0 OR COALESCE(NEW.viable_leak, 0) != 0)
              THEN strftime('%Y-%m-%dT%H:%M:%fZ','now')
              ELSE NEW.visited_at_utc END
          WHERE well_id = NEW.well_id;
        END;
        """
    )
    # Update trigger: same logic on update
    cur.execute(
        """
        CREATE TRIGGER IF NOT EXISTS wells_update
        AFTER UPDATE ON wells
        FOR EACH ROW
        BEGIN
          UPDATE wells SET
            last_edit_utc = strftime('%Y-%m-%dT%H:%M:%fZ','now'),
            visited = CASE
              WHEN (COALESCE(NEW.exists, -1) != -1
                 OR COALESCE(NEW.found, -1) != -1
                 OR COALESCE(NEW.small_leak, 0) != 0
                 OR COALESCE(NEW.viable_leak, 0) != 0)
              THEN 1 ELSE COALESCE(NEW.visited, 0) END,
            visited_at_utc = CASE
              WHEN (COALESCE(OLD.visited,0) = 0 AND COALESCE(NEW.visited,0) = 1 AND OLD.visited_at_utc IS NULL)
              THEN strftime('%Y-%m-%dT%H:%M:%fZ','now')
              ELSE NEW.visited_at_utc END
          WHERE well_id = NEW.well_id;
        END;
        """
    )
    conn.commit()


def create_survey_table(conn: sqlite3.Connection) -> None:
    """Create separate well_surveys table for clean mobile data collection"""
    cur = conn.cursor()
    
    # Create well_surveys table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS well_surveys (
            survey_id INTEGER PRIMARY KEY AUTOINCREMENT,
            well_id TEXT NOT NULL,
            found SMALLINT DEFAULT -1,  -- -1=Unknown, 0=No, 1=Yes
            well_exists SMALLINT DEFAULT -1,  -- -1=Unknown, 0=No, 1=Yes  
            small_leak SMALLINT DEFAULT 0,  -- 0=No, 1=Yes
            viable_leak SMALLINT DEFAULT 0,  -- 0=No, 1=Yes
            notes TEXT,
            surveyor_name TEXT,
            survey_date TEXT,  -- ISO8601 UTC
            survey_location TEXT,  -- WKT POINT for GPS location where survey conducted
            FOREIGN KEY (well_id) REFERENCES wells(well_id)
        );
        """
    )
    
    # Create indexes
    cur.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_surveys_well_id
        ON well_surveys (well_id);
        """
    )
    
    cur.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_surveys_date  
        ON well_surveys (survey_date);
        """
    )
    
    # Create trigger to update wells table when survey is created
    cur.execute(
        """
        CREATE TRIGGER IF NOT EXISTS survey_update_well
        AFTER INSERT ON well_surveys
        FOR EACH ROW
        BEGIN
          UPDATE wells SET
            visited = 1,
            visited_at_utc = COALESCE(visited_at_utc, NEW.survey_date),
            last_edit_utc = NEW.survey_date
          WHERE well_id = NEW.well_id;
        END;
        """
    )
    
    print("✅ Created well_surveys table with relationships")
    conn.commit()


def main() -> None:
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    paths = {}
    for key, pattern in CSV_PATTERNS.items():
        p = latest_by_date(pattern)
        if not p:
            raise FileNotFoundError(f"No CSV found for {key} using pattern: {pattern}")
        paths[key] = p

    orphan_date = parse_date_from_filename(paths["ORPHAN"]) or datetime.utcnow().date().isoformat()
    stfd_date = parse_date_from_filename(paths["STFD"]) or datetime.utcnow().date().isoformat()

    df_orphan = load_csv(paths["ORPHAN"], "ORPHAN", orphan_date)
    df_stfd = load_csv(paths["STFD"], "STFD", stfd_date)

    # Concatenate and ensure full schema
    df = pd.concat([df_stfd, df_orphan], ignore_index=True, sort=False)
    df = ensure_columns(df)

    # Drop rows with invalid coordinates
    df = df[pd.notna(df["X"]) & pd.notna(df["Y"])].copy()

    # Priority: keep STFD when duplicate well_id exists
    priority = {"STFD": 0, "ORPHAN": 1}
    df["_priority"] = df["source_list"].map(priority).fillna(2)
    df = df.sort_values(["well_id", "_priority"])  # ascending priority
    df = df.drop_duplicates(subset=["well_id"], keep="first")
    df = df.drop(columns=["_priority"])  # cleanup

    # Build GeoDataFrame
    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df["X"], df["Y"], crs="EPSG:4326"),
        crs="EPSG:4326",
    )

    # Remove existing GPKG to avoid stale schema
    if os.path.exists(OUT_GPKG):
        os.remove(OUT_GPKG)

    # Write to GeoPackage
    gdf.to_file(OUT_GPKG, layer=LAYER_NAME, driver="GPKG")

    # Apply triggers and indexes
    with sqlite3.connect(OUT_GPKG) as conn:
        apply_triggers(conn)

    print(f"Wrote {OUT_GPKG}:{LAYER_NAME} with {len(gdf)} wells (STFD prioritized on duplicates)")


if __name__ == "__main__":
    main()
