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
        f"&count=5000"
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

        if bbox_batiment and bbox_overlap(bbox_parcelle, bbox_batiment):
            return True

    return False


def nb_batiments_proches(parcelle, batiments, marge):
    bbox_parcelle = calculer_bbox_geometry(parcelle.get("geometry", {}))

    if not bbox_parcelle or not batiments:
        return 0

    minx, miny, maxx, maxy = bbox_parcelle
    bbox_elargie = [minx - marge, miny - marge, maxx + marge, maxy + marge]

    count = 0

    for batiment in batiments:
        bbox_batiment = calculer_bbox_geometry(batiment.get("geometry", {}))

        if bbox_batiment and bbox_overlap(bbox_elargie, bbox_batiment):
            count += 1

    return count


# =========================
# FONCTIONS DE SCORE
# =========================

def score_surface(contenance):
    if contenance is None:
        return 0
    if contenance < 500:
        return 5
    elif contenance < 800:
        return 15
    elif contenance < 1200:
        return 25
    elif contenance < 2000:
        return 40
    else:
        return 50


def score_occupation(a_bati):
    return 0 if a_bati else 20


def score_contexte(nb_batiments):
    if nb_batiments >= 10:
        return 30
    elif nb_batiments >= 5:
        return 20
    elif nb_batiments >= 2:
        return 10
    elif nb_batiments >= 1:
        return 5
    else:
        return 0


def calculer_score_simple(contenance, a_bati, nb_batiments):
    return (
        score_surface(contenance)
        + score_occupation(a_bati)
        + score_contexte(nb_batiments)
    )


def categorie_score(score):
    if score >= 75:
        return "Très fort"
    elif score >= 55:
        return "Fort"
    elif score >= 35:
        return "Moyen"
    else:
        return "Faible"


def couleur_score(score):
    if score >= 75:
        return "green"
    elif score >= 55:
        return "orange"
    elif score >= 35:
        return "red"
    else:
        return "darkred"


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
score_min = st.slider("Score minimum", 0, 100, 35)
marge = st.slider("Rayon analyse (approx)", 0.00001, 0.00030, 0.00005, 0.00001, format="%.5f")

communes = {
    "Nice": "06088",
    "Breil-sur-Roya": "06023",
    "Saorge": "06131",
    "Tende": "06163",
    "Roquesteron": "06106",
    "Puget-Rostang": "06099",
    "Vence": "06157",
    "La Trinité": "06149",
    "Hyères": "83069",
}

commune_choisie = st.selectbox("Commune test", list(communes.keys()))
code_insee = communes[commune_choisie]

mode_recherche = st.selectbox("Mode de recherche", ["Non bâties", "Bâties", "Toutes"])


# =========================
# SESSION STATE
# =========================

if "parcelles_scorees" not in st.session_state:
    st.session_state.parcelles_scorees = []

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

if "batiments_affiches" not in st.session_state:
    st.session_state.batiments_affiches = []


# =========================
# CHARGEMENT DES DONNÉES
# =========================

