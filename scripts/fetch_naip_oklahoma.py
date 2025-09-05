#!/usr/bin/env python3

import os
import sys
import time
import json
import shutil
import logging
import argparse
import zipfile
from pathlib import Path
from typing import List, Dict, Optional

import requests

from subprocess import run, CalledProcessError

ROOT = Path(__file__).resolve().parents[1]
TMP = ROOT / "data" / "tmp" / "naip_ok"
MBTILES_DIR = ROOT / "qgis" / "mbtiles"
VRT = TMP / "ok_naip.vrt"
MBTILES = MBTILES_DIR / "ok_naip.mbtiles"
LOG = MBTILES_DIR / "naip_build.log"

TNM_API = "https://tnmaccess.nationalmap.gov/api/v1/products"

logging.basicConfig(filename=LOG, level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
console = logging.StreamHandler()
console.setLevel(logging.INFO)
logging.getLogger("").addHandler(console)


def tnm_query(params: Dict, timeout: int = 60) -> Dict:
    r = requests.get(TNM_API, params=params, timeout=timeout)
    r.raise_for_status()
    return r.json()


def list_oklahoma_naip(year: Optional[int] = None, timeout: int = 60, limit: Optional[int] = None) -> List[Dict]:
    logging.info("Querying TNM for NAIP Oklahoma (latest year)...")
    # Use place-based query; polyType/polyCode pairs differ by API and cause errors
    params = {
        "datasets": "USDA National Agriculture Imagery Program (NAIP)",
        "place": "Oklahoma",
        "max": 10000,
        "format": "json"
    }
    data = tnm_query(params, timeout=timeout)
    items = data.get("items", [])
    if items:
        if year is None:
            years = sorted({i.get("publicationYear") for i in items if i.get("publicationYear")}, reverse=True)
            year = years[0] if years else None
        if year:
            items = [i for i in items if i.get("publicationYear") == year]
    if limit is not None:
        items = items[: max(0, int(limit))]
    logging.info("Found %d NAIP tiles (year=%s)", len(items), str(year) if year else "latest")
    return items


def ensure_dirs():
    TMP.mkdir(parents=True, exist_ok=True)
    MBTILES_DIR.mkdir(parents=True, exist_ok=True)


def download_items(items: List[Dict], timeout: int = 120, retries: int = 3, backoff: float = 2.0):
    for i, it in enumerate(items, start=1):
        url = it.get("downloadURL") or it.get("url")
        if not url or not url.lower().endswith((".tif", ".tiff", ".zip")):
            continue
        name = url.split("/")[-1]
        out = TMP / name
        if out.exists() and out.stat().st_size > 0:
            logging.info("[%d/%d] Exists %s", i, len(items), name)
        else:
            logging.info("[%d/%d] Downloading %s", i, len(items), url)
            attempt = 0
            while True:
                try:
                    with requests.get(url, stream=True, timeout=timeout) as r:
                        r.raise_for_status()
                        with open(out, "wb") as f:
                            for chunk in r.iter_content(chunk_size=1024 * 1024):
                                if chunk:
                                    f.write(chunk)
                    logging.info("Done %s (%.1f MB)", name, out.stat().st_size / (1024 * 1024))
                    break
                except Exception as e:
                    attempt += 1
                    if attempt > retries:
                        logging.error("Failed to download %s after %d attempts: %s", url, retries, e)
                        break
                    sleep_s = backoff ** attempt
                    logging.warning("Retry %d for %s in %.1fs due to %s", attempt, name, sleep_s, e)
                    time.sleep(sleep_s)

        # If a zip was downloaded, try to extract GeoTIFFs
        if out.suffix.lower() == ".zip" and out.exists():
            try:
                with zipfile.ZipFile(out) as zf:
                    for zi in zf.infolist():
                        if zi.filename.lower().endswith((".tif", ".tiff")):
                            zf.extract(zi, TMP)
                            logging.info("Extracted %s", zi.filename)
            except zipfile.BadZipFile:
                logging.error("Bad zip archive: %s", out)


def build_vrt(overwrite: bool = True):
    # Collect all GeoTIFFs (skip zips)
    tifs = [str(p) for p in TMP.glob("*.tif*") if p.is_file()]
    if not tifs:
        logging.warning("No GeoTIFFs yet; will retry later.")
        return False
    logging.info("Building VRT from %d files...", len(tifs))
    try:
        args = ["gdalbuildvrt"]
        if overwrite and VRT.exists():
            VRT.unlink(missing_ok=True)
        args += [str(VRT)] + tifs
        run(args, check=True)
        return True
    except CalledProcessError as e:
        logging.error("gdalbuildvrt failed: %s", e)
        return False


def build_mbtiles(out_path: Optional[Path] = None):
    if not VRT.exists():
        logging.info("VRT missing; skipping MBTiles step for now")
        return False
    logging.info("Translating VRT to MBTiles (this can take hours)...")
    try:
        dest = out_path or MBTILES
        run(["gdal_translate", "-of", "MBTILES", str(VRT), str(dest)], check=True)
        run(["gdaladdo", "-r", "bilinear", str(dest), "2", "4", "8", "16"], check=True)
        logging.info("MBTiles ready at %s", dest)
        return True
    except CalledProcessError as e:
        logging.error("MBTiles build failed: %s", e)
        return False


def main():
    parser = argparse.ArgumentParser(description="Fetch NAIP imagery for Oklahoma and build MBTiles")
    parser.add_argument("--year", type=int, default=None, help="Publication year to fetch (default: latest)")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of tiles (for testing)")
    parser.add_argument("--timeout", type=int, default=120, help="Request timeout seconds")
    parser.add_argument("--skip-download", action="store_true", help="Skip downloads; only build VRT/MBTiles")
    parser.add_argument("--skip-build", action="store_true", help="Skip building VRT/MBTiles; only download")
    parser.add_argument("--out", type=str, default=None, help="Output MBTiles path (default qgis/mbtiles/ok_naip.mbtiles)")
    args = parser.parse_args()

    ensure_dirs()

    if not args.skip_download:
        items = list_oklahoma_naip(year=args.year, timeout=args.timeout, limit=args.limit)
        if not items:
            logging.error("No NAIP items returned; check TNM availability or params.")
            sys.exit(1)
        download_items(items, timeout=args.timeout)

    if args.skip_build:
        logging.info("Download phase complete; skipping VRT/MBTiles build as requested")
        sys.exit(0)

    if build_vrt():
        out_path = Path(args.out) if args.out else None
        build_mbtiles(out_path)
    logging.info("NAIP job finished (check log and mbtiles folder for progress/results)")


if __name__ == "__main__":
    main()
