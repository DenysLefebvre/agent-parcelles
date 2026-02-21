# Agent IA de Détection de Parcelles Abandonnées

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Agent automatisé** pour identifier et analyser des parcelles ou biens immobiliers abandonnés/sous-exploités, en combinant des données cadastrales (Géoportail) et des images satellites (Sentinel). Idéal pour les études urbaines, la réhabilitation ou la gestion foncière.

---

## **Fonctionnalités**
- **Collecte de données** : Parcelles cadastrales (Géoportail) + images satellites (Sentinel Hub).
- **Analyse visuelle** : Détection de végétation envahissante (NDVI) et bâtiments dégradés.
- **Interface interactive** : Carte Folium/Streamlit avec filtres (superficie, score d’abandon).
- **Rapports exportables** : CSV et PDF pour un usage professionnel.

---

## **Installation**
### Prérequis
- Python 3.13
- Environnement virtuel recommandé

### Étapes
1. Cloner le dépôt :
   ```bash
   git clone https://github.com/votre-utilisateur/agent-parcelles.git
   cd agent-parcelles
