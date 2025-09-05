# Field Well Survey

Simple offline field data collection for orphan/STFD wells in Oklahoma using QField.

## Quick Start

See GETTING_STARTED.md for full setup. Minimal flow:

```bash
conda env create -f environment.yml && conda activate field-app

# Deploy dev (builds data + project + uploads to QFieldCloud)
python deploy.py --env dev

# Deploy prod
python deploy.py --env prod
```

## What This System Provides

- **Data**: ~22K wells from Oklahoma Corporation Commission (orphan + STFD)
- **Styling**: Triangles (STFD) and circles (Orphan); Gas (blue), Oil (orange), Other (purple)
- **Basemaps**: Satellite (Google XYZ) + OpenStreetMap (online)
- **Mobile Form**: Three edits only: Exists on site, Small leak, Viable for plugging (Yes/No)
- **Offline-First**: Complete workflow works without connectivity

## System Overview

- **Single Command**: `deploy.py` is the supported entrypoint for build + deploy
- **Mobile App**: QField provides offline-capable survey forms with map navigation
- **Data Sync**: QFieldCloud handles team collaboration and data preservation
- **Field Guide**: `docs/field_guide.md` - Complete mobile workflow for field workers
