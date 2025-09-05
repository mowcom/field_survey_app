#!/usr/bin/env python3
"""
Modern QFieldCloud uploader (qfieldcloud_sdk).

Env vars:
  - QFIELDCLOUD_PROJECT_ID (UUID or project name)
  - Auth: QFIELDCLOUD_USERNAME + QFIELDCLOUD_PASSWORD
  - QFIELDCLOUD_BASE_URL (default: https://app.qfield.cloud/api/v1/)

Usage:
  python tools/upload_qfc.py dist/qfield_project_dev_*.zip
This extracts the zip and uploads all files to the project, then triggers packaging.
"""
import os
import sys
from pathlib import Path
import re
import tempfile
import zipfile

from qfieldcloud_sdk.sdk import Client, FileTransferType

if len(sys.argv) < 2:
    print("Usage: python tools/upload_qfc.py <package.zip>")
    sys.exit(1)

zip_path = Path(sys.argv[1]).resolve()
if not zip_path.exists():
    print("ERROR: File not found:", zip_path)
    sys.exit(1)

base_url = os.getenv("QFIELDCLOUD_BASE_URL", "https://app.qfield.cloud/api/v1/")
project_id = os.getenv("QFIELDCLOUD_PROJECT_ID")
username = os.getenv("QFIELDCLOUD_USERNAME")
password = os.getenv("QFIELDCLOUD_PASSWORD")

if not project_id:
    print("ERROR: QFIELDCLOUD_PROJECT_ID not set")
    sys.exit(1)

c = Client(base_url)
if username and password:
    c.login(username, password)
else:
    print("ERROR: Provide QFIELDCLOUD_USERNAME and QFIELDCLOUD_PASSWORD")
    sys.exit(1)

# Resolve project id if a name was provided
UUID_RE = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")
if not UUID_RE.match(project_id):
    pid = None
    for p in c.list_projects():
        if p.get("name") == project_id and p.get("owner") == username:
            pid = p.get("id")
            break
    if not pid:
        print(f"ERROR: Could not resolve project name '{project_id}' to an id.")
        sys.exit(1)
    project_id = pid

print(f"Extracting and uploading package to project: {project_id}")
with tempfile.TemporaryDirectory() as td:
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(td)
    # Upload all files recursively from extracted root
    c.upload_files(project_id, FileTransferType.PROJECT, td, "**/*", throw_on_error=True, show_progress=False)

print("Triggering packaging…")
print(c.package_latest(project_id))
print("Upload and packaging complete.")
