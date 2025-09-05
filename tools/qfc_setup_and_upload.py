#!/usr/bin/env python3
"""
Create a QFieldCloud project and upload files using the modern SDK (qfieldcloud_sdk).

Env vars:
  QFIELDCLOUD_USERNAME / QFIELDCLOUD_PASSWORD (required)
  QFIELDCLOUD_BASE_URL (default: https://app.qfield.cloud/api/v1/)

Args:
  --name <project-name>            Project name (default: field-wells-dev)
  --zip  <path-to-zip>             Package zip to upload (default: newest dist/qfield_project_dev_*.zip)

Behavior:
  - Creates the project if missing; otherwise reuses it.
  - Uploads project files (qgz/gpkg/mbtiles) and triggers packaging.
"""
import os
import sys
import argparse
from pathlib import Path
from typing import Optional

from qfieldcloud_sdk.sdk import Client, FileTransferType, QfcRequestException


def newest_dev_zip(dist_dir: Path) -> Optional[Path]:
    zips = sorted(dist_dir.glob("qfield_project_dev_*.zip"), key=lambda p: p.stat().st_mtime, reverse=True)
    return zips[0] if zips else None


def ensure_auth(c: Client) -> None:
    user = os.getenv("QFIELDCLOUD_USERNAME")
    pwd = os.getenv("QFIELDCLOUD_PASSWORD")
    if not (user and pwd):
        print("ERROR: Set QFIELDCLOUD_USERNAME and QFIELDCLOUD_PASSWORD")
        sys.exit(1)
    c.login(user, pwd)


def create_or_get_project(c: Client, name: str) -> str:
    user = os.getenv("QFIELDCLOUD_USERNAME")
    for p in c.list_projects():
        if p.get("name") == name and p.get("owner") == user:
            return p.get("id")
    proj = c.create_project(name)
    return proj.get("id") or proj.get("slug") or name


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", default="field-wells-dev")
    ap.add_argument("--zip", default=None)
    args = ap.parse_args()

    dist_dir = Path("dist")
    if args.zip:
        zip_path = Path(args.zip)
    else:
        zip_path = newest_dev_zip(dist_dir)
    if not zip_path or not zip_path.exists():
        print("ERROR: Package zip not found. Build/Package first.")
        sys.exit(1)

    base_url = os.getenv("QFIELDCLOUD_BASE_URL", "https://app.qfield.cloud/api/v1/")
    c = Client(base_url)
    ensure_auth(c)
    project_id = create_or_get_project(c, args.name)

    # Upload essential files
    uploads = []
    from pathlib import Path as P
    files = [
        (P("qgis/wells_project_dev.qgz"), P("wells_project_dev.qgz")),
        (P("qgis/wells_dev.gpkg"), P("wells_dev.gpkg")),
    ]
    mb_dir = P("qgis/mbtiles")
    mb_filter = os.getenv("MBTILES_FILTER", "*.mbtiles")
    mb_max_mb = float(os.getenv("MBTILES_MAX_MB", "0") or 0)  # 0 = no cap
    if mb_dir.exists():
        import fnmatch
        for p in sorted(mb_dir.glob("*.mbtiles")):
            if not fnmatch.fnmatch(p.name, mb_filter):
                continue
            if mb_max_mb > 0 and p.exists() and (p.stat().st_size / (1024*1024)) > mb_max_mb:
                print(f"Skipping {p.name} (> {mb_max_mb} MB)")
                continue
            files.append((p, P("mbtiles") / p.name))
    for local, remote in files:
        if local.exists():
            print(f"Uploading {local} → {remote}")
            try:
                c.upload_file(project_id, FileTransferType.PROJECT, local, remote, show_progress=False)
                uploads.append(local)
            except QfcRequestException as e:
                # Gracefully skip quota errors or similar per-file failures
                msg = str(e)
                if "over_quota" in msg or "402" in msg:
                    print(f"Skipping due to quota: {remote}")
                    continue
                raise
    print(f"Uploaded {len(uploads)} files to project {project_id}")

    # Trigger packaging so timestamps update and project is downloadable
    print("Triggering packaging…")
    print(c.package_latest(project_id))


if __name__ == "__main__":
    main()
