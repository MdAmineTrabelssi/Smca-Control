# Répartition pratique du binôme

## Membre A — interface et visualisation

1. Installer le projet et charger la démonstration.
2. Étudier `app.py` : menu, formulaires, lecture des données et messages de validation.
3. Expliquer la matrice 5×5 et la différence initial/résiduel.
4. Étudier `smca/reports.py` : CSV protégé contre les formules et mise en page PDF.
5. Exécuter `python -m pytest tests/test_ui.py -q` et présenter le parcours utilisateur.

## Membre B — données et logique métier

1. Étudier les trois tables et les clés étrangères dans `smca/service.py`.
2. Expliquer `score`, `level`, la priorité BIA et les contrôles RTO/MTPD.
3. Tester sauvegarde, modification, suppression protégée et reprise de la base.
4. Exécuter `python -m pytest tests/test_service.py -q`.
5. Expliquer le volume Docker et effectuer une sauvegarde/restauration.

## Travail partagé

Créer un dépôt GitLab privé puis deux branches : `frontend` (A), `backend` (B). Le dépôt distant n’est pas créé par ce livrable. Les deux membres relisent les demandes de fusion ; exécuter tous les tests avant intégration dans `main`. Ne jamais versionner `.venv`, les bases réelles ou des secrets.

L’API `Store` constitue le point d’accord ; toute modification de ses paramètres se discute avant développement. Pour un conflit dans les fichiers partagés Docker/docs, choisir un seul éditeur et faire relire par l’autre. Chaque membre doit pouvoir expliquer et relancer l’application complète.

## Ordre de travail suggéré

1. Ensemble : faire valider architecture, périmètre et méthode de scoring.
2. A : adapter la présentation ; B : adapter les activités et risques au cas métier retenu.
3. Ensemble : tester dans la VM RHEL et enregistrer les preuves.
4. Ensemble : répéter la démonstration en cinq minutes, remettre le ZIP et les exports.
