import os
import geopandas as gpd
import streamlit as st
from streamlit_folium import folium_static
import folium

# Chemin absolu vers le fichier GeoJSON
file_path = os.path.join(os.getcwd(), "data", "parcelles.geojson")

# Charger les données
if os.path.exists(file_path):
    data = gpd.read_file(file_path)
    st.success(f"✅ Données chargées depuis {file_path}")
else:
    st.warning(f"⚠️ Fichier introuvable : {file_path}. Utilisation de données fictives.")
    from shapely.geometry import Polygon
    data = gpd.GeoDataFrame(
        geometry=[
            Polygon([(7.26, 43.70), (7.27, 43.70), (7.27, 43.71), (7.26, 43.71)]),
            Polygon([(7.25, 43.70), (7.26, 43.70), (7.26, 43.71), (7.25, 43.71)])
        ],
        crs="EPSG:4326"
    )

# Afficher la carte
m = folium.Map(location=[43.7034, 7.2663], zoom_start=13)
folium.GeoJson(data).add_to(m)
folium_static(m)

# Afficher les données
st.write(f"Nombre de parcelles : {len(data)}")
st.dataframe(data)
