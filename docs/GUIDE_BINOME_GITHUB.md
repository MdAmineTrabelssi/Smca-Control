# Guide complet GitHub et travail en binôme

Ce guide répartit le projet entre le membre A, responsable de l’interface, et le membre B, responsable de la logique métier et de SQLite. Les deux membres utilisent des branches séparées et intègrent leur travail avec des Pull Requests.

## 1. Premier envoi du projet par le membre A

Se placer dans le dossier qui contient directement `app.py`, `compose.yaml`, `smca/` et `tests/` :

```bash
cd ~/projets/smca-v3/smca
pwd
ls
```

Ne pas exécuter `echo "# Smca-Control" >> README.md` : le README complet existe déjà et cette commande ajouterait une ligne inutile à chaque exécution.

Configurer l’identité Git, une seule fois sur ce poste :

```bash
git config --global user.name "MdAmineTrabelssi"
git config --global user.email "ADRESSE_GITHUB"
```

Remplacer `ADRESSE_GITHUB` par l’adresse associée au compte GitHub, ou par l’adresse privée `...@users.noreply.github.com` fournie dans les paramètres GitHub.

Initialiser et contrôler le contenu avant le commit :

```bash
git init
git branch -M main
git add .
git status
```

Le statut ne doit pas contenir `.venv`, `data/smca.db`, `certs/smca-control.key`, `.env` ou une autre donnée sensible. Si l’un de ces fichiers apparaît, ne pas continuer avant de corriger `.gitignore`.

Créer le commit :

```bash
git commit -m "feat: version initiale de SMCA Control"
```

Ajouter le dépôt distant :

```bash
git remote add origin https://github.com/MdAmineTrabelssi/Smca-Control.git
git remote -v
```

Si `origin` existe déjà :

```bash
git remote set-url origin https://github.com/MdAmineTrabelssi/Smca-Control.git
```

Envoyer le projet :

```bash
git push -u origin main
```

GitHub n’accepte pas le mot de passe du compte pour Git en HTTPS. Utiliser la connexion proposée par Git Credential Manager ou un Personal Access Token limité au dépôt si le terminal le demande. Ne jamais enregistrer le token dans un fichier du projet.

Si le dépôt GitHub contient déjà un commit créé depuis le site, ne pas forcer le push. Synchroniser d’abord :

```bash
git pull --rebase origin main
git push -u origin main
```

En cas de conflit, lire la section 9 avant de poursuivre. Ne pas utiliser `git push --force` sur `main`.

## 2. Donner accès au membre B

Sur GitHub, le propriétaire ouvre le dépôt, puis **Settings > Collaborators > Add people** et invite le compte GitHub du membre B. Le membre B accepte l’invitation avant de cloner un dépôt privé.

Dans **Settings > Branches**, il est recommandé de protéger `main` :

- demander une Pull Request avant fusion ;
- demander un test GitHub Actions réussi ;
- empêcher les suppressions et les force-push sur `main`.

## 3. Installation du membre B

Le membre B installe Git et Python 3.12, puis configure son identité :

```bash
git config --global user.name "NOM_MEMBRE_B"
git config --global user.email "ADRESSE_GITHUB_MEMBRE_B"
```

Il clone le dépôt :

```bash
git clone https://github.com/MdAmineTrabelssi/Smca-Control.git
cd Smca-Control
```

Il vérifie le projet :

```bash
git remote -v
git status
git branch --show-current
```

Sous Windows PowerShell :

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
```

Sous RHEL/Linux :

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m pytest -q
```

Le résultat attendu est `50 passed` avant toute modification.

## 4. Créer la branche backend

Le membre B ne travaille pas directement sur `main` :

```bash
git switch -c backend
git status
```

Si la branche distante `backend` existe déjà :

```bash
git fetch origin
git switch --track origin/backend
```

Le membre A peut utiliser une branche distincte :

```bash
git switch -c frontend
```

## 5. Tâches complètes du membre B

Le membre B étudie et maintient principalement :

- `smca/service.py` : calculs, validations et accès SQLite ;
- `tests/test_service.py` : tests métier ;
- `Dockerfile`, `compose.yaml` et les procédures de sauvegarde avec le membre A ;
- la cohérence des données affichées par `app.py`.

### 5.1 Modèle SQLite

Vérifier et expliquer les tables :

- `activities` : activité, responsable, dépendances, impacts, RTO, RPO et MTPD ;
- `risks` : activité liée, actif, cause, conséquence, responsable et scores ;
- `treatments` : risque lié, action, stratégie, pilote, échéance, statut et preuve.

Vérifier les relations :

```text
Une activité possède plusieurs risques.
Un risque possède plusieurs traitements.
```

Les clés étrangères doivent empêcher la suppression d’une activité ou d’un risque encore utilisé.

### 5.2 Calcul du risque

Vérifier la formule et les 25 combinaisons :

```text
Score = probabilité × impact
Faible : 1 à 4
Modéré : 5 à 9
Élevé : 10 à 16
Critique : 17 à 25
```

Le score résiduel reste une estimation saisie après traitement ; il n’est pas réduit automatiquement lors de la clôture d’une action.

### 5.3 Règles BIA

Vérifier :

