# QGIS Project UI Specification (spec)

Defines forms, filters, actions, and styling for QField use.

## Layers
- Editable source: `wells` (GeoPackage)
- Styled views (filters):
  - `Wells — State Fund`: `"source_list" = 'STFD'`
  - `Wells — Orphan`: `"source_list" = 'ORPHAN'`

## Form layout (Drag-and-Drop)
- Header group (read-only): `well_id`, `source_list`, `well_name`, `operator_name`
- Status group (big buttons):
  - `exists` (Value Map): 0 No, 1 Yes
  - `small_leak` (Value Map): 0 No, 1 Yes
  - `viable_leak` (Value Map): 0 No, 1 Yes
- Optional group (collapsed): `notes`, `crew`, `photo_path` (if later added)

## Widget settings
- Use Value Map (radio/button style on mobile) for the three fields with Yes/No options.
- Disallow NULL where appropriate; defaults remain: found=-1, exists=-1, small_leak=0, viable_leak=0, visited=0 (UI hides `found` and does not expose Unknown).
- Audit fields are managed by SQLite triggers; do not set QGIS default expressions for `last_edit_utc` or visited fields.

## Actions (feature menu)
- Open in Google Maps (directions)
  - Type: Open URL
  - Expression:
    ```
    concat(
      'https://www.google.com/maps/dir/?api=1&destination=',
      y(transform($geometry, layer_property(@layer,'crs'), 'EPSG:4326')), ',',
      x(transform($geometry, layer_property(@layer,'crs'), 'EPSG:4326'))
    )
    ```
- Share via WhatsApp
  - Type: Open URL
  - Expression:
    ```
    concat(
      'https://wa.me/?text=',
      url_encode(
        concat(
          'Well ', "well_id", ' — https://maps.google.com/?q=',
          y(transform($geometry, layer_property(@layer,'crs'), 'EPSG:4326')), ',',
          x(transform($geometry, layer_property(@layer,'crs'), 'EPSG:4326'))
        )
      )
    )
    ```
- Apple Maps (fallback)
  - Type: Open URL
  - Expression:
    ```
    concat(
      'http://maps.apple.com/?daddr=',
      y(transform($geometry, layer_property(@layer,'crs'), 'EPSG:4326')), ',',
      x(transform($geometry, layer_property(@layer,'crs'), 'EPSG:4326'))
    )
    ```

## Symbology
- As per `docs/style_guide.md`:
  - STFD wells: Triangles
  - Orphan wells: Circles
  - Colors by well type: Gas blue `#2196F3`, Oil orange `#FF9800`, Other purple `#9C27B0`
  - Layer order: STFD above Orphan

## Visibility
- Default view shows `Not Visited` (visited = 0) layer; `Wells` (all) is available but hidden by default.
- No scale-dependent rules; no labels.

## Basemaps
- OpenStreetMap (primary) as XYZ
- Satellite (Google XYZ) as secondary

## Filters and presets
- Preset filter: Not Visited → `"visited" = 0`
- Optional: STFD only → `"source_list" = 'STFD'`

## Notes
- Keep symbology simple for performance; avoid heavy expressions.
- Keep status fields at the top of the form to enable 3-tap workflow.
