"""Génère des CSV de démonstration réalistes pour le détecteur.

Exemple :
    python generer_donnees_demo.py
    python generer_donnees_demo.py --rows 1500 --seed 20261009

Les fichiers existants ne sont jamais écrasés par défaut : les données sont
écrites dans ``donnees/demo`` et peuvent être régénérées avec la même graine.
"""

from __future__ import annotations

import argparse
import csv
import random
from pathlib import Path


DOSSIER = Path(__file__).resolve().parent
DOSSIER_DEFAUT = DOSSIER / "donnees" / "demo"
COLONNES = ("identifiant", "statut", "service", "email")

SOURCES = (
    ("Référentiel RH", "referentiel_rh.csv"),
    ("Paie", "paie.csv"),
    ("Gestion des accès", "gestion_acces.csv"),
    ("Annuaire IT", "annuaire_it.csv"),
    ("Gestion des projets", "gestion_projets.csv"),
    ("Avantages salariés", "avantages.csv"),
    ("Formation", "formation.csv"),
)

PRENOMS = (
    "Alice", "Amine", "Camille", "Chloé", "Clara", "David", "Élodie",
    "Fatou", "Hugo", "Inès", "Jules", "Karim", "Léa", "Lina", "Lucas",
    "Manon", "Marc", "Nadia", "Noah", "Omar", "Paul", "Sarah", "Sofia",
    "Thomas", "Yanis",
)
NOMS = (
    "Bernard", "Blanc", "Bonnet", "Caron", "Chevalier", "Colin", "Diallo",
    "Dubois", "Dupont", "Fontaine", "Garcia", "Garnier", "Girard", "Henry",
    "Lefèvre", "Leroy", "Marchand", "Martin", "Moreau", "Nguyen", "Perrin",
    "Petit", "Robert", "Roux", "Simon",
)
SERVICES = (
    "Finance", "Informatique", "Juridique", "Marketing", "Opérations",
    "Ressources humaines", "Support client", "Ventes",
)
STATUTS = ("Actif", "Inactif", "En congé")


def _personnes(nombre: int, hasard: random.Random) -> list[dict[str, str]]:
    personnes = []
    for numero in range(1, nombre + 1):
        prenom = hasard.choice(PRENOMS)
        nom = hasard.choice(NOMS)
        identifiant = f"E{numero:05d}"
        email = f"{prenom}.{nom}{numero}@exemple.fr".lower()
        personnes.append({
            "identifiant": identifiant,
            "statut": hasard.choices(STATUTS, weights=(84, 11, 5))[0],
            "service": hasard.choice(SERVICES),
            "email": email,
        })
    return personnes


def _ligne(personne: dict[str, str], index_source: int, hasard: random.Random) -> dict[str, str]:
    ligne = personne.copy()

    # Chaque source possède un petit taux de divergence, suffisamment visible
    # dans l'analyse sans rendre toutes les comparaisons incohérentes.
    if hasard.random() < 0.035:
        ligne["statut"] = hasard.choice([statut for statut in STATUTS if statut != ligne["statut"]])
    if hasard.random() < 0.045:
        ligne["service"] = hasard.choice([service for service in SERVICES if service != ligne["service"]])
    if hasard.random() < 0.025:
        ligne["email"] = ligne["email"].replace("@exemple.fr", "@entreprise.fr")

    # Valeurs absentes réparties sur plusieurs applications.
    if hasard.random() < 0.012:
        ligne[hasard.choice(("statut", "service", "email"))] = ""

    # Quelques sources historiques ont volontairement un statut absent plus
    # souvent, ce qui ressemble à une migration de données partielle.
    if index_source in (1, 5) and hasard.random() < 0.006:
        ligne["service"] = ""
    return ligne


def generer_donnees(
    dossier: Path = DOSSIER_DEFAUT,
    nombre_lignes: int = 1200,
    graine: int = 20261009,
    ecraser: bool = False,
) -> list[Path]:
    """Crée sept sources CSV déterministes et retourne leurs chemins."""
    if nombre_lignes < 100:
        raise ValueError("Le nombre de lignes doit être au moins 100.")
    if dossier.exists() and any(dossier.iterdir()) and not ecraser:
        raise FileExistsError(
            f"{dossier} contient déjà des fichiers ; utilisez --force pour les remplacer."
        )
    dossier.mkdir(parents=True, exist_ok=True)
    hasard = random.Random(graine)
    personnes = _personnes(nombre_lignes, hasard)
    chemins = []

    for index_source, (_, nom_fichier) in enumerate(SOURCES):
        # Les logiciels n'ont pas tous la même couverture fonctionnelle.
        taux_presence = (0.985, 0.965, 0.94, 0.975, 0.91, 0.88, 0.90)[index_source]
        lignes = [
            _ligne(personne, index_source, hasard)
            for personne in personnes
            if hasard.random() < taux_presence
        ]

        # Anomalies explicites : doublon, identifiant vide et quelques absences.
        if index_source in (0, 2, 4):
            lignes.append(lignes[0].copy())
        if index_source == 3:
            ligne_vide = lignes[1].copy()
            ligne_vide["identifiant"] = ""
            lignes.append(ligne_vide)

        chemin = dossier / nom_fichier
        with chemin.open("w", encoding="utf-8", newline="") as fichier:
            ecrivain = csv.DictWriter(fichier, fieldnames=COLONNES)
            ecrivain.writeheader()
            ecrivain.writerows(lignes)
        chemins.append(chemin)
    return chemins


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Génère les sources CSV synthétiques du détecteur."
    )
    parser.add_argument("--rows", type=int, default=1200, help="Identifiants de référence (défaut : 1200).")
    parser.add_argument("--seed", type=int, default=20261009, help="Graine reproductible.")
    parser.add_argument("--output-dir", type=Path, default=DOSSIER_DEFAUT, help="Dossier de sortie.")
    parser.add_argument("--force", action="store_true", help="Remplace les CSV du dossier de sortie.")
    return parser.parse_args()


def main() -> None:
    args = _arguments()
    if args.force and args.output_dir.exists():
        for chemin in args.output_dir.glob("*.csv"):
            chemin.unlink()
    chemins = generer_donnees(args.output_dir, args.rows, args.seed, args.force)
    print(f"{len(chemins)} sources générées dans {args.output_dir}")
    for chemin in chemins:
        print(f"- {chemin.name}")


if __name__ == "__main__":
    main()
