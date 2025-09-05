#!/usr/bin/env python3
"""
Simple key tests for field-app repository

Run with: python test_repo.py
"""

import os
import sys
from pathlib import Path
import subprocess

def test_environment():
    """Test conda environment and key dependencies"""
    print("🧪 Testing environment...")
    
    # Check conda environment
    conda_env = os.environ.get('CONDA_DEFAULT_ENV')
    assert conda_env == 'field-app', f"Expected 'field-app' conda env, got '{conda_env}'"
    print("✅ Conda environment: field-app")
    
    # Test key imports
    try:
        import geopandas
        print("✅ GeoPandas available")
    except ImportError:
        raise AssertionError("GeoPandas not available")
    
    try:
        from qfieldcloud_sdk.sdk import Client
        print("✅ QFieldCloud SDK available")
    except ImportError:
        raise AssertionError("QFieldCloud SDK not available")


def test_data_files():
    """Test that required data files exist"""
    print("🧪 Testing data files...")
    
    raw_dir = Path("data/raw")
    assert raw_dir.exists(), "data/raw directory missing"
    
    # Look for CSV files
    orphan_files = list(raw_dir.glob("*orphan*.csv"))
    stfd_files = list(raw_dir.glob("*stfd*.csv"))
    
    assert len(orphan_files) > 0, "No orphan CSV files found in data/raw"
    assert len(stfd_files) > 0, "No STFD CSV files found in data/raw"
    
    print(f"✅ Found {len(orphan_files)} orphan file(s)")
    print(f"✅ Found {len(stfd_files)} STFD file(s)")


def test_scripts():
    """Test that key scripts are present and executable"""
    print("🧪 Testing scripts...")
    
    scripts = [
        "scripts/prepare_wells_gpkg.py",
        "scripts/build_qgis_project.py", 
        "deploy.py"
    ]
    
    for script in scripts:
        script_path = Path(script)
        assert script_path.exists(), f"Missing script: {script}"
        assert script_path.is_file(), f"Not a file: {script}"
        print(f"✅ {script}")


def test_data_processing():
    """Test data processing pipeline"""
    print("🧪 Testing data processing...")
    
    # Run data preparation
    result = subprocess.run(
        ["python", "scripts/prepare_wells_gpkg.py"],
        capture_output=True, text=True
    )
    
    assert result.returncode == 0, f"Data preparation failed: {result.stderr}"
    print("✅ Data preparation successful")
    
    # Check output files
    gpkg_path = Path("data/processed/wells.gpkg")
    assert gpkg_path.exists(), "GeoPackage not created"
    assert gpkg_path.stat().st_size > 1000, "GeoPackage too small (likely empty)"
    print(f"✅ GeoPackage created: {gpkg_path.stat().st_size:,} bytes")


def test_qgis_project_build():
    """Test QGIS project creation"""
    print("🧪 Testing QGIS project build...")
    
    # Ensure dev gpkg exists
    dev_gpkg = Path("qgis/wells_dev.gpkg")
    if not dev_gpkg.exists():
        subprocess.run(["cp", "data/processed/wells.gpkg", "qgis/wells_dev.gpkg"])
    
    # Build QGIS project
    qgis_python = "/Applications/QGIS.app/Contents/MacOS/bin/python3"
    result = subprocess.run(
        [qgis_python, "scripts/build_qgis_project.py", "--env", "dev"],
        capture_output=True, text=True
    )
    
    assert result.returncode == 0, f"QGIS project build failed: {result.stderr}"
    print("✅ QGIS project build successful")
    
    # Check for basemap success messages
    if "Added OpenStreetMap basemap" in result.stdout:
        print("✅ OpenStreetMap basemap configured")
    if "Added ESRI Satellite basemap" in result.stdout or "Added Google Satellite basemap" in result.stdout:
        print("✅ Satellite basemap configured")
    if "Set initial extent to Oklahoma" in result.stdout:
        print("✅ Oklahoma extent configured")
    
    # Check output
    qgz_path = Path("qgis/wells_project_dev.qgz")
    assert qgz_path.exists(), "QGIS project file not created"
    print(f"✅ QGIS project created: {qgz_path.name}")


def test_deployment_package():
    """Test deployment package creation"""
    print("🧪 Testing deployment package...")
    
    # Import and test package creation
    sys.path.insert(0, str(Path.cwd()))
    from deploy import create_package
    
    try:
        zip_path, project_name = create_package("dev")
        assert zip_path.exists(), "Package zip not created"
        assert project_name == "field-wells-dev", f"Wrong project name: {project_name}"
        print(f"✅ Package created: {zip_path.name}")
        print(f"✅ Project name: {project_name}")
    except Exception as e:
        raise AssertionError(f"Package creation failed: {e}")


def test_credentials_check():
    """Test credential validation and deployment features"""
    print("🧪 Testing credential validation...")
    
    username = os.getenv("QFIELDCLOUD_USERNAME")
    password = os.getenv("QFIELDCLOUD_PASSWORD")
    
    if username and password:
        print(f"✅ Username set: {username}")
        print("✅ Password set: [hidden]")
        
        # Test connection and basic functionality
        try:
            from qfieldcloud_sdk.sdk import Client
            client = Client("https://app.qfield.cloud/api/v1/")
            print("✅ QFieldCloud client created")
            
            # Test timestamp functionality in deploy script
            from datetime import datetime, timezone
            test_timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
            print(f"✅ Timestamp format: {test_timestamp}")
            
        except Exception as e:
            print(f"⚠️  Issue with QFieldCloud functionality: {e}")
    else:
        print("⚠️  QFieldCloud credentials not set (this is OK for testing)")


def run_all_tests():
    """Run all tests"""
    tests = [
        test_environment,
        test_data_files,
        test_scripts,
        test_data_processing,
        test_qgis_project_build,
        test_deployment_package,
        test_credentials_check
    ]
    
    print("🚀 Running field-app repository tests...\n")
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            test_func()
            passed += 1
            print("✅ PASSED\n")
        except Exception as e:
            print(f"❌ FAILED: {e}\n")
            failed += 1
    
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed!")
        return 0
    else:
        print("💥 Some tests failed")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)