import ezdxf
import geopandas as gpd
from shapely.geometry import Polygon, MultiPolygon
import os

def convert_dxf_to_geojson(dxf_path, output_path):
    try:
        doc = ezdxf.readfile(dxf_path)
        msp = doc.modelspace()

        polygons = []
        for entity in msp:
            if entity.dxftype() == "LWPOLYLINE":
                try:
                    # Extraire les sommets de la polyligne
                    points = list(entity.vertices_in_wcs())
                    if len(points) >= 3:  # Une parcelle doit avoir au moins 3 points
                        # Fermer la polyligne si nécessaire
                        if points[0] != points[-1]:
                            points.append(points[0])
                        polygons.append(Polygon(points))
                except Exception as e:
                    print(f"Erreur sur une entité : {e}")
                    continue

        if not polygons:
            print("⚠️  Aucune parcelle valide trouvée dans le DXF.")
            return False

        # Créer un GeoDataFrame
        gdf = gpd.GeoDataFrame(
            geometry=polygons,
            crs="EPSG:3942"  # RGF93 / CC42 (système utilisé par le cadastre français)
        )

        # Convertir en WGS84 (EPSG:4326) pour une utilisation standard
        gdf = gdf.to_crs("EPSG:4326")

        # Sauvegarder en GeoJSON
        gdf.to_file(output_path, driver="GeoJSON")
        print(f"✅ Fichier GeoJSON créé : {output_path} (nombre de parcelles : {len(gdf)})")
        return True

    except ezdxf.DXFStructureError:
        print("❌ Erreur : Le fichier DXF est corrompu ou dans un format non supporté.")
    except Exception as e:
        print(f"❌ Erreur inattendue : {e}")
    return False

# Chemins des fichiers
dxf_path = "data/parcelles_nice.dxf"
output_path = "data/parcelles_06088.geojson"

# Créer le dossier 'data' s'il n'existe pas
os.makedirs("data", exist_ok=True)

# Exécuter la conversion
if convert_dxf_to_geojson(dxf_path, output_path):
    print("Conversion terminée avec succès !")
else:
    print("La conversion a échoué. Utilisation d'un fichier de démonstration...")
    # Créer un fichier GeoJSON de démonstration
    demo_gdf = gpd.GeoDataFrame(
        geometry=[
            Polygon([(7.26, 43.70), (7.27, 43.70), (7.27, 43.71), (7.26, 43.71)]),
            Polygon([(7.25, 43.70), (7.26, 43.70), (7.26, 43.71), (7.25, 43.71)])
        ],
        crs="EPSG:4326"
    )
    demo_gdf.to_file(output_path, driver="GeoJSON")
    print(f"✅ Fichier GeoJSON de démonstration créé : {output_path}")
