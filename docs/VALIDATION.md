# Les deux livrables de validation

## Séance 1 — Architecture et validation technique

**Problème traité :** disposer d’un registre partagé de risques d’interruption, relier ces risques aux activités et prioriser les actions de continuité.

**Choix :** une application Streamlit unique, des fonctions Python séparées et une base SQLite locale. Le navigateur ne parle pas directement à la base. SQLite convient au volume pédagogique et évite un serveur de base supplémentaire. Pour un usage réel fortement concurrent, envisager PostgreSQL, authentification, gestion des rôles et audit.

**Infrastructure :** PC Windows → tunnel SSH → proxy HTTPS Nginx → Streamlit/Python → volume SQLite dans la VM RHEL 9.x. L’adresse de démonstration est `https://smca-control.test` avec un certificat local importé dans Windows. Python 3.12 dans le conteneur est indépendant du Python système de RHEL.

**Modèle relationnel :** une activité possède plusieurs risques ; un risque possède plusieurs traitements. L’actif est décrit dans le risque ; les dépendances sont décrites dans la BIA. Les suppressions de parents liés sont bloquées. Les identifiants A/R/T permettent de retrouver les liens dans le rapport PDF.

**Points à faire valider :** numéro du sujet, version RHEL attendue, dates de passage, seuils de scoring, convention BIA, scénario métier et périmètre du prototype. La capture donne deux étapes de validation et une présentation finale limitée à cinq minutes.

## Séance 2 — Démonstration publique (5 minutes)

| Temps | Qui | Action et explication |
|---|---|---|
| 0:00–0:35 | A | Présenter le problème, l’architecture et la répartition |
| 0:35–1:15 | B | Montrer BIA « Prise de commandes » : RTO 4 h, RPO 1 h, MTPD 24 h |
| 1:15–2:05 | A | Afficher la matrice ; expliquer ERP : 4 × 5 = 20, critique |
| 2:05–2:55 | B | Ouvrir un traitement, passer à En cours ; expliquer pilote et échéance |
| 2:55–3:35 | A | Basculer sur le résiduel estimé : ERP 2 × 4 = 8, modéré |
| 3:35–4:20 | A | Télécharger PDF et CSV ; montrer les relations et les résultats |
| 4:20–5:00 | B | Montrer tests et conteneur sain, puis persistance après redémarrage préparé |

Préparer les onglets et les commandes avant le passage. Les estimations résiduelles ne prouvent pas l’efficacité d’une action : il faut un exercice de reprise et une preuve.

## Recette à réaliser sur la VM

1. Base vide : dashboard sans erreur et formulaires guidés.
2. Démonstration : 2 activités, 5 risques, 5 actions ; ERP score 20 et résiduel 8.
3. Saisie invalide : nom vide ou RTO > MTPD refusé sans ajout.
4. Modifier un risque : matrice et registre reflètent le nouveau score.
5. Terminer un traitement sans preuve : refus ; avec preuve : accepté.
6. Supprimer une activité liée : refus ; supprimer d’abord ses enfants si nécessaire.
7. Exporter : CSV lisible avec accents ; PDF sans chevauchement et avec les trois registres.
8. Redémarrer le conteneur : données conservées.
9. Sauvegarder et restaurer une base de test : contenu retrouvé.

Conserver les captures `docker compose ps`, résultats pytest et dashboard dans le rapport de soutenance. Le fichier VERIFICATION distingue les vérifications réellement exécutées des étapes restant à réaliser sur la VM.
