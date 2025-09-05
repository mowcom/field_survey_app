#!/usr/bin/env python3

import os
import sys
import argparse
from datetime import datetime
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
QGIS_DIR = ROOT / "qgis"


def pick_files(env: str):
    if env == "dev":
        proj = QGIS_DIR / "wells_project_dev.qgz"
        gpkg = QGIS_DIR / "wells_dev.gpkg"
    else:
        proj = QGIS_DIR / "wells_project.qgz"
        gpkg = QGIS_DIR / "wells.gpkg"
    mb_dir = QGIS_DIR / "mbtiles"
    mbtiles = sorted([p for p in mb_dir.glob("*.mbtiles") if p.is_file()]) if mb_dir.exists() else []
    return proj, gpkg, mbtiles


def main():
    ap = argparse.ArgumentParser(description="Package QGIS project + GPKG + MBTiles for QFieldCloud upload")
    ap.add_argument("--env", choices=["dev", "prod"], default="dev")
    ap.add_argument("--out", default=str(ROOT / "dist"), help="Output folder for the package zip")
    args = ap.parse_args()

    proj, gpkg, mbtiles = pick_files(args.env)
    for p in [proj, gpkg]:
        if not p.exists():
            sys.exit(f"Missing required file: {p}")

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d_%H%M")
    out_zip = out_dir / f"qfield_project_{args.env}_{ts}.zip"

    # Create a clean, minimal package with paths relative to repo root
    with ZipFile(out_zip, "w", compression=ZIP_DEFLATED) as z:
        def add(path: Path, arcname: Path):
            z.write(path, arcname.as_posix())

        add(proj, Path("qgis") / proj.name)
        add(gpkg, Path("qgis") / gpkg.name)
        for mb in mbtiles:
            add(mb, Path("qgis/mbtiles") / mb.name)

    print(f"Wrote package: {out_zip}")


if __name__ == "__main__":
    main()

