import ezdxf
import geopandas as gpd
from shapely.geometry import Polygon
import os

# Créer le dossier 'data' s'il n'existe pas
os.makedirs("data", exist_ok=True)

# Charger le fichier DXF
dxf_path = "data/parcelles_nice.dxf"  # Remplacez par le nom de votre fichier DXF
doc = ezdxf.readfile(dxf_path)
msp = doc.modelspace()

# Extraire les parcelles (entités de type LWPOLYLINE ou POLYLINE)
polygons = []
for entity in msp:
    if entity.dxftype() in ["LWPOLYLINE", "POLYLINE"]:
        try:
            points = [(p[0], p[1]) for p in entity.vertices()]
            polygons.append(Polygon(points))
        except:
            continue  # Ignorer les entités non valides

# Créer un GeoDataFrame
gdf = gpd.GeoDataFrame(geometry=polygons, crs="EPSG:3942")  # Système de coordonnées du DXF
gdf = gdf.to_crs("EPSG:4326")  # Conversion en WGS84 (lat/lon)

# Sauvegarder en GeoJSON
output_path = "data/parcelles_06088.geojson"
gdf.to_file(output_path, driver="GeoJSON")
print(f"✅ Fichier GeoJSON créé : {output_path}")
