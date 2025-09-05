#!/usr/bin/env python3
"""
QFieldCloud bump-and-package helper (modern SDK).

Env vars:
  QFIELDCLOUD_USERNAME / QFIELDCLOUD_PASSWORD (required)
  QFIELDCLOUD_BASE_URL (default: https://app.qfield.cloud/api/v1/)

Usage:
  python tools/qfc_bump_and_package.py --name field-wells-dev [--note "Deployed"]
"""
import os
import argparse
from datetime import datetime, timezone
from qfieldcloud_sdk.sdk import Client


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True, help="Project name owned by the current user")
    ap.add_argument("--note", default="Deployed", help="Note prefix to append in description")
    args = ap.parse_args()

    base = os.getenv("QFIELDCLOUD_BASE_URL", "https://app.qfield.cloud/api/v1/")
    user = os.getenv("QFIELDCLOUD_USERNAME")
    pwd = os.getenv("QFIELDCLOUD_PASSWORD")
    if not (user and pwd):
        raise SystemExit("Set QFIELDCLOUD_USERNAME and QFIELDCLOUD_PASSWORD")

    c = Client(base)
    c.login(user, pwd)

    pid = None
    for p in c.list_projects():
        if p.get("name") == args.name and p.get("owner") == user:
            pid = p.get("id")
            break
    if not pid:
        raise SystemExit(f"Project not found for user {user}: {args.name}")

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    proj = c.get_project(pid)
    desc = (proj.get("description") or "").strip()
    if desc:
        desc += "\n"
    desc += f"{args.note} at {stamp}"
    c.patch_project(pid, description=desc)
    print("Description bumped.")

    res = c.package_latest(pid)
    print("Packaging:", res.get("status"))


if __name__ == "__main__":
    main()

