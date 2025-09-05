#!/usr/bin/env bash
set -euo pipefail

# Convert a single GeoTIFF (or VRT) to MBTiles and build overviews
# Usage: ./scripts/mbtiles_from_geotiff.sh input.tif output.mbtiles

if [[ $# -lt 2 ]]; then
  echo "Usage: $0 <input.tif|.vrt> <output.mbtiles>" >&2
  exit 1
fi

IN="$1"
OUT="$2"

# Create MBTiles
gdal_translate -of MBTILES "$IN" "$OUT"

# Build overviews (zooms)
gdaladdo -r bilinear "$OUT" 2 4 8 16

echo "Wrote $OUT"
