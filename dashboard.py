import streamlit as st
import requests
import folium
from streamlit_folium import st_folium


# =========================
# FONCTIONS DE CHARGEMENT
# =========================


@st.cache_data(show_spinner=False)
def charger_parcelles(code_insee):
    url = f"https://apicarto.ign.fr/api/cadastre/parcelle?code_insee={code_insee}"
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    return response.json()


@st.cache_data(show_spinner=False)
def charger_batiments_bbox(bbox):
    minx, miny, maxx, maxy = bbox
    url = (
        "https://data.geopf.fr/wfs/ows"
        f"?service=WFS"
        f"&version=2.0.0"
        f"&request=GetFeature"
        f"&typeName=BDTOPO_V3:batiment"
        f"&outputFormat=application/json"
        f"&srsName=EPSG:4326"
        f"&bbox={minx},{miny},{maxx},{maxy},EPSG:4326"
        f"&count=500"
    )
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    return response.json()


def calculer_bbox_depuis_features(features):
    minx, miny = float("inf"), float("inf")
    maxx, maxy = float("-inf"), float("-inf")

    for f in features:
        geom = f.get("geometry", {})
        coords = geom.get("coordinates", [])
        geom_type = geom.get("type")

        points = []

        if geom_type == "Polygon":
            for ring in coords:
                points.extend(ring)

        elif geom_type == "MultiPolygon":
            for polygon in coords:
                for ring in polygon:
                    points.extend(ring)

        for x, y in points:
            minx = min(minx, x)
            miny = min(miny, y)
            maxx = max(maxx, x)
            maxy = max(maxy, y)

    if minx == float("inf"):
        return None

    return [minx, miny, maxx, maxy]


def calculer_bbox_geometry(geometry):
    coords = geometry.get("coordinates", [])
    geom_type = geometry.get("type")

    points = []

    if geom_type == "Polygon":
        for ring in coords:
            points.extend(ring)

    elif geom_type == "MultiPolygon":
        for polygon in coords:
            for ring in polygon:
                points.extend(ring)

    if not points:
        return None

    xs = [p[0] for p in points]
    ys = [p[1] for p in points]

    return [min(xs), min(ys), max(xs), max(ys)]


def bbox_overlap(b1, b2):
    if not b1 or not b2:
        return False

    minx1, miny1, maxx1, maxy1 = b1
    minx2, miny2, maxx2, maxy2 = b2

    return not (maxx1 < minx2 or maxx2 < minx1 or maxy1 < miny2 or maxy2 < miny1)


# =========================
# LOGIQUE TEMPORAIRE
# =========================


def parcelle_a_bati(parcelle, batiments):
    bbox_parcelle = calculer_bbox_geometry(parcelle.get("geometry", {}))

    if not bbox_parcelle or not batiments:
        return False

    for batiment in batiments:
        bbox_batiment = calculer_bbox_geometry(batiment.get("geometry", {}))

        if bbox_overlap(bbox_parcelle, bbox_batiment):
            return True

    return False


# =========================
# CONFIG STREAMLIT
# =========================

st.set_page_config(page_title="Agent Parcelles", layout="wide")

st.title("Agent Parcelles")
st.write("Détection de parcelles et habitations potentielles")


# =========================
# PARAMÈTRES
# =========================

surface_min = st.number_input("Surface minimale (m²)", min_value=0, value=500, step=100)

mode_recherche = st.selectbox(
    "Mode de recherche", ["Parcelles", "Habitations", "Les deux"]
)


# =========================
# SESSION STATE
# =========================

if "features_filtrees" not in st.session_state:
    st.session_state.features_filtrees = []

if "resume_chargement" not in st.session_state:
    st.session_state.resume_chargement = ""

if "afficher_carte" not in st.session_state:
    st.session_state.afficher_carte = False

if "debug_bbox" not in st.session_state:
    st.session_state.debug_bbox = None

if "debug_batiments_keys" not in st.session_state:
    st.session_state.debug_batiments_keys = None

if "debug_batiments_count" not in st.session_state:
    st.session_state.debug_batiments_count = None


# =========================
# CHARGEMENT DES DONNÉES
# =========================

if st.button("Charger les parcelles"):
    try:
        data = charger_parcelles("06088")

        batiments = []
        st.session_state.debug_batiments_keys = None
        st.session_state.debug_batiments_count = 0

        bbox = None
        if "features" in data:
            bbox = calculer_bbox_depuis_features(data["features"])

        st.session_state.debug_bbox = bbox

        if bbox:
            try:
                batiments_data = charger_batiments_bbox(bbox)
                batiments = batiments_data.get("features", [])

                st.session_state.debug_batiments_keys = list(batiments_data.keys())
                st.session_state.debug_batiments_count = len(batiments)

            except Exception as e:
                st.session_state.debug_batiments_keys = [f"ERREUR: {e}"]
                st.session_state.debug_batiments_count = 0
                batiments = []

        features_filtrees = []

        if "features" in data:
            toutes = data["features"]

            for f in toutes:
                props = f.get("properties", {})
                contenance = props.get("contenance")

                if contenance is not None:
                    a_bati = parcelle_a_bati(f, batiments)

                    if mode_recherche == "Parcelles":
                        if contenance >= surface_min and not a_bati:
                            features_filtrees.append(f)

                    elif mode_recherche == "Habitations":
                        if a_bati:
                            features_filtrees.append(f)

                    elif mode_recherche == "Les deux":
                        if contenance >= surface_min or a_bati:
                            features_filtrees.append(f)

            features_filtrees = sorted(
                features_filtrees,
                key=lambda f: f["properties"].get("contenance", 0),
                reverse=True,
            )[:50]

            st.session_state.features_filtrees = features_filtrees
            st.session_state.resume_chargement = (
                f"Mode : {mode_recherche} | "
                f"Parcelles reçues : {len(toutes)} | "
                f"Résultat affiché : {len(features_filtrees)}"
            )
            st.session_state.afficher_carte = False

        else:
            st.session_state.features_filtrees = []
            st.session_state.resume_chargement = "Format inattendu reçu depuis l'API."

    except Exception as e:
        st.session_state.features_filtrees = []
        st.session_state.resume_chargement = f"Erreur : {e}"


# =========================
# INFOS / DEBUG
# =========================

if st.session_state.resume_chargement:
    st.info(st.session_state.resume_chargement)

st.write("BBOX :", st.session_state.debug_bbox)
st.write("Clés réponse bâtiments :", st.session_state.debug_batiments_keys)
st.write("Nb bâtiments :", st.session_state.debug_batiments_count)


# =========================
# AFFICHAGE CARTE
# =========================

if st.button("Afficher sur la carte"):
    st.session_state.afficher_carte = True

m = folium.Map(location=[43.7, 7.25], zoom_start=13)

if st.session_state.afficher_carte and st.session_state.features_filtrees:
    if mode_recherche == "Habitations":
        couleur = "blue"
    elif mode_recherche == "Les deux":
        couleur = "orange"
    else:
        couleur = "red"

    folium.GeoJson(
        {"type": "FeatureCollection", "features": st.session_state.features_filtrees},
        name="parcelles",
        style_function=lambda x, c=couleur: {
            "color": c,
            "weight": 1,
        },
        tooltip=folium.GeoJsonTooltip(
            fields=["contenance"], aliases=["Surface (m²) :"]
        ),
    ).add_to(m)

st_folium(m, width=1100, height=650)
