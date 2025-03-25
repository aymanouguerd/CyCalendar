# CyCalendar

CyCalendar est un outil qui synchronise automatiquement votre emploi du temps CY Tech avec Google Calendar.

## Fonctionnalités

- Authentification automatique avec le système CY Tech
- Récupération de votre emploi du temps
- Conversion au format ICS
- Synchronisation avec Google Calendar
- Formatage intelligent des événements :
  - Suppression des doublons de préfixes (ex: "CM CM" devient "CM")
  - Correction des caractères spéciaux
  - Coloration automatique : bleu pour les CM, rouge doux pour les TD
- Stockage des fichiers ICS générés dans le dossier `generated/`

## Configuration requise

- Python 3.x
- Les dépendances listées dans `requirements.txt`
- Un compte Google avec accès à l'API Google Calendar
- Des identifiants OAuth2 Google (fichier `client_secret_*.json`)

## Installation

1. Clonez ce dépôt
2. Installez les dépendances :
   ```bash
   pip install -r requirements.txt
   ```
3. Placez votre fichier d'identifiants OAuth2 Google (`client_secret_*.json`) dans le dossier `google/`

## Utilisation

1. Exécutez le script :
   ```bash
   python cyCalendar.py
   ```
2. Suivez les étapes d'authentification CY Tech
3. Le programme créera automatiquement un calendrier "Cours CY" dans votre Google Calendar et y importera vos cours

## Structure des dossiers

- `generated/` : Stockage des fichiers ICS générés
- `google/` : Stockage des fichiers d'authentification Google (credentials et token)
- `src/` : Code source du projet

## Notes

- Le calendrier est automatiquement recréé à chaque synchronisation pour éviter les doublons
- Les CM sont colorés en bleu (#4a4aff)
- Les TD sont colorés en rouge clair (#FF6666)
- Le calendrier lui-même est coloré en bleu (#2660aa)