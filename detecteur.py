
import csv
from pathlib import Path

DOSSIER = Path(__file__).parent



def lire_csv(nom_fichier):
    chemin = DOSSIER / nom_fichier

    with open(chemin, "r", encoding="utf-8-sig", newline="") as fichier:
        # Ignorer les lignes vides au début du fichier
        lignes_non_vides = (ligne for ligne in fichier if ligne.strip())

        lecteur = csv.DictReader(lignes_non_vides, skipinitialspace=True)

        colonnes = [
            colonne.strip() if colonne else ""
            for colonne in (lecteur.fieldnames or [])
        ]

        print(f"\nFichier : {nom_fichier}")
        print(f"Colonnes détectées : {colonnes}")

        if "commande_id" not in colonnes or "statut" not in colonnes:
            raise ValueError(
                f"Colonnes incorrectes dans {nom_fichier}. "
                f"Colonnes trouvées : {colonnes}"
            )

        lignes = {}

        for ligne in lecteur:
            ligne_nettoyee = {
                (cle.strip() if cle else ""): (valeur or "").strip()
                for cle, valeur in ligne.items()
                if cle is not None
            }

            identifiant = ligne_nettoyee.get("commande_id", "")
            statut = ligne_nettoyee.get("statut", "")

            if identifiant:
                lignes[identifiant] = statut

        return lignes



try:
    commandes = lire_csv("logiciel_commandes.csv")
    livraisons = lire_csv("logiciel_livraisons.csv")

    print("\nLecture des deux fichiers réussie.")
    print(f"Commandes : {len(commandes)}")
    print(f"Livraisons : {len(livraisons)}")

except (OSError, csv.Error, ValueError) as erreur:
    print(f"\nErreur : {erreur}")
