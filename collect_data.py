import geopandas as gpd
import argparse
import requests
import os
from urllib.parse import urljoin

def download_parcelles(code_insee="06004", output_file="parcelles.geojson"):
    """
    Télécharge les parcelles cadastrales d'une commune depuis le Géoportail.
    Args:
        code_insee (str): Code INSEE de la commune (ex: "06004" pour Antibes).
        output_file (str): Chemin du fichier de sortie (ex: "parcelles.geojson").
    """
    base_url = f"https://cadastre.data.gouv.fr/data/etalab-cadastre/latest/geojson/communes/{code_insee}/"
    parcelles_url = urljoin(base_url, "parcelles.json")

    try:
        # Vérifier si l'URL est accessible
        response = requests.head(parcelles_url)
        if response.status_code != 200:
            print(f"❌ Erreur: Impossible de trouver les données pour le code INSEE {code_insee}.")
            print(f"Vérifiez le code INSEE ou consultez https://cadastre.data.gouv.fr/")
            return None

        # Télécharger et sauvegarder les parcelles
        gdf = gpd.read_file(parcelles_url)
        gdf.to_file(output_file, driver="GeoJSON")
        print(f"✅ Parcelles sauvegardées dans {output_file} (nombre: {len(gdf)})")
        return gdf
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Télécharger les parcelles cadastrales.")
    parser.add_argument("--code_insee", default="06004", help="Code INSEE de la commune (ex: 06004 pour Antibes).")
    parser.add_argument("--output", default="parcelles.geojson", help="Fichier de sortie.")
    args = parser.parse_args()

    download_parcelles(args.code_insee, args.output)
