# Certificat local

Exécuter `bash scripts/generate-local-certificate.sh` dans la VM avant le premier `docker compose up`.

Le script crée :

- `smca-local-ca.crt` : autorité locale publique à importer dans Windows ;
- `smca-local-ca.key` : clé privée de l'autorité, à conserver uniquement dans la VM ;
- `smca-control.crt` : certificat présenté par Nginx ;
- `smca-control.key` : clé privée du serveur, à conserver uniquement dans la VM.

Copier uniquement `smca-local-ca.crt` vers Windows. Ne jamais copier ou partager
un fichier `.key`.

Les fichiers générés sont exclus de Git et du ZIP de livraison.

