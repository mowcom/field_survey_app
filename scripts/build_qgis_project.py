#!/usr/bin/env python3

import os
import sys
import argparse

QGIS_RES = "/Applications/QGIS.app/Contents/Resources"
os.environ.setdefault("PROJ_LIB", os.path.join(QGIS_RES, "proj"))
os.environ.setdefault("GDAL_DATA", os.path.join(QGIS_RES, "gdal"))

from qgis.core import (
    QgsApplication, QgsProject, QgsVectorLayer, QgsRasterLayer,
    QgsCategorizedSymbolRenderer, QgsRendererCategory, QgsSymbol,
    QgsMarkerSymbol, QgsEditorWidgetSetup, QgsProperty, QgsDefaultValue,
    QgsLayerTreeGroup, QgsCoordinateReferenceSystem, QgsReferencedRectangle,
    QgsAction, QgsActionManager, QgsRectangle, QgsFieldConstraints,
    QgsAttributeEditorContainer, QgsAttributeEditorField, QgsEditFormConfig
)
from PyQt5.QtGui import QColor

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
QGIS_DIR = os.path.join(PROJECT_ROOT, "qgis")
GPKG_QGIS_PATH = os.path.join(QGIS_DIR, "wells.gpkg")
DEV_GPKG_QGIS_PATH = os.path.join(QGIS_DIR, "wells_dev.gpkg")
DATA_DIR = os.path.join(PROJECT_ROOT, "data", "processed")
GPKG_DATA_PATH = os.path.join(DATA_DIR, "wells.gpkg")
DEV_GPKG_DATA_PATH = os.path.join(DATA_DIR, "wells_dev.gpkg")
LAYER_NAME = "wells"
OUT_QGZ = os.path.join(QGIS_DIR, "wells_project.qgz")
OUT_QGZ_DEV = os.path.join(QGIS_DIR, "wells_project_dev.qgz")
MBTILES_DIR = os.path.join(QGIS_DIR, "mbtiles")

# Consistent color scheme - same colors for Gas/Oil/Other across both shapes
COLORS = {
    "GAS": QColor("#2196F3"),    # Blue for Gas
    "OIL": QColor("#FF9800"),    # Orange for Oil  
    "OTHER": QColor("#9C27B0")   # Purple for Other
}

# Single size for all points
POINT_SIZE = "2.6"


def build_renderer(layer: QgsVectorLayer) -> QgsCategorizedSymbolRenderer:
    """Build categorized renderer with shape differentiation: circles for orphan, pins for STFD"""
    categories = []
    
    # Create categories for all combinations
    for well_type in ("GAS", "OIL", "OTHER"):
        for source in ("STFD", "ORPHAN"):
            color = COLORS.get(well_type, QColor("#666666"))  # Use consistent color by well type
            
            # Shape differentiation: pins for STFD, circles for orphan
            if source == "STFD":
                shape_name = "triangle"  # Triangle/pin shape for STFD (more distinctive)
            else:
                shape_name = "circle"  # Circle for orphan
            
            symbol = QgsMarkerSymbol.createSimple({
                'name': shape_name,
                'color': color.name(),
                'outline_color': '#000000',
                'outline_width': '0.4',
                'size': POINT_SIZE
            })
            
            # Category value should match the expression we'll use
            category_value = f"{well_type}_{source}"
            label = f"{well_type} ({source})"
            categories.append(QgsRendererCategory(category_value, symbol, label))
    
    # Use expression to concatenate well_type and source_list
    expression = "concat(\"well_type\", '_', \"source_list\")"
    return QgsCategorizedSymbolRenderer(expression, categories)


def apply_value_maps(layer: QgsVectorLayer) -> None:
    """Configure simple Yes/No widgets and hide non-editable fields"""
    fields = layer.fields()

    def set_value_map(field_name: str, mapping):
        idx = fields.indexOf(field_name)
        if idx == -1:
            return
        cfg = {"map": [{"value": v, "label": label} for v, label in mapping], "style": "radio"}
        layer.setEditorWidgetSetup(idx, QgsEditorWidgetSetup("ValueMap", cfg))

    def set_read_only(field_name: str):
        idx = fields.indexOf(field_name)
        if idx != -1:
            layer.setEditorWidgetSetup(idx, QgsEditorWidgetSetup("TextEdit", {"IsReadOnly": True}))

    def set_hidden(field_name: str):
        idx = fields.indexOf(field_name)
        if idx != -1:
            layer.setEditorWidgetSetup(idx, QgsEditorWidgetSetup("Hidden", {}))

    # Editable survey fields: Yes/No only
    yn = [(0, "No"), (1, "Yes")]
    set_value_map("exists", yn)
    set_value_map("small_leak", yn)
    set_value_map("viable_leak", yn)

    # Hide 'found' (kept for compatibility but not used)
    set_hidden("found")

    # System fields read-only
    for f in ("visited", "visited_at_utc", "last_edit_utc"):
        set_read_only(f)

    # Context (keep read-only; QField form can still show basic ID info)
    for f in ("well_id", "source_list", "well_name", "operator_name"):
        set_read_only(f)

    # Ensure no default expressions for audit fields (triggers manage them)
    print("✅ Widgets: exists/small_leak/viable_leak as Yes/No; others hidden/read-only")


