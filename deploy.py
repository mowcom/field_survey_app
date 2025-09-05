#!/usr/bin/env python3
"""
Simple QFieldCloud deployment script for field-app

Prerequisites:
- conda activate field-app
- Environment variables: QFIELDCLOUD_USERNAME, QFIELDCLOUD_PASSWORD

Usage:
    python deploy.py --env dev     # Deploy to dev project  
    python deploy.py --env prod    # Deploy to prod project
"""

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime
from zipfile import ZipFile, ZIP_DEFLATED

from qfieldcloud_sdk.sdk import Client, FileTransferType


def ensure_conda_env():
    """Check that we're in the field-app conda environment"""
    conda_env = os.environ.get('CONDA_DEFAULT_ENV')
    if conda_env != 'field-app':
        print("ERROR: Must be in conda environment 'field-app'")
        print("Run: conda activate field-app")
        sys.exit(1)


def build_data_and_project(env: str):
    """Build the GeoPackage and QGIS project"""
    print(f"Building data and project for {env}...")
    
    # Build GeoPackage from CSVs
    os.system("python scripts/prepare_wells_gpkg.py")
    
    # Build QGIS project using QGIS Python
    qgis_python = "/Applications/QGIS.app/Contents/MacOS/bin/python3"
    if env == "dev":
        os.system("cp -f data/processed/wells.gpkg qgis/wells_dev.gpkg")
        os.system(f"{qgis_python} scripts/build_qgis_project.py --env dev")
    else:
        os.system("cp -f data/processed/wells.gpkg qgis/wells.gpkg") 
        os.system(f"{qgis_python} scripts/build_qgis_project.py --env prod")


def create_package(env: str) -> Path:
    """Create deployment package"""
    print(f"Creating package for {env}...")
    
    # Set up file paths
    if env == "dev":
        proj_file = Path("qgis/wells_project_dev.qgz")
        gpkg_file = Path("qgis/wells_dev.gpkg")
        project_name = "field-wells-dev"
    else:
        proj_file = Path("qgis/wells_project.qgz")
        gpkg_file = Path("qgis/wells.gpkg")
        project_name = "field-wells-prod"
    
    # Verify files exist
    for f in [proj_file, gpkg_file]:
        if not f.exists():
            print(f"ERROR: Missing file {f}")
            sys.exit(1)
    
    # Create package zip
    dist_dir = Path("dist")
    dist_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    zip_path = dist_dir / f"qfield_project_{env}_{timestamp}.zip"
    
    with ZipFile(zip_path, "w", compression=ZIP_DEFLATED) as z:
        z.write(proj_file, f"qgis/{proj_file.name}")
        z.write(gpkg_file, f"qgis/{gpkg_file.name}")
    
    print(f"Created package: {zip_path}")
    return zip_path, project_name


def deploy_to_qfieldcloud(zip_path: Path, project_name: str):
    """Deploy package to QFieldCloud"""
    print(f"Deploying to QFieldCloud project: {project_name}")
    
    # Check credentials
    username = os.getenv("QFIELDCLOUD_USERNAME")
    password = os.getenv("QFIELDCLOUD_PASSWORD")
    if not (username and password):
        print("ERROR: Set QFIELDCLOUD_USERNAME and QFIELDCLOUD_PASSWORD environment variables")
        sys.exit(1)
    
    # Connect to QFieldCloud
    client = Client("https://app.qfield.cloud/api/v1/")
    client.login(username, password)
    
    # Get or create project
    project_id = None
    for project in client.list_projects():
        if project.get("name") == project_name and project.get("owner") == username:
            project_id = project.get("id")
            break
    
    if not project_id:
        print(f"Creating new project: {project_name}")
        project = client.create_project(project_name)
        project_id = project.get("id")
    
    print(f"Using project ID: {project_id}")
    
    # Extract and upload files from zip
    import tempfile
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Extract zip
        with ZipFile(zip_path, 'r') as z:
            z.extractall(temp_path)
        
        # Upload project files
        qgis_dir = temp_path / "qgis"
        for file_path in qgis_dir.iterdir():
            if file_path.is_file():
                remote_path = Path(file_path.name)
                print(f"Uploading {file_path.name}...")
                client.upload_file(
                    project_id, 
                    FileTransferType.PROJECT, 
                    file_path, 
                    remote_path,
                    show_progress=False
                )

        # Ensure the server-side Project File is set to our uploaded .qgz/.qgs (first-time init)
        project_file_name = None
        for f in qgis_dir.iterdir():
            if f.suffix.lower() in (".qgz", ".qgs"):
                project_file_name = f.name
                break
        if project_file_name:
            try:
                # 1) List files to find the uploaded project file id
                files = client._request("GET", f"files/?project={project_id}").json()
                file_id = None
                for item in files:
                    if item.get("name") == project_file_name:
                        file_id = item.get("id")
                        break
                # 2) Patch the project to set project_file
                if file_id:
                    client._request("PATCH", f"projects/{project_id}/", json={"project_file": file_id})
                    print(f"✅ Set Project File to: {project_file_name}")
                else:
                    print(f"⚠️  Could not find uploaded project file id for {project_file_name}")
            except Exception as e:
                print(f"⚠️  Could not set Project File via API (will require UI once): {e}")
    
    # Trigger packaging
    print("Triggering project packaging...")
    try:
        client.package_latest(project_id)
    except Exception as e:
        print(f"⚠️  Packaging trigger via latest failed: {e}")
    
    # Bump the "Last changed" timestamp by updating description
    print("Updating project timestamp...")
    try:
        from datetime import datetime, timezone
        current_project = client.get_project(project_id)
        current_desc = current_project.get('description', '') or ''
        
        # Add deployment timestamp to description
        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
        new_desc = f"{current_desc.strip()}\n\nDeployed: {timestamp}".strip()
        
        client.patch_project(project_id, description=new_desc)
        print(f"✅ Project timestamp updated: {timestamp}")
        
    except Exception as e:
        print(f"⚠️  Could not update timestamp: {e}")
    
    print(f"Deployment complete! Project available at: https://app.qfield.cloud/a/{project_name}")


def main():
    parser = argparse.ArgumentParser(description="Deploy field-app to QFieldCloud")
    parser.add_argument("--env", choices=["dev", "prod"], default="dev", 
                       help="Environment to deploy (default: dev)")
    parser.add_argument("--skip-build", action="store_true", 
                       help="Skip data and project build step")
    args = parser.parse_args()
    
    ensure_conda_env()
    
    if not args.skip_build:
        build_data_and_project(args.env)
    
    zip_path, project_name = create_package(args.env)
    deploy_to_qfieldcloud(zip_path, project_name)


if __name__ == "__main__":
    main()
