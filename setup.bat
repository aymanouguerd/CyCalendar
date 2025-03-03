@echo off
echo === Installation de CyCalendar pour Windows ===
echo Démarrage de l'installation...

echo.
echo Installation des dépendances Python...
echo Cette opération peut prendre plusieurs minutes selon votre connexion internet
pip install --upgrade pip
pip install -r requirements.txt

echo.
echo Création des répertoires nécessaires...
if not exist google mkdir google
if not exist generated mkdir generated

echo.
echo Installation terminée !
echo.
echo Pour utiliser CyCalendar :
echo 1. Créez un fichier .env à la racine du projet avec vos identifiants CY
echo    CY_USERNAME=votre_nom_utilisateur
echo    CY_PASSWORD=votre_mot_de_passe
echo 2. Exécutez "python cyCalendar.py"
echo.
echo Note : Vous devez avoir Chrome ou Edge installé pour que le script fonctionne.
pause