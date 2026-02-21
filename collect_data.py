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
    url = f"https://cadastre.data.gouv.fr/data/etalab-cadastre/latest/geojson/communes/{code_insee}/parcelles.json"

    try:
        # Vérifier si l'URL est accessible
        response = requests.head(url)
        if response.status_code != 200:
            print(f"❌ Erreur: Impossible de trouver les données pour le code INSEE {code_insee}.")
            print(f"Vérifiez le code INSEE sur https://cadastre.data.gouv.fr/")
            return None

        # Télécharger et sauvegarder les parcelles
        gdf = gpd.read_file(url)
        gdf.to_file(output_file, driver="GeoJSON")
        print(f"✅ Parcelles sauvegardées dans {output_file} (nombre: {len(gdf)})")
        return gdf
    except Exception as e:
        print(f"❌ Erreur pour {code_insee}: {e}")
        return None

def download_multiple_parcelles(codes_insee, output_dir="data"):
    """Télécharge les parcelles pour plusieurs communes."""
    for code in codes_insee:
        print(f"Téléchargement des parcelles pour {code}...")
        download_parcelles(code, output_dir)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Télécharger les parcelles cadastrales.")
    parser.add_argument("--code_insee", default="06088", help="Code INSEE de la commune (ex: 06088 pour Nice).")
    parser.add_argument("--output_dir", default="data", help="Dossier de sortie.")
    parser.add_argument("--multiple", nargs='+', help="Liste de codes INSEE (ex: 06004 06088 06029).")
    args = parser.parse_args()

    if args.multiple:
        download_multiple_parcelles(args.multiple, args.output_dir)
    else:
        download_parcelles(args.code_insee, args.output_dir)
