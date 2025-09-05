#!/usr/bin/env python3
import os
from qgis.core import QgsApplication, QgsProject, QgsRasterLayer

QGZ = os.path.join(os.path.dirname(os.path.dirname(__file__)), "qgis", "wells_project.qgz")

qgs = QgsApplication([], False)
QgsApplication.setPrefixPath("/Applications/QGIS.app/Contents/MacOS", True)
qgs.initQgis()

proj = QgsProject.instance()
proj.read(QGZ)

osm_uri = "type=xyz&zmin=0&zmax=19&url=https://tile.openstreetmap.org/{z}/{x}/{y}.png"
rl = QgsRasterLayer(osm_uri, "OSM (XYZ)", "wms")
if not rl.isValid():
    rl = QgsRasterLayer(osm_uri, "OSM (XYZ)", "xyz")

if rl.isValid():
    proj.addMapLayer(rl)
    proj.write(QGZ)
    print("Added OSM (XYZ) basemap.")
else:
    print("Failed to add OSM basemap.")

qgs.exitQgis()
