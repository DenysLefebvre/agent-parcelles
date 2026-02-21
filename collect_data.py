import geopandas as gpd
import argparse

def download_parcelles(code_insee="06004", output_file="parcelles.geojson"):
    """
    Télécharge les parcelles cadastrales d'une commune depuis Géoportail.
    Args:
        code_insee (str): Code INSEE de la commune (ex: "06004" pour Antibes).
        output_file (str): Chemin du fichier de sortie (ex: "parcelles.geojson").
    """
    url = f"https://cadastre.data.gouv.fr/data/etalab-cadastre/latest/geojson/communes/{code_insee}/parcelles.json"
    try:
        gdf = gpd.read_file(url)
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
