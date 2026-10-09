# Data Sentinel

Data Sentinel est une application de détection d’anomalies entre plusieurs logiciels d’entreprise.

L’objectif est de comparer des données provenant de différentes sources, comme les ressources humaines, la paie, les accès informatiques ou la formation, afin de repérer les informations qui ne correspondent pas.

## Vidéo de démonstration

Une vidéo de présentation du projet sera ajoutée au dépôt GitHub :

[Voir la vidéo de démonstration](./demo/video-demo.mp4)

## Ce que fait le projet

L’application permet de :

- comparer plusieurs fichiers CSV ;
- détecter les contradictions entre les logiciels ;
- repérer les valeurs manquantes ;
- identifier les doublons ;
- détecter les identifiants absents ;
- signaler les enregistrements présents dans un logiciel mais absents d’un autre ;
- afficher les résultats dans un tableau de bord interactif ;
- consulter l’historique des analyses ;
- filtrer les anomalies par type ou par recherche ;
- exporter toutes les anomalies d’une analyse au format CSV ;
- exporter une anomalie précise au format CSV ;
- visualiser l’évolution des anomalies avec Chart.js.

## Sources de données

Le projet peut comparer plusieurs logiciels. Les données de démonstration comprennent notamment :

- Référentiel RH ;
- Paie ;
- Gestion des accès ;
- Annuaire IT ;
- Gestion des projets ;
- Avantages salariés ;
- Formation.

Les fichiers sont placés dans [donnees/demo/](./donnees/demo/).

## Installation

Le projet utilise Python et FastAPI.

Depuis le dossier du projet :

```bash
.venv/bin/python -m pip install fastapi uvicorn
```

## Lancer l’API

```bash
.venv/bin/uvicorn api:app --host 127.0.0.1 --port 8000
```

L’API est ensuite disponible à l’adresse :

```text
http://127.0.0.1:8000
```

La documentation automatique est disponible ici :

```text
http://127.0.0.1:8000/docs
```

## Lancer l’interface

Dans un autre terminal, depuis la racine du projet :

```bash
python3 -m http.server 5500
```

Puis ouvrir :

```text
http://127.0.0.1:5500/interface/index.html
```

## Générer davantage de données

Le script [generer_donnees_demo.py](./generer_donnees_demo.py) génère des données synthétiques reproductibles.

Exemple avec 1 200 identifiants :

```bash
.venv/bin/python generer_donnees_demo.py --rows 1200 --seed 20261009 --force
```

Exemple avec 5 000 identifiants :

```bash
.venv/bin/python generer_donnees_demo.py --rows 5000 --seed 20261009 --force
```

Le nombre d’identifiants augmente le volume de lignes générées dans les différents logiciels.

## Configuration

Les sources, les champs comparés et les règles de comparaison sont définis dans [configuration.json](./configuration.json).

Les règles actuelles permettent notamment de considérer :

- une différence de statut comme une contradiction potentielle ;
- une différence de service comme une différence à vérifier ;
- une différence d’adresse email comme une contradiction potentielle.

## Graphiques

Le tableau de bord utilise Chart.js pour afficher :

- la répartition des anomalies ;
- les anomalies par gravité ;
- les anomalies par type ;
- l’évolution des analyses ;
- les champs les plus touchés ;
- la comparaison des sources.

L’interface possède également une palette personnalisée, des effets de profondeur et une interaction 3D légère au survol des cartes.

## Structure principale

```text
api.py                  API FastAPI
moteur.py               Lecture, comparaison et enregistrement des données
configuration.json      Sources et règles de comparaison
generer_donnees_demo.py Générateur de données de démonstration
interface/index.html    Tableau de bord web
donnees/demo/           Sources CSV générées
resultats/anomalies.db  Historique SQLite des analyses
```

## API principale

Quelques routes importantes :

```text
GET  /sources
GET  /sources/verification
POST /analyses
GET  /analyses
GET  /analyses/statistiques
GET  /analyses/{analyse_id}/anomalies
GET  /analyses/{analyse_id}/export-csv
GET  /analyses/{analyse_id}/anomalies/{anomalie_id}/export-csv
```

## Vérifier le code

```bash
.venv/bin/python -m py_compile api.py moteur.py generer_donnees_demo.py
```
# detecteur-contradictions
