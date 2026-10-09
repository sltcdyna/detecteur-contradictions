
import csv
import io
import json
import sqlite3
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

from moteur import (
    lancer_analyse,
    BASE_DE_DONNEES,
    creer_base_de_donnees
)

GRAVITES = {
    "CONTRADICTION_POTENTIELLE": "Élevée",
    "ENREGISTREMENT_ABSENT": "Élevée",
    "IDENTIFIANT_MANQUANT": "Élevée",
    "DOUBLON": "Moyenne",
    "VALEUR_MANQUANTE": "Moyenne",
}


DOSSIER = Path(__file__).resolve().parent
FICHIER_CONFIGURATION = DOSSIER / "configuration.json"


app = FastAPI(
    title="Détecteur de contradictions",
    description=(
        "API de comparaison de données entre plusieurs "
        "systèmes d'information."
    ),
    version="1.1.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def accueil():
    return {
        "message": "API du détecteur de contradictions opérationnelle",
        "documentation": "/docs"
    }


@app.get("/sources")
def consulter_sources():
    try:
        with open(
            FICHIER_CONFIGURATION,
            "r",
            encoding="utf-8"
        ) as fichier:
            configuration = json.load(fichier)

        sources = configuration.get("sources", [])

        return {
            "total": len(sources),
            "sources": sources
        }

    except (OSError, json.JSONDecodeError) as erreur:
        raise HTTPException(
            status_code=500,
            detail=f"Impossible de lire la configuration : {erreur}"
        )


@app.get("/sources/verification")
def verifier_sources():
    try:
        with open(
            FICHIER_CONFIGURATION,
            "r",
            encoding="utf-8"
        ) as fichier:
            configuration = json.load(fichier)

    except (OSError, json.JSONDecodeError) as erreur:
        raise HTTPException(
            status_code=500,
            detail=str(erreur)
        )

    resultats = []

    for source in configuration.get("sources", []):
        chemin = Path(source.get("fichier", ""))

        if not chemin.is_absolute():
            chemin = DOSSIER / chemin

        resultat = {
            "nom": source.get("nom", "Source sans nom"),
            "fichier": source.get("fichier", ""),
            "statut": "",
            "message": ""
        }

        if not chemin.is_file():
            resultat["statut"] = "introuvable"
            resultat["message"] = "Le fichier n'existe pas."

        else:
            try:
                with open(
                    chemin,
                    "r",
                    encoding="utf-8-sig",
                    newline=""
                ) as fichier:
                    lecteur = csv.reader(fichier)
                    entete = next(lecteur, None)

                if not entete:
                    resultat["statut"] = "erreur"
                    resultat["message"] = "Le fichier est vide."
                else:
                    resultat["statut"] = "disponible"
                    resultat["message"] = "Fichier accessible."

            except (OSError, UnicodeError, csv.Error) as erreur:
                resultat["statut"] = "erreur"
                resultat["message"] = str(erreur)

        resultats.append(resultat)

    return {
        "total": len(resultats),
        "sources": resultats
    }


@app.post("/analyses")
def creer_analyse():
    try:
        lancer_analyse()

        return {
            "message": "Analyse terminée",
            "conseil": (
                "Consultez GET /analyses pour retrouver "
                "l'historique."
            )
        }

    except (OSError, ValueError, json.JSONDecodeError) as erreur:
        raise HTTPException(
            status_code=400,
            detail=str(erreur)
        )


@app.get("/analyses")
def consulter_historique():
    creer_base_de_donnees()

    with sqlite3.connect(BASE_DE_DONNEES) as connexion:
        connexion.row_factory = sqlite3.Row

        lignes = connexion.execute("""
            SELECT id, date_analyse, nombre_anomalies
            FROM analyses
            ORDER BY id DESC
        """).fetchall()

    return {
        "total": len(lignes),
        "analyses": [dict(ligne) for ligne in lignes]
    }


@app.get("/analyses/statistiques")
def consulter_statistiques():
    """Retourne les agrégats utilisés par le tableau de bord."""
    creer_base_de_donnees()

    with sqlite3.connect(BASE_DE_DONNEES) as connexion:
        connexion.row_factory = sqlite3.Row
        analyses = connexion.execute("""
            SELECT id, date_analyse, nombre_anomalies
            FROM analyses
            ORDER BY id
        """).fetchall()
        anomalies = connexion.execute("""
            SELECT analyse_id, type_anomalie, champ, source_1, source_2
            FROM anomalies
            ORDER BY id
        """).fetchall()

    par_gravite = {"Élevée": 0, "Moyenne": 0, "À vérifier": 0}
    par_type = {}
    par_champ = {}
    par_source = {}
    par_analyse = {
        ligne["id"]: {
            "id": ligne["id"],
            "date_analyse": ligne["date_analyse"],
            "nombre_anomalies": ligne["nombre_anomalies"],
        }
        for ligne in analyses
    }

    for anomalie in anomalies:
        type_anomalie = anomalie["type_anomalie"] or "Non précisé"
        gravite = GRAVITES.get(type_anomalie, "À vérifier")
        par_gravite[gravite] += 1
        par_type[type_anomalie] = par_type.get(type_anomalie, 0) + 1

        champ = anomalie["champ"] or "Non précisé"
        par_champ[champ] = par_champ.get(champ, 0) + 1

        sources = {
            source for source in (anomalie["source_1"], anomalie["source_2"])
            if source
        }
        for source in sources or {"Non précisée"}:
            par_source[source] = par_source.get(source, 0) + 1

    return {
        "gravite": [
            {"libelle": libelle, "nombre": nombre}
            for libelle, nombre in par_gravite.items()
        ],
        "types": [
            {"libelle": libelle, "nombre": nombre}
            for libelle, nombre in sorted(
                par_type.items(), key=lambda element: element[1], reverse=True
            )
        ],
        "evolution": list(par_analyse.values()),
        "champs": [
            {"libelle": libelle, "nombre": nombre}
            for libelle, nombre in sorted(
                par_champ.items(), key=lambda element: element[1], reverse=True
            )
        ],
        "sources": [
            {"libelle": libelle, "nombre": nombre}
            for libelle, nombre in sorted(
                par_source.items(), key=lambda element: element[1], reverse=True
            )
        ],
    }


@app.get("/analyses/{analyse_id}/anomalies")
def consulter_anomalies(analyse_id: int):
    creer_base_de_donnees()

    with sqlite3.connect(BASE_DE_DONNEES) as connexion:
        connexion.row_factory = sqlite3.Row

        analyse = connexion.execute(
            "SELECT id FROM analyses WHERE id = ?",
            (analyse_id,)
        ).fetchone()

        if analyse is None:
            raise HTTPException(
                status_code=404,
                detail="Analyse introuvable."
            )

        lignes = connexion.execute("""
            SELECT
                id,
                date_detection,
                type_anomalie,
                identifiant,
                champ,
                source_1,
                valeur_1,
                source_2,
                valeur_2,
                description
            FROM anomalies
            WHERE analyse_id = ?
            ORDER BY id
        """, (analyse_id,)).fetchall()

    return {
        "analyse_id": analyse_id,
        "total": len(lignes),
        "anomalies": [dict(ligne) for ligne in lignes]
    }


@app.get("/analyses/{analyse_id}/export-csv")
def exporter_anomalies_csv(analyse_id: int):
    creer_base_de_donnees()

    with sqlite3.connect(BASE_DE_DONNEES) as connexion:
        analyse = connexion.execute(
            "SELECT id FROM analyses WHERE id = ?",
            (analyse_id,)
        ).fetchone()

        if analyse is None:
            raise HTTPException(
                status_code=404,
                detail="Analyse introuvable."
            )

        lignes = connexion.execute("""
            SELECT
                date_detection,
                type_anomalie,
                identifiant,
                champ,
                source_1,
                valeur_1,
                source_2,
                valeur_2,
                description
            FROM anomalies
            WHERE analyse_id = ?
            ORDER BY id
        """, (analyse_id,)).fetchall()

    sortie = io.StringIO(newline="")
    redacteur = csv.writer(sortie, delimiter=";")

    redacteur.writerow([
        "Date de détection",
        "Type d'anomalie",
        "Identifiant",
        "Champ",
        "Source 1",
        "Valeur 1",
        "Source 2",
        "Valeur 2",
        "Description"
    ])

    for ligne in lignes:
        redacteur.writerow(ligne)

    contenu = "\ufeff" + sortie.getvalue()
    sortie.close()

    nom_fichier = f"anomalies_analyse_{analyse_id}.csv"

    return StreamingResponse(
        iter([contenu]),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": (
                f'attachment; filename="{nom_fichier}"'
            )
        }
    )


