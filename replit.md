# Agent IA de Détection de Parcelles Abandonnées

An AI agent for detecting and analyzing abandoned or under-exploited land parcels in France, using cadastral data and satellite imagery.

## Project Overview

This tool combines French cadastral data (from Géoportail/Etalab) with satellite imagery (Sentinel) to identify abandoned parcels by detecting overgrown vegetation (NDVI) and degraded buildings.

## Tech Stack

- **Language**: Python 3.12
- **UI Framework**: Streamlit (interactive web dashboard)
- **Mapping**: Folium + streamlit-folium
- **GIS**: GeoPandas, Shapely, PyProj
- **Data**: French cadastral API (cadastre.data.gouv.fr)

## Project Structure

- `dashboard.py` — Main Streamlit app (entry point)
- `collect_data.py` — Downloads cadastral parcels by INSEE code
- `convert_dxf_to_geojson.py` — Converts AutoCAD DXF to GeoJSON (EPSG:3942 → EPSG:4326)
- `requirements.txt` — Python dependencies
- `data/` — Stores downloaded GeoJSON files (e.g., `parcelles.geojson`)
- `.streamlit/config.toml` — Streamlit server configuration

## Running the App

The app runs via the "Start application" workflow:
```
streamlit run dashboard.py
```

Streamlit is configured to listen on `0.0.0.0:5000` (see `.streamlit/config.toml`).

## Setup Notes

- All dependencies installed via `pip` from `requirements.txt`
- Streamlit config sets port 5000, host 0.0.0.0, headless mode, CORS disabled for Replit proxy compatibility
- If no `data/parcelles.geojson` exists, the dashboard shows a sample polygon near Nice, France
