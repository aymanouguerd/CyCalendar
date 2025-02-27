#!/bin/bash

echo "=== Installation de CyCalendar ==="
echo "Démarrage de l'installation..."

# Mise à jour des paquets
echo "Mise à jour du système..."
sudo apt-get update

# Installation des dépendances système
echo "Installation des dépendances système..."
sudo apt-get install -y \
    python3 \
    python3-pip \
    chromium-browser \
    chromium-chromedriver

# Création des répertoires nécessaires
echo "Création des répertoires..."
mkdir -p google
mkdir -p generated

# Installation des dépendances Python
echo "Installation des dépendances Python..."
python3 -m pip install --upgrade pip
pip3 install -r requirements.txt

# Configuration des permissions
echo "Configuration des permissions..."
sudo chmod +x /usr/bin/chromedriver

echo "Installation terminée !"
echo ""
echo "N'oubliez pas de :"
echo "1. Créer un fichier .env avec vos identifiants CY"
echo "2. Placer votre fichier client_secret.json dans le dossier google/"