def configure_survey_form(layer: QgsVectorLayer) -> None:
    """Configure clean mobile survey form with only essential fields"""
    fields = layer.fields()
    
    # Configure form widgets for mobile survey
    def set_value_map(field_name: str, mapping):
        idx = fields.indexOf(field_name)
        if idx == -1:
            return
        cfg = {
            "map": [{"value": v, "label": label} for v, label in mapping],
            "style": "radio"
        }
        layer.setEditorWidgetSetup(idx, QgsEditorWidgetSetup("ValueMap", cfg))
    
    def set_read_only(field_name: str):
        idx = fields.indexOf(field_name)
        if idx != -1:
            layer.setEditorWidgetSetup(idx, QgsEditorWidgetSetup("TextEdit", {"IsReadOnly": True}))

    def set_hidden(field_name: str):
        idx = fields.indexOf(field_name)
        if idx != -1:
            layer.setEditorWidgetSetup(idx, QgsEditorWidgetSetup("Hidden", {}))
    
    # Main survey fields with big mobile buttons
    ynu = [(-1, "Unknown"), (0, "No"), (1, "Yes")]
    set_value_map("found", ynu)
    set_value_map("well_exists", ynu)
    set_value_map("small_leak", [(0, "No"), (1, "Yes")])
    set_value_map("viable_leak", [(0, "No"), (1, "Yes")])
    
    # Auto-populated fields
    surveyor_idx = fields.indexOf("surveyor_name")
    if surveyor_idx != -1:
        layer.setDefaultValueDefinition(surveyor_idx, QgsDefaultValue("@user_full_name", True))
        set_read_only("surveyor_name")
        
    date_idx = fields.indexOf("survey_date")
    if date_idx != -1:
        layer.setDefaultValueDefinition(date_idx, QgsDefaultValue("now()", True))
        set_read_only("survey_date")
        
    location_idx = fields.indexOf("survey_location")
    if location_idx != -1:
        layer.setDefaultValueDefinition(location_idx, QgsDefaultValue("geom_to_wkt($geometry)", True))
        set_read_only("survey_location")
    
    # Hide technical fields
    set_hidden("survey_id")
    
    # Use simple generated layout for reliability
    form_config = layer.editFormConfig()
    form_config.setLayout(QgsEditFormConfig.GeneratedLayout)
    layer.setEditFormConfig(form_config)
    
    print("✅ Clean mobile survey form configured")


def configure_mobile_survey_form(layer: QgsVectorLayer) -> None:
    """Ultra-simple form: only the three editable fields visible"""
    fields = layer.fields()
    form_config = layer.editFormConfig()
    form_config.setLayout(QgsEditFormConfig.GeneratedLayout)

    # Apply widgets and suppression
    apply_value_maps(layer)

    # Order: exists, small_leak, viable_leak
    try:
        from qgis.core import QgsAttributeEditorContainer, QgsAttributeEditorField
        root = QgsAttributeEditorContainer("Survey", None)
        for fname in ("exists", "small_leak", "viable_leak"):
            idx = fields.indexOf(fname)
            if idx != -1:
                root.addChildElement(QgsAttributeEditorField(fname, idx, root))
        form_config.setInvisibleRootContainer(root)
    except Exception:
        # Fallback: rely on generated layout
        pass

    layer.setEditFormConfig(form_config)
    print("✅ Form suppression applied: only exists / small_leak / viable_leak shown")


def configure_simple_well_form(layer: QgsVectorLayer) -> None:
    """Configure simple read-only form for well information"""
    fields = layer.fields()
    
    def set_read_only(field_name: str):
        idx = fields.indexOf(field_name)
        if idx != -1:
            layer.setEditorWidgetSetup(idx, QgsEditorWidgetSetup("TextEdit", {"IsReadOnly": True}))

    # Make all well fields read-only (context info only)
    for i in range(fields.count()):
        field_name = fields.at(i).name()
        set_read_only(field_name)
    
    # Use simple generated layout
    form_config = layer.editFormConfig()
    form_config.setLayout(QgsEditFormConfig.GeneratedLayout)
    layer.setEditFormConfig(form_config)
    
    print("✅ Simple read-only well form configured")


