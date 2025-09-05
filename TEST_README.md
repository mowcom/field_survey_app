# Repository Tests

## Running Tests

```bash
conda activate field-app
python test_repo.py
```

## Test Coverage

The test suite validates:

1. **Environment** - Conda env, GeoPandas, QFieldCloud SDK
2. **Data Files** - CSV files in `data/raw/`
3. **Scripts** - Core scripts exist and are executable
4. **Data Processing** - GeoPackage generation from CSVs
5. **QGIS Project** - Project build using PyQGIS
6. **Deployment Package** - Zip creation for QFieldCloud
7. **Credentials** - QFieldCloud authentication setup

## Test Results

- ✅ **All tests passing** means repository is deployment-ready
- ⚠️ **Credential warnings** are OK if not deploying
- ❌ **Failed tests** indicate setup issues

## Manual Testing

Test individual components:

```bash
# Test data processing
python scripts/prepare_wells_gpkg.py

# Test QGIS project build  
/Applications/QGIS.app/Contents/MacOS/bin/python3 scripts/build_qgis_project.py --env dev

# Test deployment (with credentials)
export QFIELDCLOUD_USERNAME="your_user"
export QFIELDCLOUD_PASSWORD="your_pass"
python deploy.py --env dev
```

## Adding Tests

To add new tests, add functions to `test_repo.py` and include in `run_all_tests()` list.
Note: Tests do not trigger QFieldCloud packaging. On first deploy per project, set the `.qgz` as the Project File in the QFieldCloud UI and click Package once.
