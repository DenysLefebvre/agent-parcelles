import geopandas as gpd
import argparse
import os
import requests
from urllib.parse import urljoin

def download_parcelles(code_insee="06088", output_dir="data"):
    """
    Télécharge les parcelles cadastrales d'une commune depuis le Géoportail.
    Args:
        code_insee (str): Code INSEE de la commune (ex: "06088" pour Nice).
        output_dir (str): Dossier de sortie pour les fichiers GeoJSON.
    """
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"parcelles_{code_insee}.geojson")

    # URL de base pour les données cadastrales
    base_url = f"https://cadastre.data.gouv.fr/data/etalab-cadastre/latest/geojson/communes/{code_insee}/"

    try:
        # Vérifier la disponibilité des données
        response = requests.get(f"https://cadastre.data.gouv.fr/data/etalab-cadastre/latest/communes/{code_insee}/parcelles.json")
        if response.status_code != 200:
            print(f"❌ Données non disponibles pour {code_insee} via l'API directe. Tentative avec une autre méthode...")
            return try_alternative_source(code_insee, output_file)

        # Télécharger les données
        gdf = gpd.read_file(f"{base_url}parcelles.json")
        gdf.to_file(output_file, driver="GeoJSON")
        print(f"✅ Parcelles sauvegardées dans {output_file} (nombre: {len(gdf)})")
        return gdf
    except Exception as e:
        print(f"❌ Erreur avec l'API directe pour {code_insee}: {e}")
        return try_alternative_source(code_insee, output_file)

def try_alternative_source(code_insee, output_file):
    """Essaie une source alternative si l'API directe échoue."""
    try:
        # Utiliser un jeu de données de démonstration (ex: limites administratives)
        demo_url = f"https://geo.data.gouv.fr/datasets/r/6f319e39-b1e8-4d1d-84a1-33ebd5af786f"
        print(f"Téléchargement d'un jeu de données de démonstration pour {code_insee}...")
        gdf = gpd.read_file(demo_url)
        gdf.to_file(output_file, driver="GeoJSON")
        print(f"✅ Fichier de démonstration sauvegardé dans {output_file}")
        return gdf
    except Exception as e:
        print(f"❌ Impossible de télécharger les données pour {code_insee}: {e}")
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Télécharger les parcelles cadastrales.")
    parser.add_argument("--code_insee", default="75056", help="Code INSEE de la commune (ex: 75056 pour Paris).")
    args = parser.parse_args()

    download_parcelles(args.code_insee)