@app.get("/analyses/{analyse_id}/anomalies/{anomalie_id}/export-csv")
def exporter_anomalie_csv(analyse_id: int, anomalie_id: int):
    """Exporte une anomalie précise au format CSV."""
    creer_base_de_donnees()

    with sqlite3.connect(BASE_DE_DONNEES) as connexion:
        ligne = connexion.execute("""
            SELECT
                date_detection,
                type_anomalie,
                identifiant,
                champ,
                source_1,
                valeur_1,
                source_2,
                valeur_2,
                description
            FROM anomalies
            WHERE id = ? AND analyse_id = ?
        """, (anomalie_id, analyse_id)).fetchone()

    if ligne is None:
        raise HTTPException(
            status_code=404,
            detail="Anomalie introuvable dans cette analyse."
        )

    sortie = io.StringIO(newline="")
    redacteur = csv.writer(sortie, delimiter=";")
    redacteur.writerow([
        "Date de détection",
        "Type d'anomalie",
        "Identifiant",
        "Champ",
        "Source 1",
        "Valeur 1",
        "Source 2",
        "Valeur 2",
        "Description"
    ])
    redacteur.writerow(ligne)

    contenu = "\ufeff" + sortie.getvalue()
    sortie.close()
    nom_fichier = f"anomalie_{anomalie_id}_analyse_{analyse_id}.csv"

    return StreamingResponse(
        iter([contenu]),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": (
                f'attachment; filename="{nom_fichier}"'
            )
        }
    )
