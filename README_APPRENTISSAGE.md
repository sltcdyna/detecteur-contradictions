# README d’apprentissage

Ce document résume ce que j’ai appris en construisant Data Sentinel.

## 1. Comprendre le besoin

J’ai appris à transformer un besoin métier en fonctionnalités concrètes.

Le problème de départ était simple : plusieurs logiciels contiennent des informations sur les mêmes personnes, mais ces informations peuvent être différentes ou incomplètes.

Pour répondre à ce problème, il faut :

1. identifier les sources ;
2. définir une clé commune ;
3. choisir les champs à comparer ;
4. définir ce qui constitue une anomalie ;
5. enregistrer les résultats ;
6. afficher les résultats de façon compréhensible.

## 2. Lire et nettoyer des fichiers CSV

J’ai appris à utiliser le module `csv` de Python pour :

- lire les en-têtes ;
- parcourir les lignes ;
- supprimer les espaces inutiles ;
- gérer les valeurs vides ;
- vérifier qu’une colonne obligatoire existe ;
- détecter les lignes sans identifiant ;
- détecter les doublons.

Le nettoyage est important, car deux valeurs peuvent être équivalentes malgré des différences de casse ou d’espaces.

## 3. Comparer plusieurs logiciels

J’ai appris à comparer des dictionnaires de données à partir d’un identifiant commun.

Le moteur rassemble les identifiants présents dans toutes les sources, puis vérifie :

- si l’identifiant existe dans chaque source ;
- si les valeurs des champs correspondent ;
- si une règle demande de signaler une différence ;
- si une règle demande de signaler une contradiction.

Cette logique permet de comparer plusieurs systèmes sans dépendre d’un nombre fixe de lignes.

## 4. Utiliser une configuration externe

J’ai appris à placer les règles métier dans [configuration.json](./configuration.json) au lieu de les écrire directement dans le code.

Cela permet de modifier :

- la clé d’identification ;
- la liste des champs ;
- les sources ;
- le comportement de chaque règle ;

sans réécrire le moteur principal.

## 5. Créer une API avec FastAPI

J’ai appris à construire une API REST avec FastAPI.

Les routes permettent de :

- vérifier que l’API fonctionne ;
- lister les sources ;
- lancer une analyse ;
- consulter l’historique ;
- récupérer les anomalies ;
- obtenir les statistiques ;
- télécharger des exports CSV.

J’ai également appris à utiliser les réponses HTTP appropriées, notamment `404` lorsqu’une analyse ou une anomalie n’existe pas.

## 6. Stocker les résultats avec SQLite

J’ai appris à utiliser SQLite pour conserver l’historique des analyses.

La base contient notamment :

- les analyses ;
- la date de chaque analyse ;
- le nombre d’anomalies ;
- le type d’anomalie ;
- le champ concerné ;
- les sources ;
- les valeurs comparées ;
- la description de l’anomalie.

L’utilisation de requêtes paramétrées permet d’éviter de construire des requêtes SQL dangereuses avec des valeurs directement concaténées.

## 7. Construire un tableau de bord web

J’ai appris à construire une interface HTML, CSS et JavaScript sans framework.

Le tableau de bord utilise :

- HTML pour la structure ;
- CSS pour la mise en page et le thème visuel ;
- JavaScript pour les interactions ;
- `fetch` pour appeler l’API ;
- Chart.js pour les graphiques.

J’ai aussi appris à gérer les états importants :

- chargement ;
- absence de données ;
- erreur API ;
- analyse sélectionnée ;
- export en cours.

## 8. Construire des statistiques utiles

J’ai appris qu’un graphique fiable doit être alimenté par des données agrégées clairement définies.

L’API calcule notamment :

- les anomalies par gravité ;
- les anomalies par type ;
- l’évolution par analyse ;
- les champs les plus touchés ;
- les sources impliquées.

Les statistiques sont calculées à partir des anomalies réellement enregistrées dans SQLite, et non à partir de valeurs écrites en dur dans l’interface.

## 9. Générer des données de démonstration

J’ai appris à créer un générateur de données reproductible avec `random.Random` et une graine.

Le script peut générer plusieurs milliers de lignes pour plusieurs logiciels et injecter volontairement :

- des différences de statut ;
- des différences de service ;
- des différences d’email ;
- des valeurs manquantes ;
- des doublons ;
- des identifiants manquants ;
- des enregistrements absents.

La graine permet d’obtenir les mêmes données lors de chaque génération, ce qui facilite les tests et les démonstrations.

## 10. Exporter des résultats

J’ai appris à générer un fichier CSV depuis une API.

Le projet propose deux niveaux d’export :

- exporter toutes les anomalies d’une analyse ;
- exporter une seule anomalie.

Chaque export contient les informations nécessaires pour comprendre et traiter l’anomalie.

## 11. Concevoir une interface lisible

J’ai appris qu’un bon tableau de bord doit hiérarchiser l’information.

Les cartes présentent les indicateurs principaux, tandis que les graphiques donnent une vision globale. Les tableaux permettent ensuite d’examiner le détail.

La palette visuelle utilise des couleurs d’accent violet, rose, vert et olive, complétées par des fonds sombres, des bordures discrètes et des textes contrastés.

## 12. Ajouter une interaction 3D raisonnable

J’ai appris à utiliser :

- `perspective` ;
- `transform-style: preserve-3d` ;
- `rotateX` ;
- `rotateY` ;
- `translateY` ;
- les événements `pointermove` et `pointerleave`.

L’effet reste léger afin de ne pas gêner la lecture. Le projet respecte aussi la préférence utilisateur `prefers-reduced-motion`.

## 13. Tester et diagnostiquer

J’ai appris à vérifier une fonctionnalité sur plusieurs niveaux :

1. vérifier la syntaxe Python ;
2. appeler directement l’API ;
3. vérifier le contenu de la base ;
4. ouvrir l’interface dans un navigateur ;
5. consulter les erreurs JavaScript ;
6. tester les interactions et les téléchargements.

Un exemple important a été le problème de chargement des sources : l’API fonctionnait, mais la fonction JavaScript était déclarée dans une mauvaise portée. L’observation de l’erreur du navigateur a permis de trouver puis corriger la cause.

## 14. Ce que je peux améliorer ensuite

Les prochaines améliorations possibles sont :

- ajouter une authentification ;
- remplacer les fichiers CSV par une base de données métier ;
- ajouter une pagination côté API ;
- éviter de charger plusieurs milliers de lignes dans un seul tableau ;
- ajouter des filtres par source et par gravité ;
- créer des tests automatisés ;
- ajouter des graphiques par période ;
- permettre la correction ou la validation d’une anomalie ;
- ajouter une notification lorsqu’une nouvelle analyse est terminée.

## Conclusion

Ce projet m’a permis de relier plusieurs domaines :

- Python ;
- lecture de données ;
- logique de comparaison ;
- API REST ;
- SQLite ;
- HTML/CSS ;
- JavaScript ;
- visualisation avec Chart.js ;
- génération de données ;
- tests et débogage.

Data Sentinel est donc à la fois une application fonctionnelle et un support d’apprentissage complet pour comprendre le parcours d’une donnée, depuis plusieurs sources jusqu’à son analyse et sa visualisation.

