#!/bin/bash

echo ""
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

# Installation des dépendances Python - sans environnement virtuel
echo "Installation des dépendances Python..."
# Installation avec le paramètre pour outrepasser la protection système
python3 -m pip install --upgrade pip --break-system-packages
# Installation des dépendances avec le paramètre pour outrepasser la protection système
python3 -m pip install -r requirements.txt --break-system-packages

# Configuration des permissions
echo "Configuration des permissions..."
sudo chmod +x /usr/bin/chromedriver

echo ""
echo "Installation terminée !"