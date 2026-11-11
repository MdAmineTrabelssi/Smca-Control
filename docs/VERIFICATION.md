# Vérification de la livraison — 09/11/2026

## Résultats réellement obtenus

Environnement : Windows, Python 3.14.0, Streamlit 1.67.0, Plotly 6.9.0, pandas 3.1.1, ReportLab 4.5.1, pytest 9.2.0 et pypdf 6.21.4. Les dépendances directes sont figées dans les fichiers requirements.

Commande exécutée depuis la racine du projet :

```text
python -m pytest -q --junitxml=docs/tests-results.xml
.................................................. [100%]
50 passed in 6.15s
```

| Vérification | Résultat |
|---|---|
| 25 combinaisons de la matrice et 8 bornes de classification | Réussi |
| Valeurs invalides, booléens et notes hors intervalle | Refusés |
| RTO/MTPD, RPO négatif, valeurs non finies et champs obligatoires | Contrôlés |
| Persistance SQLite, modification, suppression protégée et sauvegarde | Réussi |
| Échéance dépassée et preuve obligatoire à la clôture | Réussi |
| Chargement de démonstration sur base déjà remplie | Refusé |
| CSV : accents, séparateurs, retours ligne et formules neutralisées | Réussi |
| PDF : base vide, données fictives, texte long et caractères XML | Réussi |
| Interface : base vide, démonstration et navigation dans 5 écrans | Réussi via AppTest |
| Interface : création d’activité et validation d’une saisie vide | Réussi via AppTest |
| Interface : création de risque, traitement et clôture avec preuve | Réussi via AppTest |
| Refonte frontend : thème, cartes, navigation, formulaires et matrice | 50 tests réussis après modification |
| Serveur Streamlit réel : santé `ok` et page HTTP 200 | Réussi ; serveur temporaire arrêté après test |
| `python -m pip check` | Aucune dépendance cassée |
| `docker compose config -q` | Configuration acceptée |
| Configuration HTTPS Nginx et nom local `smca-control.test` | Fichiers préparés ; certificat et confiance à valider dans la VM/Windows |
| Rapport PDF exemple : rendu des trois pages et inspection visuelle | Vérifié ; sections séparées et fiches non coupées |

Les tests d’interface ont d’abord été bloqués par les restrictions sur les connexions locales de l’environnement de travail. Ils ont ensuite tous réussi avec ces connexions autorisées. Aucun contournement n’est requis dans le code livré.

## Limites de validation

- Le moteur Docker est indisponible sur ce poste. La commande `docker info` ne trouve pas le moteur Linux ; le démarrage de Docker Desktop échoue car son installation n’est pas trouvée. La construction et l’exécution des deux Dockerfiles ne sont donc **pas validées ici**.
- Le proxy Nginx, le certificat généré dans RHEL et sa confiance dans Chrome doivent être validés sur le poste de démonstration.
- Aucune VM RHEL ni souscription Red Hat n’a été créée ou configurée. Suivre INSTALLATION.md puis compléter la recette VALIDATION.md dans la VM.
- L’image est prévue pour Python 3.12 ; les tests locaux ont été exécutés sous Python 3.14, pas sous Python 3.12. Le `Dockerfile.test` permet de vérifier la version cible.
- AppTest vérifie les composants et interactions Streamlit ; aucune validation visuelle du rendu navigateur de l’application n’a été effectuée. La vérification visuelle porte sur le PDF.
- Les données sont fictives. Les seuils BIA et les niveaux de risque sont pédagogiques et doivent être validés par l’enseignant.

## Preuves incluses

`tests-results.xml` contient le résultat JUnit des 50 tests. `examples/rapport_demo.pdf` et les trois CSV proviennent du même jeu de démonstration. Les bases utilisées par les tests sont temporaires et ne sont pas livrées comme données métier.