def configure_form_layout(layer: QgsVectorLayer) -> None:
    """Configure drag-and-drop form layout with groups for mobile workflow"""
    fields = layer.fields()
    form_config = layer.editFormConfig()
    
    # Use drag-and-drop layout for custom grouping
    form_config.setLayout(QgsEditFormConfig.TabLayout)
    
    # Create root container
    root_container = QgsAttributeEditorContainer("Survey Form", None)
    
    # Header Group (read-only context info)
    header_group = QgsAttributeEditorContainer("Well Information", root_container)
    header_group.setCollapsed(False)
    
    header_fields = ["well_id", "source_list", "well_name", "operator_name"]
    for field_name in header_fields:
        idx = fields.indexOf(field_name)
        if idx != -1:
            field_element = QgsAttributeEditorField(field_name, idx, header_group)
            header_group.addChildElement(field_element)
    
    # Survey Status Group (main data entry - big buttons)
    status_group = QgsAttributeEditorContainer("Survey Status", root_container)
    status_group.setCollapsed(False)
    
    # Order fields for logical workflow
    status_fields = ["found", "exists", "small_leak", "viable_leak"]
    for field_name in status_fields:
        idx = fields.indexOf(field_name)
        if idx != -1:
            field_element = QgsAttributeEditorField(field_name, idx, status_group)
            status_group.addChildElement(field_element)
    
    # System Group (collapsed by default)
    system_group = QgsAttributeEditorContainer("System Information", root_container)
    system_group.setCollapsed(True)
    
    system_fields = ["visited", "editor_name", "visited_at_utc", "last_edit_utc"]
    for field_name in system_fields:
        idx = fields.indexOf(field_name)
        if idx != -1:
            field_element = QgsAttributeEditorField(field_name, idx, system_group)
            system_group.addChildElement(field_element)
    
    # Add groups to root container
    root_container.addChildElement(header_group)
    root_container.addChildElement(status_group)
    root_container.addChildElement(system_group)
    
    # Set form configuration - try different approaches for compatibility
    try:
        # Try modern API first
        form_config.setInvisibleRootContainer(root_container)
    except AttributeError:
        # Fallback - set layout with simplified approach
        form_config.setLayout(QgsEditFormConfig.GeneratedLayout)
    
    layer.setEditFormConfig(form_config)
    
    print("✅ Drag-and-drop form layout configured with groups")


def add_actions(layer: QgsVectorLayer) -> None:
    mgr: QgsActionManager = layer.actions()
    for act in list(mgr.actions()):
        if act.name() in ("Open in Google Maps", "Share via WhatsApp", "Open in Apple Maps", "My Location"):
            mgr.removeAction(act)
    mgr.addAction(QgsAction.OpenUrl, "Open in Google Maps",
                  "concat('https://www.google.com/maps/dir/?api=1&destination=', y(transform($geometry, layer_property(@layer,'crs'), 'EPSG:4326')), ',', x(transform($geometry, layer_property(@layer,'crs'), 'EPSG:4326')))", None, False)
    mgr.addAction(QgsAction.OpenUrl, "Share via WhatsApp",
                  "concat('https://wa.me/?text=', url_encode(concat('Well ', \"well_id\", ' — https://maps.google.com/?q=', y(transform($geometry, layer_property(@layer,'crs'), 'EPSG:4326')), ',', x(transform($geometry, layer_property(@layer,'crs'), 'EPSG:4326')))))", None, False)
    mgr.addAction(QgsAction.OpenUrl, "Open in Apple Maps",
                  "concat('http://maps.apple.com/?daddr=', y(transform($geometry, layer_property(@layer,'crs'), 'EPSG:4326')), ',', x(transform($geometry, layer_property(@layer,'crs'), 'EPSG:4326')))", None, False)
    # Optional quick access to user's current location in Maps
    mgr.addAction(QgsAction.OpenUrl, "My Location",
                  "'https://www.google.com/maps/search/?api=1&query=My+Location'", None, False)


