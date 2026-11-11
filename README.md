# SMCA — Mini-projet N°6

Application locale de cartographie des risques et d’analyse d’impact sur l’activité (BIA), réalisée pour un binôme. Interface en français, Python/Streamlit et SQLite ; aucun service externe nécessaire à l’exécution.

## Démarrer sous Windows

Installer Python 3.12 et extraire ce dossier, puis ouvrir PowerShell dans le dossier contenant `app.py` :

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m streamlit run app.py --server.address=127.0.0.1 --browser.gatherUsageStats=false
```

Ouvrir http://localhost:8501 puis cliquer **Charger la démonstration**. Aucune activation PowerShell ni modification de sa politique d’exécution n’est nécessaire. Arrêt : Ctrl+C.

## Fonctionnalités

- Interface sombre responsive avec identité visuelle, cartes interactives et formulaires harmonisés.
- Tableau de bord et matrice 5×5 initiale/résiduelle, effectifs par case.
- Création, modification et suppression des activités, risques et traitements ; liens protégés par clés étrangères.
- BIA : impacts financier, opérationnel et réputation ; RTO/RPO/MTPD en heures ; priorité de reprise.
- Registre : activité, actif, cause, conséquence, responsable, scores, recherche et filtre.
- Actions : stratégie, pilote, échéance, statut, retard, preuve obligatoire à la clôture.
- Export CSV UTF-8 pour chaque registre et rapport PDF avec matrice, BIA, risques et traitements.
- Données fictives chargées seulement sur demande, dans une base vide.

## Architecture et répartition

```text
Navigateur
   | HTTP local / tunnel SSH
Streamlit : app.py + smca/reports.py                 MEMBRE A
   | appels Python
Services : smca/service.py                         MEMBRE B
   | requêtes paramétrées et transactions
SQLite : data/smca.db ou volume Docker smca_data
```

| Fichiers | Responsable | Livrable |
|---|---|---|
| app.py, smca/reports.py, tests/test_ui.py | A (votre rôle) | Formulaires, dashboard, matrice et exports |
| smca/service.py, tests/test_service.py | B | Schéma, validations, BIA, calculs, persistance |
| Dockerfile, compose.yaml, docs/ | A + B | Déploiement, validation et soutenance |

Le contrat est la classe `Store` : `rows`, `save_activity`, `save_risk`, `save_treatment`, `delete`, `backup`. Les fonctions de sauvegarde créent sans `item_id`, modifient avec `item_id`. L’interface ne contient pas de SQL. Chaque formulaire sauvegarde dans une transaction ; la suppression d’un parent lié est refusée.

## Méthode pédagogique

Score = probabilité (1 à 5) × impact (1 à 5). Seuils : 1–4 faible, 5–9 modéré, 10–16 élevé, 17–25 critique. La couleur de la matrice exprime la classe de score, le nombre indique l’effectif des risques.

Criticité BIA = maximum des trois impacts. Priorité si criticité ≥ 4 ou RTO ≤ 4 h. RTO : délai cible de reprise ; RPO : ancienneté maximale des données perdues ; MTPD : durée d’interruption maximale tolérée. Vérification : 0 < RTO ≤ MTPD et RPO ≥ 0. RPO et RTO ne sont pas automatiquement ordonnés.

Les scores résiduels sont déclaratifs : terminer une action ne diminue pas automatiquement un score. Les seuils doivent être validés par les responsables métier. Ce prototype n’est ni une certification ISO 22301 ni un dispositif complet de gestion de crise. Il n’intègre pas d’authentification, de rôles ou de journal d’audit : usage pédagogique local, sans exposition publique.

## Docker

Générer d’abord le certificat HTTPS local :

```bash
bash scripts/generate-local-certificate.sh
```

```powershell
docker compose config -q
docker compose up -d --build
docker compose ps
docker compose logs --tail 50
docker compose down
```

L’application est servie par Nginx sur `127.0.0.1:8443` dans la VM. Avec le tunnel SSH et la configuration Windows décrits dans `docs/INSTALLATION.md`, l’adresse visible devient `https://smca-control.test`. La base persiste après `down` et reconstruction grâce au volume nommé. Ne pas utiliser `down -v` : cela détruit les données. L’image tourne sous un utilisateur non privilégié, sans capacités Linux, avec système de fichiers en lecture seule hors données et fichiers temporaires. Le port n’est publié que sur la boucle locale.

## Documentation et preuves

- [Installation Windows + VM RHEL](docs/INSTALLATION.md)
- [Validation de l’architecture et scénario de soutenance](docs/VALIDATION.md)
- [Organisation du binôme](docs/BINOME.md)
- [Guide complet GitHub du binôme](docs/GUIDE_BINOME_GITHUB.md)
- [Résultats de vérification](docs/VERIFICATION.md)
- `examples/` : exports du jeu fictif.

La capture du sujet porte le **n°12**, alors que l’échange et la demande désignent le **n°6**. Le sujet est identique : identification et cartographie des risques SMCA. Le numéro est à confirmer avec l’enseignant. La capture indique les dates **02/11/2026, 16/02/2026 et 30/11/2026 (finale)** ; la deuxième semble incohérente chronologiquement et n’est pas corrigée sans confirmation. Les deux étapes de validation et la limite de cinq minutes sont reprises dans les documents.
