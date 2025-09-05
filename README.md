# Field Well Survey

Simple offline field data collection for orphan/STFD wells in Oklahoma using QField.

## Quick Start

**📖 [See GETTING_STARTED.md for complete setup guide](GETTING_STARTED.md)**

```bash
# Setup environment
conda env create -f environment.yml && conda activate field-app

# Deploy to QFieldCloud (handles data + project + upload)
python deploy.py --env dev
```

## What This System Provides

- **Data**: ~22K wells from Oklahoma Corporation Commission (orphan + STFD)
- **Styling**: Shape differentiation - triangles for STFD, circles for orphan wells
- **Colors**: Blue (gas), orange (oil), purple (other) consistent across shapes
- **Basemaps**: OpenStreetMap + ESRI Satellite for offline field work
- **Mobile Forms**: Touch-friendly survey forms with GPS integration
- **Offline-First**: Complete workflow works without connectivity

## System Overview

- **Single Command**: `deploy.py` handles data processing, project build, and QFieldCloud sync
- **Mobile App**: QField provides offline-capable survey forms with map navigation
- **Data Sync**: QFieldCloud handles team collaboration and data preservation
- **Field Guide**: `docs/field_guide.md` - Complete mobile workflow for field workers