def add_basemap_layers(proj: QgsProject) -> None:
    """Add simple, standard basemap layers that work reliably in QField"""
    
    # Satellite basemap: Simplified Google Satellite (bottom layer)
    satellite_uri = "type=xyz&url=https://mt1.google.com/vt/lyrs%3Ds%26x%3D{x}%26y%3D{y}%26z%3D{z}&zmax=19&zmin=0&http-header:User-Agent=QField"
    satellite_layer = QgsRasterLayer(satellite_uri, "Satellite", "wms") 
    if satellite_layer.isValid():
        proj.addMapLayer(satellite_layer, False)
        print("✅ Added Satellite basemap")
    else:
        print("❌ Failed to add Satellite basemap")
        
    # OpenStreetMap basemap (alternative)
    osm_uri = "type=xyz&url=https://tile.openstreetmap.org/{z}/{x}/{y}.png&zmax=19&zmin=0&http-header:User-Agent=QField"
    osm_layer = QgsRasterLayer(osm_uri, "OpenStreetMap", "wms")
    if osm_layer.isValid():
        proj.addMapLayer(osm_layer, False)
        print("✅ Added OpenStreetMap basemap")
    else:
        print("❌ Failed to add OpenStreetMap basemap")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--env", choices=["dev","prod"], default="prod")
    args = parser.parse_args()

    qgs = QgsApplication([], False)
    QgsApplication.setPrefixPath("/Applications/QGIS.app/Contents/MacOS", True)
    qgs.initQgis()

    proj = QgsProject.instance()

    gpkg = GPKG_QGIS_PATH if args.env == "prod" else DEV_GPKG_QGIS_PATH
    if not os.path.exists(gpkg):
        gpkg = GPKG_DATA_PATH if args.env == "prod" else DEV_GPKG_DATA_PATH
    out_qgz = OUT_QGZ if args.env == "prod" else OUT_QGZ_DEV

    uri = f"{gpkg}|layername={LAYER_NAME}"
    if not os.path.exists(gpkg):
        raise RuntimeError(f"Missing GeoPackage: {gpkg}")

    wells = QgsVectorLayer(uri, "Wells", "ogr")
    if not wells.isValid():
        raise RuntimeError("Failed to load wells layer from GeoPackage")

    # Configure layer for editing in QField
    wells.startEditing()
    wells.commitChanges()
    
    # Enable editing capabilities  
    capabilities = wells.dataProvider().capabilities()
    print(f"Layer capabilities: {capabilities}")
    
    # Set simple categorized renderer for all wells
    wells.setRenderer(build_renderer(wells))
    
    # No labels - keep it simple
    wells.setLabelsEnabled(False)

    # Add basemaps FIRST (so they render at bottom)
    add_basemap_layers(proj)
    
    # Configure wells layer with mobile survey form
    configure_mobile_survey_form(wells)
    add_actions(wells)

    # Add wells layer to project (will render above basemaps)
    proj.addMapLayer(wells, False)
    
    # Create filtered layer view for "Not Surveyed" wells
    not_surveyed_uri = f'{gpkg}|layername={LAYER_NAME}|subset="visited" = 0'
    not_surveyed_layer = QgsVectorLayer(not_surveyed_uri, "Not Surveyed", "ogr")
    if not_surveyed_layer.isValid():
        not_surveyed_layer.setRenderer(build_renderer(not_surveyed_layer))
        configure_mobile_survey_form(not_surveyed_layer)
        add_actions(not_surveyed_layer)
        proj.addMapLayer(not_surveyed_layer, False)
        print("✅ Added 'Not Surveyed' filtered layer")
    
    # Organize layers in simple tree structure
    root = proj.layerTreeRoot()
    
    # Add wells layer (primary, visible) - will be on top in render order
    if not_surveyed_layer.isValid():
        not_surveyed_tree = root.addLayer(not_surveyed_layer)
        not_surveyed_tree.setItemVisibilityChecked(True)
        print("✅ 'Not Surveyed' layer set to visible")
    
    # Add all wells layer for reference (hidden by default)
    all_wells_tree = root.addLayer(wells)
    all_wells_tree.setItemVisibilityChecked(False)
    print("✅ 'Wells' layer added (hidden by default)")
    
    # Add basemap layers to tree (will render at bottom)
    for layer in proj.mapLayers().values():
        if layer.name() in ["Satellite", "OpenStreetMap"]:
            basemap_tree = root.addLayer(layer)
            # Set satellite visible by default, OSM hidden
            if layer.name() == "Satellite":
                basemap_tree.setItemVisibilityChecked(True)
                print("✅ Satellite layer set to visible")
            else:
                basemap_tree.setItemVisibilityChecked(False)
                print("✅ OpenStreetMap layer set to hidden")
    
    # Keep only Not Surveyed and basemaps visible by default
    if not_surveyed_layer.isValid():
        all_wells_tree.setItemVisibilityChecked(False)
        print("✅ Only 'Not Surveyed' visible by default")

    # Set initial extent to Oklahoma
    oklahoma_extent = QgsRectangle(-103.002, 33.615, -94.430, 37.002)  # Oklahoma bbox
    oklahoma_ref_extent = QgsReferencedRectangle(oklahoma_extent, QgsCoordinateReferenceSystem("EPSG:4326"))
    proj.viewSettings().setDefaultViewExtent(oklahoma_ref_extent)
    
    # Set project CRS to WGS84 (EPSG:4326) for consistency
    proj.setCrs(QgsCoordinateReferenceSystem("EPSG:4326"))
    
    print("✅ Set initial extent to Oklahoma")

    os.makedirs(QGIS_DIR, exist_ok=True)
    proj.write(out_qgz)
    print(f"Wrote project: {out_qgz}")

    qgs.exitQgis()


if __name__ == "__main__":
    main()
