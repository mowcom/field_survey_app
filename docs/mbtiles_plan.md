# Offline MBTiles Plan (Oklahoma)

Goal: Provide offline Streets + Satellite basemaps on iPad/iPhone.

## Streets (Open data)
- Option A: OpenMapTiles (vector MBTiles)
  - Download Oklahoma extract (if available) or generate with OpenMapTiles tools.
  - Pros: small, scalable; Cons: needs a style JSON in a compatible viewer (QGIS renders vector tiles directly).
- Option B: OSM raster MBTiles
  - Use a prebuilt OSM raster MBTiles for OK area or render from a trusted source.

## Satellite (NAIP imagery)
- Source: USDA NAIP (public domain) for Oklahoma.
- Prepare GeoTIFFs for AOIs, then convert to MBTiles.

## Example commands (raster → MBTiles)
```bash
# Convert GeoTIFF to MBTiles
gdal_translate -of MBTILES input.tif ok_sat.mbtiles
# Build overviews (zooms)
gdaladdo -r bilinear ok_sat.mbtiles 2 4 8 16
```

## Zoom strategy
- Streets: z5–z17 for statewide; consider tiling by region if file too large.
- Satellite: z8–z17 for AOIs; split by region to keep each file < ~500 MB.

## Packaging
- Store MBTiles in `qgis/mbtiles/` and mark as "Copy" in QField Sync.
- Reference them in the project so QField downloads alongside the GeoPackage.

## Notes
- Respect licensing: NAIP is public domain; avoid scraping commercial tiles.
- Test on device for performance/size balance.