if st.button("Charger les parcelles"):
    try:
        data = charger_parcelles(code_insee)

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
                st.session_state.batiments_affiches = batiments[:500]
                st.session_state.debug_batiments_keys = list(batiments_data.keys())
                st.session_state.debug_batiments_count = len(batiments)

            except Exception as e:
                st.session_state.debug_batiments_keys = [f"ERREUR: {e}"]
                st.session_state.debug_batiments_count = 0
                st.session_state.batiments_affiches = []
                batiments = []

        features_filtrees = []
        parcelles_scorees = []

        if "features" in data:
            toutes = data["features"]
            st.write("Nombre total retourné par l'API parcelles :", len(toutes))

            for f in toutes:
                props = f.get("properties", {})
                contenance = props.get("contenance")

                if contenance is not None:
                    a_bati = parcelle_a_bati(f, batiments)
                    nb_bat = nb_batiments_proches(f, batiments, marge)
                    score = calculer_score_simple(contenance, a_bati, nb_bat)

                    garder = False

                    if mode_recherche == "Non bâties":
                        if contenance >= surface_min and not a_bati:
                            garder = True

                    elif mode_recherche == "Bâties":
                        if a_bati:
                            garder = True

                    elif mode_recherche == "Toutes":
                        if contenance >= surface_min or a_bati:
                            garder = True

                    if garder and score >= score_min:
                        props["score"] = score
                        props["a_bati"] = "Oui" if a_bati else "Non"
                        props["categorie_score"] = categorie_score(score)
                        props["nb_batiments"] = nb_bat

                        parcelles_scorees.append({
                            "feature": f,
                            "contenance": contenance,
                            "a_bati": a_bati,
                            "score": score,
                            "categorie": categorie_score(score),
                            "nb_batiments": nb_bat,
                        })

            parcelles_scorees = sorted(
                parcelles_scorees,
                key=lambda p: p["score"],
                reverse=True,
            )[:50]

            features_filtrees = [p["feature"] for p in parcelles_scorees]

            st.session_state.features_filtrees = features_filtrees
            st.session_state.parcelles_scorees = parcelles_scorees
            st.session_state.resume_chargement = (
                f"Mode : {mode_recherche} | "
                f"Parcelles reçues : {len(toutes)} | "
                f"Résultat affiché : {len(features_filtrees)}"
            )
            st.session_state.afficher_carte = False

        else:
            st.session_state.features_filtrees = []
            st.session_state.parcelles_scorees = []
            st.session_state.resume_chargement = "Format inattendu reçu depuis l'API."

    except Exception as e:
        st.session_state.features_filtrees = []
        st.session_state.parcelles_scorees = []
        st.session_state.resume_chargement = f"Erreur : {e}"


# =========================
# INFOS / DEBUG
# =========================

if st.session_state.resume_chargement:
    st.info(st.session_state.resume_chargement)

st.write("BBOX :", st.session_state.debug_bbox)
st.write("Clés réponse bâtiments :", st.session_state.debug_batiments_keys)
st.write("Nb bâtiments :", st.session_state.debug_batiments_count)
st.write("Total bâtiments chargés :", st.session_state.debug_batiments_count)


# =========================
# AFFICHAGE CARTE
# =========================

if st.button("Afficher sur la carte"):
    st.session_state.afficher_carte = True

if st.session_state.debug_bbox:
    minx, miny, maxx, maxy = st.session_state.debug_bbox
    centre_lat = (miny + maxy) / 2
    centre_lon = (minx + maxx) / 2
    m = folium.Map(location=[centre_lat, centre_lon], zoom_start=15)
else:
    m = folium.Map(location=[43.7, 7.25], zoom_start=13)

if st.session_state.afficher_carte and st.session_state.features_filtrees:
    folium.GeoJson(
        {
            "type": "FeatureCollection",
            "features": st.session_state.features_filtrees,
        },
        name="parcelles",
        style_function=lambda x: {
            "color": couleur_score(x["properties"].get("score", 0)),
            "fillColor": couleur_score(x["properties"].get("score", 0)),
            "weight": 1,
            "fillOpacity": 0.5,
        },
        tooltip=folium.GeoJsonTooltip(
            fields=["contenance", "a_bati", "score", "categorie_score", "nb_batiments"],
            aliases=["Surface (m²) :", "Bâtie :", "Score :", "Classe :", "Bâtiments proches :"],
        ),
    ).add_to(m)

if st.session_state.afficher_carte and st.session_state.batiments_affiches:
    folium.GeoJson(
        {
            "type": "FeatureCollection",
            "features": st.session_state.batiments_affiches,
        },
        name="batiments",
        style_function=lambda x: {
            "color": "black",
            "weight": 2,
            "fillColor": "blue",
            "fillOpacity": 0.5,
        },
        tooltip=folium.GeoJsonTooltip(fields=[], aliases=[]),
    ).add_to(m)

folium.LayerControl().add_to(m)
st_folium(m, width=1100, height=650)

if st.session_state.parcelles_scorees:
    st.subheader("Parcelles détectées")

    tableau = []
    for p in st.session_state.parcelles_scorees:
        tableau.append({
            "Surface (m²)": p["contenance"],
            "Bâtie": "Oui" if p["a_bati"] else "Non",
            "Score": p["score"],
            "Classe": p["categorie"],
            "Bâtiments proches": p["nb_batiments"],
        })

    st.dataframe(tableau, use_container_width=True)