```text
0 < RTO ≤ MTPD
RPO ≥ 0
Impacts compris entre 1 et 5
```

La priorité est calculée à partir de la criticité et du RTO. Le membre B doit documenter toute modification de cette convention.

### 5.4 Traitements

Tester les quatre stratégies : réduire, éviter, transférer et accepter. Une action ne peut pas passer à `Terminé` sans preuve. Vérifier aussi les échéances dépassées.

### 5.5 Persistance et sauvegarde

Vérifier qu’un redémarrage conserve les données. Tester la fonction `Store.backup()` avec une base temporaire. Ne jamais committer une base de données réelle.

### 5.6 Tests backend

Pendant le développement :

```bash
python -m pytest tests/test_service.py -q
```

Avant chaque push :

```bash
python -m pytest -q
```

## 6. Méthode de travail quotidienne du membre B

Avant de commencer une nouvelle session :

```bash
git switch backend
git fetch origin
git rebase origin/main
```

Modifier uniquement les fichiers nécessaires, puis vérifier :

```bash
git status
git diff
python -m pytest -q
```

Créer des commits courts et explicites :

```bash
git add smca/service.py tests/test_service.py
git commit -m "feat: renforcer les validations BIA"
```

Autres exemples :

```text
fix: corriger le calcul du niveau résiduel
test: couvrir les suppressions protégées
docs: expliquer la sauvegarde SQLite
```

Envoyer la branche :

```bash
git push -u origin backend
```

Après le premier push, `git push` suffit pour les commits suivants.

## 7. Pull Request du membre B

Sur GitHub, ouvrir **Pull requests > New pull request**, choisir :

```text
base: main
compare: backend
```

La description doit indiquer :

- le problème traité ;
- les fichiers modifiés ;
- le comportement avant et après ;
- la commande de test et son résultat ;
- toute limite ou décision métier à valider.

Le membre A relit le code et vérifie que GitHub Actions est vert. Les corrections demandées sont ajoutées dans la même branche `backend`, puis poussées ; la Pull Request se met à jour automatiquement.

## 8. Intégration par le membre A

Le membre A ne fusionne que lorsque :

- les tests GitHub Actions réussissent ;
- la logique métier est comprise ;
- l’interface fonctionne avec le backend ;
- aucun secret, certificat privé ou fichier SQLite n’est ajouté.

Après fusion sur GitHub, les deux membres synchronisent :

```bash
git switch main
git pull --ff-only origin main
```

Puis chacun recrée sa branche depuis la nouvelle version de `main`, ou rebase sa branche active.

## 9. Résoudre un conflit sans perdre le travail

Pendant un rebase, Git indique les fichiers en conflit :

```bash
git status
```

Ouvrir chaque fichier, choisir le contenu correct et retirer les marqueurs :

```text
<<<<<<<
=======
>>>>>>>
```

Puis :

```bash
git add FICHIER_CORRIGE
git rebase --continue
```

Pour annuler le rebase et revenir à l’état initial :

```bash
git rebase --abort
```

Ne jamais utiliser `git reset --hard` ou `git push --force` pour résoudre un conflit de ce projet partagé.

## 10. Déployer une version fusionnée dans la VM

Avant la mise à jour, sauvegarder SQLite :

```bash
cd ~/projets/smca-v3/smca
mkdir -p backups
sudo docker compose exec -T app python -c "from smca.service import Store; Store().backup('/tmp/smca-backup.db')"
sudo docker compose cp app:/tmp/smca-backup.db backups/smca-backup.db
```

Mettre ensuite le code à jour :

```bash
git switch main
git pull --ff-only origin main
```

Si le certificat local n’existe pas :

```bash
bash scripts/generate-local-certificate.sh
```

Reconstruire et vérifier :

```bash
sudo docker compose up -d --build
sudo docker compose ps
curl --cacert certs/smca-local-ca.crt --resolve smca-control.test:8443:127.0.0.1 https://smca-control.test:8443/healthz
```

Le résultat attendu est `ok`. Vérifier ensuite `https://smca-control.test` depuis Windows avec le tunnel SSH actif.

## 11. Règles de sécurité du dépôt

Ne jamais committer :

- les mots de passe, tokens GitHub ou identifiants Red Hat ;
- `certs/smca-control.key` ;
- `.env` ;
- `.venv/` ;
- `data/smca.db` ou une sauvegarde contenant des données réelles ;
- des informations personnelles dans les données de démonstration.

Avant chaque push :

```bash
git status
git diff --cached
```

## 12. Répartition finale pour la soutenance

| Sujet | Membre A | Membre B |
|---|---:|---:|
| Interface, navigation et thème | Responsable | Relecture |
| Dashboard et matrice | Responsable | Fournit les scores |
| Exports PDF/CSV | Responsable | Vérifie les données |
| SQLite et relations | Relecture | Responsable |
| BIA et validations | Interface | Responsable |
| Risques et traitements | Interface | Logique métier |
| Docker, HTTPS et persistance | Ensemble | Ensemble |
| Tests et démonstration | Ensemble | Ensemble |

Chaque membre doit être capable de lancer l’application complète, expliquer son propre travail et résumer le travail de l’autre.

