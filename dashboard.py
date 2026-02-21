import streamlit as st
import folium
from streamlit_folium import folium_static
import geopandas as gpd
import pandas as pd

st.title("🗺️ Détection de Parcelles Abandonnées")

# Charger les données (exemple avec données fictives si aucun fichier n'existe)
try:
    gdf = gpd.read_file("parcelles.geojson")
    data = pd.DataFrame(gdf.drop(columns="geometry"))
    data["lat"] = gdf.centroid.y
    data["lon"] = gdf.centroid.x
except:
    st.warning("⚠️ Aucun fichier 'parcelles.geojson' trouvé. Utilisation de données fictives.")
    data = pd.DataFrame({
        "id": ["1", "2", "3"],
        "lat": [43.58, 43.59, 43.60],
        "lon": [7.12, 7.13, 7.14],
        "score_abandon": [80, 30, 60],
        "superficie": [5000, 2000, 10000]
    })

# Créer la carte
m = folium.Map(location=[data["lat"].mean(), data["lon"].mean()], zoom_start=13)
for _, row in data.iterrows():
    folium.CircleMarker(
        location=[row["lat"], row["lon"]],
        radius=row["score_abandon"] / 10,
        color="red" if row["score_abandon"] > 50 else "green",
        fill=True,
        popup=f"ID: {row['id']}<br>Score: {row['score_abandon']}"
    ).add_to(m)

# Afficher la carte et les données
folium_static(m)
st.dataframe(data)

# Filtre par score
score_min = st.slider("Score minimum d'abandon", 0, 100, 30)
filtered_data = data[data["score_abandon"] >= score_min]
st.write(f"Parcelles filtrées ({len(filtered_data)}):")
st.dataframe(filtered_data)
