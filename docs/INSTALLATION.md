# Installation Windows et VM RHEL 9.x

## 1. Préparer Windows

Dans le Gestionnaire des tâches > Performances > Processeur, vérifier « Virtualisation : activée ». Sinon, activer Intel VT-x/AMD-V dans le firmware du PC. Installer un hyperviseur compatible avec votre machine (VMware Workstation, VirtualBox ou Hyper-V), avec une licence valide selon ses conditions. Ne pas installer plusieurs hyperviseurs pour ce projet.

Installer Python 3.12 et Git depuis leurs sites officiels. VS Code est facultatif. Vérifier dans PowerShell :

```powershell
py -3.12 --version
git --version
```

Extraire le ZIP dans un dossier accessible en écriture. Se placer dans `smca`, à côté de `app.py`, et suivre les commandes du README. Si `py` n’existe pas mais `python --version` affiche Python 3.12+, remplacer `py -3.12` par `python`. Internet est nécessaire à la première installation des bibliothèques.

## 2. Créer la VM du projet

Créer un compte Red Hat Developer et obtenir une souscription valide adaptée à l’usage pédagogique. Télécharger l’ISO RHEL 9.x depuis Red Hat ; le document enseignant mentionne RHEL 9.5 comme modèle, sans imposer clairement cette version exacte. Confirmer ce point avant la soutenance.

Configuration de départ : **2 vCPU, 4 Go RAM, 30 Go disque, réseau NAT**. Installer le profil minimal, créer un utilisateur `etudiant` avec droits d’administration, choisir un mot de passe robuste et terminer l’installation. Noter l’adresse IP de la VM avec `ip -br address`.

Dans la VM :

```bash
sudo subscription-manager register
sudo subscription-manager status
sudo dnf upgrade --refresh -y
sudo dnf install -y git unzip openssh-server firewalld dnf-plugins-core
sudo systemctl enable --now sshd firewalld
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --reload
getenforce
```

Saisir les identifiants de souscription à l’invite, jamais dans un script livré. Avec Simple Content Access, le statut de souscription peut différer ; vérifier surtout que `dnf` accède aux dépôts. Garder SELinux en mode `Enforcing`. Redémarrer si les mises à jour du noyau le nécessitent. Faire un instantané VM après installation et mises à jour.

## 3. Installer Docker Engine et Compose dans RHEL

Les commandes suivantes suivent la documentation officielle Docker pour RHEL. Docker CE provient du dépôt Docker ; il ne s’agit pas du moteur Podman fourni par Red Hat. Dans une VM déjà équipée, vérifier les conflits de paquets selon la documentation avant d’installer ; ne pas supprimer aveuglément un environnement existant.

```bash
sudo dnf config-manager --add-repo https://download.docker.com/linux/rhel/docker-ce.repo
sudo dnf install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo systemctl enable --now docker
sudo docker run --rm hello-world
sudo docker compose version
```

Comparer l’empreinte GPG présentée à celle publiée par Docker avant de l’accepter. Les commandes utilisent `sudo` : aucun ajout au groupe privilégié `docker` n’est requis.

## 4. Transférer et lancer

Depuis Windows, remplacer `IP_VM` par l’adresse de la VM :

```powershell
scp .\SMCA-mini-projet.zip etudiant@IP_VM:~/
ssh etudiant@IP_VM
```

Si le NAT de l’hyperviseur ne permet pas cet accès, définir une redirection **127.0.0.1:2222 → VM:22**, puis utiliser `scp -P 2222` et `ssh -p 2222` avec `etudiant@127.0.0.1`.

Dans la VM :

```bash
mkdir -p ~/projets/smca-livraison
unzip ~/SMCA-mini-projet.zip -d ~/projets/smca-livraison
cd ~/projets/smca-livraison/smca
bash scripts/generate-local-certificate.sh
sudo docker compose config -q
sudo docker compose up -d --build
sudo docker compose ps
curl --cacert certs/smca-local-ca.crt --resolve smca-control.test:8443:127.0.0.1 https://smca-control.test:8443/healthz
```

Le résultat santé attendu est `ok`. Le volume `smca_smca_data` conserve SQLite. Le proxy HTTPS expose le port 8443 uniquement sur la boucle locale de la VM ; il ne faut pas ouvrir ce port dans firewalld.

Copier seulement l'autorité locale publique vers Windows :

```powershell
scp etudiant@IP_VM:~/projets/smca-livraison/smca/certs/smca-local-ca.crt "$HOME\Desktop\smca-local-ca.crt"
```

Ne jamais copier un fichier `.key`. Dans un PowerShell **exécuté en tant qu'administrateur**, importer l'autorité locale dans le magasin de confiance de Windows :

