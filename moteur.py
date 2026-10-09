
import csv
import json
import sqlite3
from pathlib import Path
from datetime import datetime
from itertools import combinations

DOSSIER = Path(__file__).resolve().parent
FICHIER_CONFIGURATION = DOSSIER / "configuration.json"
DOSSIER_RESULTATS = DOSSIER / "resultats"
BASE_DE_DONNEES = DOSSIER_RESULTATS / "anomalies.db"


def charger_configuration():
    """Charge les paramètres du moteur depuis le fichier JSON."""
    with open(FICHIER_CONFIGURATION, "r", encoding="utf-8") as fichier:
        configuration = json.load(fichier)

    champs_obligatoires = [
        "cle_identification",
        "champs_a_comparer",
        "sources"
    ]

    for champ in champs_obligatoires:
        if champ not in configuration:
            raise ValueError(
                f"Configuration invalide : champ '{champ}' manquant."
            )

    if len(configuration["sources"]) < 2:
        raise ValueError("Il faut au moins deux sources à comparer.")

    return configuration


def lire_csv(source, cle_identification, champs_a_comparer):
    """Lit une source CSV et prépare ses données pour la comparaison."""
    chemin = DOSSIER / source["fichier"]

    if not chemin.is_file():
        raise FileNotFoundError(
            f"Fichier introuvable pour {source['nom']} : {chemin}"
        )

    with open(
        chemin,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as fichier:
        lignes_non_vides = (
            ligne for ligne in fichier if ligne.strip()
        )

        lecteur = csv.DictReader(
            lignes_non_vides,
            skipinitialspace=True
        )

        colonnes = [
            colonne.strip() if colonne else ""
            for colonne in (lecteur.fieldnames or [])
        ]

        colonnes_requises = [
            cle_identification,
            *champs_a_comparer
        ]

        colonnes_manquantes = [
            colonne
            for colonne in colonnes_requises
            if colonne not in colonnes
        ]

        if colonnes_manquantes:
            raise ValueError(
                f"{source['nom']} : colonnes manquantes : "
                f"{', '.join(colonnes_manquantes)}"
            )

        donnees = {}
        anomalies = []

        for numero_ligne, ligne in enumerate(lecteur, start=2):
            ligne_nettoyee = {
                (cle.strip() if cle else ""):
                (valeur or "").strip()
                for cle, valeur in ligne.items()
                if cle is not None
            }

            identifiant = ligne_nettoyee.get(
                cle_identification, ""
            )

            if not identifiant:
                anomalies.append({
                    "type": "IDENTIFIANT_MANQUANT",
                    "identifiant": "",
                    "champ": cle_identification,
                    "source_1": source["nom"],
                    "source_2": "",
                    "valeur_1": "",
                    "valeur_2": "",
                    "description": (
                        f"Identifiant absent à la ligne "
                        f"{numero_ligne} de {source['nom']}."
                    )
                })
                continue

            if identifiant in donnees:
                anomalies.append({
                    "type": "DOUBLON",
                    "identifiant": identifiant,
                    "champ": cle_identification,
                    "source_1": source["nom"],
                    "source_2": "",
                    "valeur_1": identifiant,
                    "valeur_2": identifiant,
                    "description": (
                        f"L'identifiant {identifiant} apparaît "
                        f"plusieurs fois dans {source['nom']}."
                    )
                })
                continue

            donnees[identifiant] = ligne_nettoyee

            for champ in champs_a_comparer:
                if not ligne_nettoyee.get(champ, ""):
                    anomalies.append({
                        "type": "VALEUR_MANQUANTE",
                        "identifiant": identifiant,
                        "champ": champ,
                        "source_1": source["nom"],
                        "source_2": "",
                        "valeur_1": "",
                        "valeur_2": "",
                        "description": (
                            f"La valeur du champ '{champ}' est "
                            f"absente pour {identifiant} dans "
                            f"{source['nom']}."
                        )
                    })

    print(
        f"Lecture de {source['nom']} : "
        f"{len(donnees)} identifiants."
    )

    return donnees, anomalies



def creer_base_de_donnees():
    """Crée les tables nécessaires à l'historique des analyses."""
    DOSSIER_RESULTATS.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(BASE_DE_DONNEES) as connexion:
        connexion.execute("PRAGMA foreign_keys = ON")

        connexion.execute("""
            CREATE TABLE IF NOT EXISTS analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date_analyse TEXT NOT NULL,
                nombre_anomalies INTEGER NOT NULL DEFAULT 0
            )
        """)

        connexion.execute("""
            CREATE TABLE IF NOT EXISTS anomalies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date_detection TEXT NOT NULL,
                type_anomalie TEXT NOT NULL,
                identifiant TEXT,
                champ TEXT,
                source_1 TEXT,
                valeur_1 TEXT,
                source_2 TEXT,
                valeur_2 TEXT,
                description TEXT NOT NULL
            )
        """)

        colonnes = {
            ligne[1]
            for ligne in connexion.execute(
                "PRAGMA table_info(anomalies)"
            ).fetchall()
        }

        if "analyse_id" not in colonnes:
            connexion.execute("""
                ALTER TABLE anomalies
                ADD COLUMN analyse_id INTEGER
                REFERENCES analyses(id)
            """)





def enregistrer_anomalies(anomalies):
    """Enregistre une nouvelle analyse sans effacer les précédentes."""
    date_detection = datetime.now().isoformat(
        timespec="seconds"
    )

    with sqlite3.connect(BASE_DE_DONNEES) as connexion:
        connexion.execute("PRAGMA foreign_keys = ON")

        curseur = connexion.execute("""
            INSERT INTO analyses (date_analyse, nombre_anomalies)
            VALUES (?, ?)
        """, (date_detection, len(anomalies)))

        analyse_id = curseur.lastrowid

        for anomalie in anomalies:
            connexion.execute("""
                INSERT INTO anomalies (
                    date_detection,
                    type_anomalie,
                    identifiant,
                    champ,
                    source_1,
                    valeur_1,
                    source_2,
                    valeur_2,
                    description,
                    analyse_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                date_detection,
                anomalie["type"],
                anomalie.get("identifiant", ""),
                anomalie.get("champ", ""),
                anomalie.get("source_1", ""),
                anomalie.get("valeur_1", ""),
                anomalie.get("source_2", ""),
                anomalie.get("valeur_2", ""),
                anomalie["description"],
                analyse_id
            ))

    return analyse_id



def comparer_sources(
    source_1,
    donnees_1,
    source_2,
    donnees_2,
    champs_a_comparer,
    cle_identification,
    regles
):
    """Compare deux sources en appliquant les règles configurées."""
    anomalies = []

    tous_les_identifiants = (
        set(donnees_1.keys()) | set(donnees_2.keys())
    )

    for identifiant in sorted(tous_les_identifiants):
        existe_1 = identifiant in donnees_1
        existe_2 = identifiant in donnees_2

        if not existe_1 or not existe_2:
            source_absente = source_1 if not existe_1 else source_2
            source_presente = source_2 if not existe_1 else source_1

            anomalies.append({
                "type": "ENREGISTREMENT_ABSENT",
                "identifiant": identifiant,
                "champ": cle_identification,
                "source_1": source_1,
                "source_2": source_2,
                "valeur_1": (
                    identifiant if existe_1 else ""
                ),
                "valeur_2": (
                    identifiant if existe_2 else ""
                ),
                "description": (
                    f"{identifiant} est présent dans "
                    f"{source_presente}, mais absent de "
                    f"{source_absente}."
                )
            })
            continue

        for champ in champs_a_comparer:
            valeur_1 = donnees_1[identifiant].get(champ, "")
            valeur_2 = donnees_2[identifiant].get(champ, "")

            if not valeur_1 or not valeur_2:
                continue

            if valeur_1.casefold() == valeur_2.casefold():
                continue

            regle = regles.get(champ, {})
            mode = regle.get("mode", "difference_a_verifier")
            description_regle = regle.get(
                "description",
                "Les valeurs de ce champ doivent être vérifiées."
            )

            if mode == "ignorer":
                continue

            if mode == "contradiction_si_different":
                type_anomalie = "CONTRADICTION_POTENTIELLE"
            else:
                type_anomalie = "DIFFERENCE_A_VERIFIER"

            anomalies.append({
                "type": type_anomalie,
                "identifiant": identifiant,
                "champ": champ,
                "source_1": source_1,
                "source_2": source_2,
                "valeur_1": valeur_1,
                "valeur_2": valeur_2,
                "description": (
                    f"{identifiant} — champ '{champ}' : "
                    f"{source_1} = '{valeur_1}', "
                    f"{source_2} = '{valeur_2}'. "
                    f"Règle : {description_regle}"
                )
            })

    return anomalies
2


def lancer_analyse():
    """Exécute le processus complet de détection."""
    print("\n=== DÉTECTEUR DE CONTRADICTIONS ===\n")

    configuration = charger_configuration()

    cle = configuration["cle_identification"]
    champs = configuration["champs_a_comparer"]
    sources = configuration["sources"]

    donnees_par_source = {}
    anomalies = []

    for source in sources:
        donnees, anomalies_lecture = lire_csv(
            source,
            cle,
            champs
        )

        donnees_par_source[source["nom"]] = donnees
        anomalies.extend(anomalies_lecture)

    for source_1, source_2 in combinations(sources, 2):
        anomalies_comparaison = comparer_sources(
            source_1["nom"],
        donnees_par_source[source_1["nom"]],
            source_2["nom"],
            donnees_par_source[source_2["nom"]],
            champs,
            cle,
            configuration.get("regles", {})
        )

        anomalies.extend(anomalies_comparaison)

    creer_base_de_donnees()
    analyse_id = enregistrer_anomalies(anomalies)

    print(f"Numéro de l'analyse : {analyse_id}")

    print("\n=== RÉSULTATS ===")
    print(f"Anomalies détectées : {len(anomalies)}")

    for anomalie in anomalies:
        print(
            f"[{anomalie['type']}] "
            f"{anomalie['description']}"
        )

    print(f"\nRésultats enregistrés dans : {BASE_DE_DONNEES}")
    print("\nAnalyse terminée.")


def afficher_historique():
    """Affiche les analyses précédentes et leur nombre d'anomalies."""
    if not BASE_DE_DONNEES.exists():
        print("Aucune base de données trouvée.")
        return

    with sqlite3.connect(BASE_DE_DONNEES) as connexion:
        analyses = connexion.execute("""
            SELECT id, date_analyse, nombre_anomalies
            FROM analyses
            ORDER BY id DESC
        """).fetchall()

    if not analyses:
        print("Aucune analyse enregistrée.")
        return

    print("\n=== HISTORIQUE DES ANALYSES ===")

    for identifiant, date_analyse, nombre_anomalies in analyses:
        print(
            f"Analyse #{identifiant} | "
            f"Date : {date_analyse} | "
            f"Anomalies : {nombre_anomalies}"
        )


def afficher_anomalies_analyse(identifiant_analyse):
    """Affiche les anomalies associées à une analyse précise."""
    with sqlite3.connect(BASE_DE_DONNEES) as connexion:
        anomalies = connexion.execute("""
            SELECT type_anomalie, identifiant, champ, description
            FROM anomalies
            WHERE analyse_id = ?
            ORDER BY id
        """, (identifiant_analyse,)).fetchall()

    if not anomalies:
        print(
            f"Aucune anomalie trouvée pour l'analyse "
            f"#{identifiant_analyse}."
        )
        return

    print(f"\n=== ANOMALIES DE L'ANALYSE #{identifiant_analyse} ===")

    for type_anomalie, identifiant, champ, description in anomalies:
        print(f"[{type_anomalie}] {description}")


if __name__ == "__main__":
    try:
        print("\n=== DÉTECTEUR DE CONTRADICTIONS ===")
        print("1. Lancer une nouvelle analyse")
        print("2. Consulter l'historique")
        print("3. Consulter les anomalies d'une analyse")

        choix = input("\nTon choix : ").strip()

        if choix == "1":
            lancer_analyse()
        elif choix == "2":
            afficher_historique()
        elif choix == "3":
            afficher_historique()
            numero = input("\nNuméro de l'analyse : ").strip()

            if numero.isdigit():
                afficher_anomalies_analyse(int(numero))
            else:
                print("Numéro invalide.")
        else:
            print("Choix invalide.")

    except (OSError, ValueError, json.JSONDecodeError) as erreur:
        print(f"\nERREUR : {erreur}")
