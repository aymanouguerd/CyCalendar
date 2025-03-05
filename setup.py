#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import platform
import subprocess
import shutil
import getpass
from pathlib import Path

class CyCalendarInstaller:
    def __init__(self):
        self.os_type = platform.system()
        self.project_root = Path.cwd()
        self.env_path = self.project_root / '.env'
        self.google_dir = self.project_root / 'google'
        self.credentials_path = None
        self.mode = None

    def display_welcome(self):
        print("""
=================================================
    CyCalendar - Assistant d'Installation
=================================================
Bienvenue dans l'assistant d'installation de CyCalendar!
Ce script va vous guider à travers les étapes d'installation.
""")

    def select_installation_mode(self):
        print("\nVeuillez choisir un mode d'installation:")
        print("1. Mode Manuel (génération ICS simple)")
        print("2. Mode Automatique (synchronisation avec Google Calendar)")
        print("3. Mode Automatique avec GitHub Actions (mises à jour périodiques)")
        
        while True:
            choice = input("\nVotre choix (1/2/3): ")
            if choice in ["1", "2", "3"]:
                self.mode = int(choice)
                return
            print("Choix invalide. Veuillez réessayer.")

    def install_dependencies(self):
        print("\n[1/5] Installation des dépendances...")
        
        if self.os_type == "Linux":
            print("Installation des dépendances Linux...")
            try:
                subprocess.run(["bash", "setup.bash"], check=True)
                print("✅ Dépendances Linux installées avec succès.")
            except subprocess.CalledProcessError:
                print("⚠️ Erreur lors de l'installation des dépendances Linux.")
                print("Tentative d'installation manuelle des dépendances Python...")
                self.install_python_dependencies()
        
        elif self.os_type == "Windows":
            print("Installation des dépendances Windows...")
            try:
                subprocess.run(["setup.bat"], shell=True, check=True)
                print("✅ Dépendances Windows installées avec succès.")
            except subprocess.CalledProcessError:
                print("⚠️ Erreur lors de l'installation des dépendances Windows.")
                print("Tentative d'installation manuelle des dépendances Python...")
                self.install_python_dependencies()
        
        else:
            print(f"Système d'exploitation non reconnu: {self.os_type}")
            print("Tentative d'installation des dépendances Python uniquement...")
            self.install_python_dependencies()

    def install_python_dependencies(self):
        print("Installation des dépendances Python...")
        try:
            requirements_path = self.project_root / "requirements.txt"
            if not requirements_path.exists():
                with open(requirements_path, "w") as f:
                    f.write("selenium\nrequests\npython-dotenv\ngoogle-api-python-client\ngoogle-auth-httplib2\ngoogle-auth-oauthlib\npytz\nxvfbwrapper\n")
            
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
            print("✅ Dépendances Python installées avec succès.")
        except subprocess.CalledProcessError:
            print("❌ Échec de l'installation des dépendances Python.")
            sys.exit(1)

    def setup_environment(self):
        print("\n[2/5] Configuration du fichier .env...")
        
        # Demander les informations d'identification CY Tech
        cy_username = input("Entrez votre identifiant CY Tech (e-1erelettreprenom+nom): ")
        cy_password = getpass.getpass("Entrez votre mot de passe CY Tech: ")
        
        # Créer le fichier .env
        with open(self.env_path, 'w') as env_file:
            env_file.write(f"CY_USERNAME={cy_username}\n")
            env_file.write(f"CY_PASSWORD={cy_password}\n")
        
        print("✅ Fichier .env créé avec succès.")

    def setup_google_api(self):
        if self.mode == 1:
            print("\n[3/5] Mode manuel sélectionné - Étape Google API ignorée.")
            return True
            
        print("\n[3/5] Configuration de l'API Google Calendar...")
        print("""
Pour cette étape, vous devez:
1. Aller sur https://console.cloud.google.com/
2. Créer un nouveau projet
3. Activer l'API Google Calendar
4. Créer des identifiants OAuth 2.0
5. Télécharger le fichier JSON
""")
        
        print("Voulez-vous ouvrir le guide étape par étape dans votre navigateur?")
        choice = input("(o/n): ")
        if choice.lower() == 'o':
            self.open_browser("https://console.cloud.google.com/")
        
        print("\nUne fois le fichier JSON téléchargé, veuillez entrer son chemin complet:")
        credentials_path = input("Chemin du fichier JSON: ").strip('"\'')
        
        if not os.path.exists(credentials_path):
            print("❌ Le fichier spécifié n'existe pas.")
            return False
            
        # Création du dossier google s'il n'existe pas
        os.makedirs(self.google_dir, exist_ok=True)
        
        # Copie du fichier JSON dans le dossier google
        self.credentials_path = Path(credentials_path)
        dest_path = self.google_dir / self.credentials_path.name
        shutil.copy2(credentials_path, dest_path)
        
        print(f"✅ Fichier d'identification Google copié dans {dest_path}")
        return True

    def setup_github_actions(self):
        if self.mode != 3:
            print("\n[4/5] Mode GitHub Actions non sélectionné - Étape ignorée.")
            return
            
        print("\n[4/5] Configuration de GitHub Actions...")
        print("""
Pour configurer GitHub Actions, vous devez:
1. Forker le dépôt https://github.com/NayJi7/CyCalendar
2. Activer le workflow "Update Google Calendar"
3. Ajouter les secrets suivants dans votre dépôt:
   - CY_USERNAME: votre identifiant CY Tech
   - CY_PASSWORD: votre mot de passe CY Tech
   - GOOGLE_CREDENTIALS: contenu du fichier JSON d'identification Google
   - WORKFLOW_PAT: un token d'accès personnel GitHub
""")
        
        print("Voulez-vous ouvrir le guide étape par étape dans votre navigateur?")
        choice = input("(o/n): ")
        if choice.lower() == 'o':
            self.open_browser("https://github.com/NayJi7/CyCalendar")
            
        print("\nUne fois que vous avez forké le dépôt et que vous êtes prêt à configurer les secrets,")
        print("exécutez le script token_converter.py pour générer la valeur de GOOGLE_TOKEN_PICKLE.")
        
        # Vérifie si le script token_converter.py existe
        token_converter_path = self.project_root / "src" / "token_converter.py"
        if not token_converter_path.exists():
            print(f"⚠️ Le script token_converter.py n'a pas été trouvé à l'emplacement {token_converter_path}")
            print("Veuillez vérifier que vous êtes dans le dossier racine du projet.")
        else:
            print(f"Le script token_converter.py se trouve à: {token_converter_path}")
            print("Exécutez-le après avoir configuré et exécuté CyCalendar une première fois.")

    def run_cycalendar(self):
        print("\n[5/5] Exécution de CyCalendar...")
        
        try:
            subprocess.run([sys.executable, "cyCalendar.py"], check=True)
            print("✅ CyCalendar a été exécuté avec succès!")
            
            if self.mode == 1:
                print("\nVotre fichier ICS a été généré dans le dossier 'generated/'.")
                print("Vous pouvez maintenant l'importer manuellement dans Google Calendar.")
            elif self.mode == 2:
                print("\nVotre calendrier a été synchronisé avec Google Calendar.")
            else:
                print("\nVotre calendrier a été synchronisé avec Google Calendar.")
                print("Les mises à jour automatiques via GitHub Actions sont configurées.")
        except subprocess.CalledProcessError:
            print("❌ Une erreur s'est produite lors de l'exécution de CyCalendar.")
            print("Veuillez vérifier les messages d'erreur ci-dessus.")

    def open_browser(self, url):
        import webbrowser
        webbrowser.open(url)

    def run(self):
        try:
            self.display_welcome()
            self.select_installation_mode()
            self.install_dependencies()
            self.setup_environment()
            
            if self.mode > 1:
                success = self.setup_google_api()
                if not success:
                    print("❌ Configuration de l'API Google Calendar échouée.")
                    return
            
            if self.mode == 3:
                self.setup_github_actions()
                
            self.run_cycalendar()
            
            print("""
=================================================
    Installation terminée!
=================================================
""")
            
            if self.mode == 1:
                print("N'oubliez pas d'importer manuellement le fichier ICS dans Google Calendar.")
            elif self.mode == 2:
                print("Vous pouvez maintenant réexécuter CyCalendar.py quand vous souhaitez mettre à jour votre calendrier.")
            else:
                print("GitHub Actions mettra automatiquement à jour votre calendrier selon la planification configurée.")
                
        except KeyboardInterrupt:
            print("\n\nInstallation annulée par l'utilisateur.")
        except Exception as e:
            print(f"\n❌ Une erreur s'est produite: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    installer = CyCalendarInstaller()
    installer.run()