```powershell
certutil -addstore -f Root "$HOME\Desktop\smca-local-ca.crt"
```

Ouvrir ensuite, toujours comme administrateur, le fichier suivant dans le Bloc-notes :

```powershell
notepad C:\Windows\System32\drivers\etc\hosts
```

Ajouter cette ligne, enregistrer et fermer :

```text
127.0.0.1 smca-control.test
```

Pour afficher l’application, ouvrir un PowerShell Windows et conserver le tunnel actif :

```powershell
ssh -N -L 443:127.0.0.1:8443 etudiant@IP_VM
```

Avec une redirection NAT SSH sur le port 2222 :

```powershell
ssh -p 2222 -N -L 443:127.0.0.1:8443 etudiant@127.0.0.1
```

Ouvrir ensuite **https://smca-control.test**. Le navigateur affiche le nom SMCA Control, HTTPS et aucune alerte lorsque le certificat a été importé correctement. Si le port Windows 443 est déjà utilisé, utiliser `-L 8443:127.0.0.1:8443` et ouvrir `https://smca-control.test:8443`.

Cette autorité est réservée à cette démonstration locale. Pour la retirer plus tard, ouvrir `certlm.msc`, aller dans **Autorités de certification racines de confiance > Certificats** et supprimer uniquement `SMCA Control Local CA` après avoir vérifié son nom.

## 5. Vérifier la persistance

Charger les données fictives, créer une activité nommée « Test persistance », puis :

```bash
sudo docker compose restart
sudo docker compose ps
```

Actualiser le navigateur : l’activité doit rester présente. Tester également `sudo docker compose down` suivi de `sudo docker compose up -d`. Ne jamais ajouter `-v` lors d’un arrêt normal.

## 6. Sauvegarder et restaurer

Sauvegarde cohérente par l’API SQLite (copie dans `/tmp`, puis extraction) :

```bash
mkdir -p backups
sudo docker compose exec -T app python -c "from smca.service import Store; Store().backup('/tmp/smca-backup.db')"
sudo docker compose cp app:/tmp/smca-backup.db backups/smca-backup.db
```

Conserver une copie datée hors VM. Pour restaurer, sauvegarder d’abord la base actuelle, arrêter l’application, remplacer la base via un conteneur ponctuel qui monte le même volume, puis redémarrer :

```bash
sudo docker compose stop app
sudo docker compose run --rm -T app python -c "import sys; from pathlib import Path; Path('/app/data/smca.db').write_bytes(sys.stdin.buffer.read())" < backups/smca-backup.db
sudo docker compose up -d
```

Cette restauration remplace les données. Utiliser uniquement une sauvegarde de cette version, vérifier son intégrité avant restauration (`PRAGMA integrity_check` via Python/SQLite) et conserver la sauvegarde précédente.

## 7. Tests dans la VM

Le conteneur de production ne contient pas pytest. Exécuter les tests dans une image de test temporaire, depuis le dossier du projet :

```bash
sudo docker build -f Dockerfile.test -t smca-tests .
sudo docker run --rm smca-tests
```

## 8. Sécurisation et dépannage

- Maintenir RHEL à jour, conserver SELinux et firewalld actifs. Ne pas désactiver SELinux pour résoudre un problème.
- Utiliser des clés SSH ; tester la connexion par clé avant de désactiver les mots de passe. Ne pas autoriser la connexion SSH directe de root.
- Ne pas publier cette application sans authentification sur Internet. Le tunnel SSH assure l’accès à la démonstration.
- `docker compose logs --tail 100` : diagnostic de démarrage. `docker info` : disponibilité du moteur.
- « Port déjà utilisé » : arrêter l’autre instance ou changer uniquement le port hôte dans Compose.
- Permission SQLite : conserver le volume nommé ; l’utilisateur du conteneur est UID 10001. Ne pas substituer un montage hôte arbitraire sans permissions et contexte SELinux adaptés.
- Erreur réseau pip/dnf : vérifier DNS, accès Internet et éventuel proxy ; ne pas désactiver TLS.
- Absence de données : vérifier `SMCA_DB` et le volume utilisé ; une base locale Windows et une base Docker sont distinctes.

## Sources officielles consultées le 09/11/2026

- Docker Engine sur RHEL : https://docs.docker.com/engine/install/rhel/
- Plugin Compose : https://docs.docker.com/compose/install/linux/
- Tests Streamlit : https://docs.streamlit.io/develop/api-reference/app-testing
- Python Windows : https://www.python.org/downloads/windows/
- Red Hat Developer : https://developers.redhat.com/products/rhel/overview

La VM et la souscription doivent être configurées sur le poste de soutenance. Ce guide ne prétend pas que la VM a été créée par la livraison.
