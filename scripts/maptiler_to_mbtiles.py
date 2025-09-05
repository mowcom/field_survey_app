#!/usr/bin/env python3

import os
import math
import time
import sqlite3
import argparse
from pathlib import Path
from typing import Tuple

import requests


def lonlat_to_tile(lon: float, lat: float, z: int) -> Tuple[int, int]:
    lat = max(min(lat, 85.05112878), -85.05112878)
    n = 2 ** z
    x = (lon + 180.0) / 360.0 * n
    lat_rad = math.radians(lat)
    y = (1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n
    return int(math.floor(x)), int(math.floor(y))


def ensure_db(path: Path, name: str, bounds: Tuple[float, float, float, float], minzoom: int, maxzoom: int) -> sqlite3.Connection:
    if path.exists():
        path.unlink()
    con = sqlite3.connect(str(path))
    cur = con.cursor()
    cur.executescript(
        """
        CREATE TABLE metadata (name TEXT, value TEXT);
        CREATE TABLE tiles (zoom_level INTEGER, tile_column INTEGER, tile_row INTEGER, tile_data BLOB);
        CREATE UNIQUE INDEX tile_index ON tiles (zoom_level, tile_column, tile_row);
        """
    )
    minlon, minlat, maxlon, maxlat = bounds
    meta = {
        "name": name,
        "type": "baselayer",
        "version": "1.3",
        "description": "MapTiler Satellite (downloaded subset for offline)",
        "format": "jpg",
        "bounds": f"{minlon},{minlat},{maxlon},{maxlat}",
        "minzoom": str(minzoom),
        "maxzoom": str(maxzoom),
        "attribution": "© MapTiler, © OpenStreetMap contributors",
    }
    cur.executemany("INSERT INTO metadata(name,value) VALUES(?,?)", list(meta.items()))
    con.commit()
    return con


def insert_tile(con: sqlite3.Connection, z: int, x: int, y_xyz: int, data: bytes) -> None:
    # MBTiles expects TMS row indexing (flip Y)
    n = 2 ** z
    y_tms = (n - 1) - y_xyz
    con.execute(
        "INSERT OR REPLACE INTO tiles(zoom_level, tile_column, tile_row, tile_data) VALUES(?,?,?,?)",
        (z, x, y_tms, sqlite3.Binary(data)),
    )


def download_tiles_to_mbtiles(key: str, bounds: Tuple[float, float, float, float], minzoom: int, maxzoom: int, out: Path, delay: float = 0.0, timeout: int = 60) -> None:
    minlon, minlat, maxlon, maxlat = bounds
    con = ensure_db(out, out.stem, bounds, minzoom, maxzoom)
    session = requests.Session()
    total = 0
    try:
        for z in range(minzoom, maxzoom + 1):
            x_min, y_max = lonlat_to_tile(minlon, minlat, z)
            x_max, y_min = lonlat_to_tile(maxlon, maxlat, z)
            if x_max < x_min:
                x_min, x_max = x_max, x_min
            if y_max < y_min:
                y_min, y_max = y_max, y_min
            for x in range(x_min, x_max + 1):
                for y in range(y_min, y_max + 1):
                    url = f"https://api.maptiler.com/tiles/satellite-v2/{z}/{x}/{y}.jpg?key={key}"
                    r = session.get(url, timeout=timeout)
                    if r.status_code == 200 and r.content:
                        insert_tile(con, z, x, y, r.content)
                        total += 1
                    else:
                        # Tolerate missing tiles
                        pass
                    if delay:
                        time.sleep(delay)
            con.commit()
    finally:
        con.commit()
        con.close()
    print(f"Wrote {out} with {total} tiles (z{minzoom}-{maxzoom})")


def main():
    ap = argparse.ArgumentParser(description="Download MapTiler Satellite XYZ tiles into an MBTiles file for offline use")
    ap.add_argument("--key", default=os.getenv("MAPTILER_API_KEY"), help="MapTiler API key (or set MAPTILER_API_KEY)")
    ap.add_argument("--bbox", nargs=4, type=float, metavar=("MINLON","MINLAT","MAXLON","MAXLAT"), required=True, help="Bounding box in lon/lat (EPSG:4326)")
    ap.add_argument("--minzoom", type=int, default=8)
    ap.add_argument("--maxzoom", type=int, default=14)
    ap.add_argument("--delay", type=float, default=0.0, help="Delay seconds between requests (to be gentle)")
    ap.add_argument("--timeout", type=int, default=60)
    ap.add_argument("--out", type=str, default="qgis/mbtiles/ok_sat_maptiler.mbtiles")
    args = ap.parse_args()

    if not args.key:
        raise SystemExit("Provide --key or set MAPTILER_API_KEY")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    download_tiles_to_mbtiles(args.key, tuple(args.bbox), args.minzoom, args.maxzoom, out, delay=args.delay, timeout=args.timeout)


if __name__ == "__main__":
    main()

