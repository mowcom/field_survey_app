# Map Styling Guide (QGIS/QField)

Simple, consistent symbology for thousands of wells on iPad/iPhone.

## Layering strategy
- Single `Wells` layer with categorized renderer
- All wells visible by default with shape and color differentiation

## Symbology
- **Shape differentiation**:
  - **STFD wells**: Triangle pins
  - **Orphan wells**: Circles
- **Consistent colors** across both shapes by well type:
  - **Gas**: Blue `#2196F3`
  - **Oil**: Orange `#FF9800` 
  - **Other**: Purple `#9C27B0`
- **Size**: 2.6mm with black outline (0.4 width)

## Categories
- Gas (STFD) - Blue triangle
- Oil (STFD) - Orange triangle  
- Other (STFD) - Purple triangle
- Gas (ORPHAN) - Blue circle
- Oil (ORPHAN) - Orange circle
- Other (ORPHAN) - Purple circle

- ## Visibility
- Default view shows only `Not Visited` (visited = 0)
- `Wells` (all) is available but hidden by default
- No scale-dependent visibility; no labels

## Basemaps
- OpenStreetMap (primary)
- Satellite (Google XYZ) as secondary
- Both included; Satellite visible by default

## Default view
- Initial extent: Oklahoma bounding box
- CRS: WGS84 (EPSG:4326)

## Performance
- Simple symbols optimized for mobile
- Minimal expressions for fast rendering
- Consistent size across all categories

## Form context
- Header shows: `well_id` (API), `source_list`, `well_name`, `operator_name`
