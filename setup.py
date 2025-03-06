import os
import sys
import platform
import subprocess
import getpass
from time import sleep
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
        print("3. Mode Automatique et périodique (mises à jour périodiques avec GitHub Actions)")
        
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
                with open(".setup.log", "w") as f:
                    f.write("1")
            except subprocess.CalledProcessError:
                print("⚠️ Erreur lors de l'installation des dépendances Linux.")
                print("Tentative d'installation manuelle des dépendances Python...")
                self.install_python_dependencies()
        
        elif self.os_type == "Windows":
            print("Installation des dépendances Windows...")
            try:
                subprocess.run(["setup.bat"], shell=True, check=True)
                print("✅ Dépendances Windows installées avec succès.")
                with open(".setup.log", "w") as f:
                    f.write("1")
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
        with open(".setup.log", "w") as f:
            f.write("2")

    def setup_google_api(self):
        if self.mode == 1:
            print("\n[3/5] Mode manuel sélectionné - Étape Google API ignorée.")
            return True
            
        print("\n[3/5] Configuration de l'API Google Calendar...")
        print("""
Pour cette étape, vous devez:
1. Aller sur https://console.cloud.google.com/
2. Créer un nouveau projet
3. Activer l'API Google Calendar en la cherchant dans la barre de recherche
4. Allez sur l'écran de consentement OAuth dans la barre à gauche puis Audience puis sous Utilisateurs tests cliquez sur add users et ajoutez votre email
5. Cliquez sur les 3 barres tout en haut à gauche puis survolez API et services et cliquez sur identifiants
6. Cliquez sur créer des identifiants puis sélectionnez ID client OAuth (Type d'app : App de bureau, )
6. Télécharger le fichier JSON (tout à droite dans la catégorie Codes secrets du client)
(N'hésitez pas à consulter le Readme pour plus de détails et d'illustrations)
""")
        
        while True:
            print("\nUne fois le fichier JSON téléchargé, veuillez entrer son chemin complet:")
            credentials_path = input("Chemin du fichier JSON: ").strip('"\'')
            
            if os.path.exists(credentials_path):
                credentials_path = os.path.expanduser(credentials_path)
                if not Path(credentials_path).name.lower().startswith('client_secret_') or not Path(credentials_path).name.lower().endswith('.apps.googleusercontent.com.json'):
                    print("❌ Le fichier ne semble pas être un fichier d'identification Google OAuth valide.")
                    print("Le nom du fichier doit commencer par 'client_secret_' et se terminer par '.apps.googleusercontent.com.json'")
                    continue
                break
            
            print("❌ Le fichier spécifié n'existe pas. Veuillez réessayer.")
            
        # Création du dossier google s'il n'existe pas
        try:
            os.makedirs(self.google_dir, exist_ok=True)
        except Exception as e:
            print(f"❌ Impossible de créer le dossier google: {e}")
            return False
        
        # Copie du fichier JSON dans le dossier google
        self.credentials_path = Path(credentials_path)
        dest_path = self.google_dir / self.credentials_path.name
        
        # Éviter de copier si le fichier est déjà au bon endroit
        if self.credentials_path.resolve() != dest_path.resolve():
            try:
                # Lecture du fichier source
                with open(credentials_path, 'rb') as source:
                    content = source.read()
                
                # Écriture dans le fichier destination
                with open(dest_path, 'wb') as target:
                    target.write(content)
                
                print(f"✅ Fichier d'identification Google copié dans {dest_path}")
            except PermissionError:
                print("❌ Erreur de permission lors de la copie du fichier.")
                print("Essayez de copier manuellement le fichier dans le dossier 'google'")
                print(f"Source: {credentials_path}")
                print(f"Destination: {dest_path}")
            
                choice = input("Avez-vous copié manuellement le fichier? (y/n): ")
                if choice.lower() != 'y':
                    return False
            except Exception as e:
                print(f"❌ Erreur lors de la copie du fichier: {e}")
                return False
        else:
            print(f"✅ Le fichier d'identification Google est déjà dans le bon dossier")
    
        try:
            with open(".setup.log", "w") as f:
                f.write("3")
        except Exception as e:
            print(f"⚠️ Impossible d'écrire dans le fichier .setup.log: {e}")
        
        return True

    def install_gh_cli(self):
        try:
            # Check if gh is already installed
            subprocess.run(["gh", "--version"], check=True, capture_output=True)
            print("✅ GitHub CLI est déjà installé!")
            return
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("Installation de GitHub CLI...")
            try:
                if self.os_type == "Linux":
                    # Pour les distributions basées sur Debian/Ubuntu
                    subprocess.run(["curl", "-fsSL", "https://cli.github.com/packages/githubcli-archive-keyring.gpg", "|", "sudo", "dd", "of=/usr/share/keyrings/githubcli-archive-keyring.gpg"], shell=True)
                    subprocess.run(["echo", "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main", "|", "sudo", "tee", "/etc/apt/sources.list.d/github-cli.list"], shell=True)
                    subprocess.run(["sudo", "apt", "update"])
                    subprocess.run(["sudo", "apt", "install", "gh", "-y"])
                elif self.os_type == "Windows":
                    subprocess.run(["winget", "install", "--id", "GitHub.cli"])
                else:
                    print(f"⚠️ Installation manuelle requise pour {self.os_type}.")
                    print("Veuillez installer GitHub CLI depuis: https://cli.github.com/")
                    input("Appuyez sur Entrée une fois que vous avez installé GitHub CLI...")
                
                # Verify installation
                subprocess.run(["gh", "--version"], check=True)
                print("✅ GitHub CLI installé avec succès!")
            except subprocess.CalledProcessError:
                print("❌ Erreur lors de l'installation de GitHub CLI")
                print("Veuillez l'installer manuellement depuis: https://cli.github.com/")
                input("Appuyez sur Entrée une fois que vous avez installé GitHub CLI...")

    def setup_github_actions(self):
        if self.mode != 3:
            print("\n[4/5] Mode GitHub Actions non sélectionné - Étape ignorée.")
            return
        
        # Installation de GitHub CLI
        self.install_gh_cli()
        
        hasforked = input("Avez vous déjà forké le repo ? (y/n): ")
        if hasforked.lower() != 'y':
            print("Veuillez recommencer dans un fork de ce repo (https://github.com/NayJi7/CyCalendar) et non dans un clone. Le repo doit vous appartenir (fork) pour continuer.")
            sys.exit(1)
            
        print("\n[4/5] Configuration de GitHub Actions...")
        try:
            # Check if already logged in
            try:
                subprocess.run(["gh", "auth", "status"], check=True, capture_output=True)
                print("✅ Already logged in to GitHub!")
                token = subprocess.run(["gh", "auth", "token"], check=True, capture_output=True, text=True).stdout.strip()
            except subprocess.CalledProcessError:
                # Login with token only if not already logged in
                print("""
Pour configurer GitHub Actions, vous devez:
1. Allez sur votre compte GitHub et cliquez sur votre avatar en haut à droite
2. Sélectionnez Settings
3. Descendez et cliquez sur Developer settings tout en bas à gauche
4. Sélectionnez Personal access tokens puis Fine-grained tokens
5. Cliquez sur Generate new token
6. Donnez un nom à votre token (ex: "CyCalendar Workflow")
7. Choisissez une durée d'expiration (No expiration ou un an)
8. Dans repository access selectionnez All repositories ou Only select repositories (CyCalendar)
9. Sélectionnez les permissions suivantes en read/write:
    - repo: Actions, Contents, Workflows, Pull Requests, Secrets
10. Cliquez sur Generate token
11. IMPORTANT: Copiez le token généré immédiatement
""")
                token = input("Collez le token généré: ")
                subprocess.run(["gh", "auth", "login", "--with-token"], input=token.encode(), check=True)
            
            # Verify login status
            result = subprocess.run(["gh", "auth", "status"], capture_output=True, text=True)
            if "Logged in to" not in result.stdout:
                print("❌ Échec de connexion à GitHub")
                sys.exit(1)
            print("✅ Connecté à GitHub avec succès!")
            
        except subprocess.CalledProcessError:
            print("❌ Erreur lors de la connexion à GitHub ou de l'ajout des secrets")
            sys.exit(1)
        
        # Vérifie si le script token_converter.py existe
        token_converter_path = self.project_root / "src" / "token_converter.py"
        if not token_converter_path.exists():
            print(f"⚠️ Le script token_converter.py n'a pas été trouvé à l'emplacement {token_converter_path}")
            print("Veuillez vérifier que vous êtes dans le dossier racine du projet.")
        else:
            print("\nVérification et génération du token...")
            print("Veuillez suivre les instructions à l'écran et vous connecter avec votre compte google pour générer le token.")
            
            if not os.path.exists(self.google_dir / "token.pickle"):
                try:
                    subprocess.run([sys.executable, "cyCalendar.py"], check=True)
                    if not os.path.exists(self.google_dir / "token.pickle"):
                        print("❌ Le token n'a pas été généré correctement.")
                        sys.exit(1)
                    print("\n✅ Le token a été généré avec succès!")
                except subprocess.CalledProcessError:
                    print("❌ Erreur lors de l'exécution de cyCalendar.py")
                    sys.exit(1)
            else:
                print("✅ Le token a déjà été généré.")
            
            print("Exécution du script token_converter.py...\n")
            subprocess.run([sys.executable, "src/token_converter.py"], check=True)

        print("\nConfiguration des secrets GitHub...")
        
        try:
            # Récupération des informations nécessaires
            with open(self.env_path, 'r') as f:
                env_content = f.read()
                cy_username = env_content.split('CY_USERNAME=')[1].split('\n')[0]
                cy_password = env_content.split('CY_PASSWORD=')[1].split('\n')[0]
            
            credentials_files = list(self.google_dir.glob('client_secret_*.apps.googleusercontent.com.json'))
            if credentials_files:
                with open(credentials_files[0], 'r') as f:
                    google_credentials = f.read()
            else:
                print("❌ Fichier de credentials Google introuvable")
                sys.exit(1)

            with open(self.google_dir / "token.pickle", 'rb') as f:
                import base64
                google_token = base64.b64encode(f.read()).decode('utf-8')

            # Extraction du nom du repo
            repo_url = subprocess.run(["gh", "repo", "view", "--json", "url", "-q", ".url"], 
                                    capture_output=True, text=True).stdout.strip()
            repo_name = repo_url.split('/')[-1]

            # Ajout des secrets
            print("\nAjout des secrets GitHub...")
            secrets = {
                'CY_USERNAME': cy_username,
                'CY_PASSWORD': cy_password,
                'GOOGLE_CREDENTIALS': google_credentials,
                'GOOGLE_TOKEN': google_token,
                'WORKFLOW_PAT': token  # token from previous input
            }

            for secret_name, secret_value in secrets.items():
                print(f"Ajout du secret {secret_name}...")
                subprocess.run(["gh", "secret", "set", secret_name, "-b", secret_value], check=True)
                print(f"✅ Secret {secret_name} ajouté avec succès!")

            print("\n✅ Tous les secrets ont été configurés avec succès!")
              
            try:
                # List available workflows first
                print("\nRécupération de la liste des workflows...")
                result = subprocess.run(["gh", "workflow", "list"], capture_output=True, text=True, check=True)
                print(result.stdout)

                # Extract the workflow ID for "Update Google Calendar"
                workflows = result.stdout.splitlines()
                workflow_line = next((line for line in workflows if "Update Google Calendar" in line), None)
                
                if workflow_line:
                    workflow_id = workflow_line.split()[-1]  # Assuming ID is the third column
                    
                    # Enable the workflow using ID
                    print("\nActivation du workflow...")
                    subprocess.run(["gh", "workflow", "enable", workflow_id], check=True)
                    print("✅ Workflow GitHub Actions activé!")
                    
                    # Run the workflow using ID
                    print("\nLancement du workflow...")
                    subprocess.run(["gh", "workflow", "run", workflow_id], check=True)
                    print("✅ Workflow lancé!")
                else:
                    raise ValueError("Workflow 'Update Google Calendar' non trouvé")

            except subprocess.CalledProcessError as e:
                print(f"❌ Erreur lors de la configuration du workflow : {e}")
                import traceback
                traceback.print_exc()
            except Exception as e:
                print(f"❌ Une erreur s'est produite : {e}")
                import traceback
                traceback.print_exc()    

        except subprocess.CalledProcessError as e:
            print(f"❌ Erreur lors de l'ajout des secrets: {e}")
            print("Veuillez résoudre l'erreur affichée ou les ajouter manuellement dans les paramètres de votre repo GitHub")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Une erreur s'est produite: {e}")
            print("Veuillez résoudre l'erreur affichée ou ajouter les secrets manuellement dans les paramètres de votre repo GitHub")
            sys.exit(1)

        print("\n✅ Configuration de GitHub Actions terminée!\n")
        with open(".setup.log", "w") as f:
            f.write("4")

    def run(self):
        try :
            try:
                with open(".setup.log", "r") as f:
                    log = f.read()
                    log = int(log)
                    choice = input("Une installation précédente a été détectée. Souhaitez vous recommencer ? (y/n): ")
                    if choice.lower() == 'y':
                        log = 0
            except FileNotFoundError:
                log = 0
                pass
            
            self.display_welcome()
            self.select_installation_mode()
            if log < 1 : self.install_dependencies()
            if log < 2 : self.setup_environment()
            
            if self.mode > 1 and log < 3:
                success = self.setup_google_api()
                if not success:
                    print("❌ Configuration de l'API Google Calendar échouée.")
                    return
            
            if self.mode == 3 and log < 4:
                self.setup_github_actions()
                print("\n\nConfiguration de GitHub Actions terminée! Vous pouvez maintenant vérifier le statut du workflow dans l'onglet Actions de votre repo GitHub.")
                print("Ou plus simplement patientez quelques minutes et consultez votre calendrier Google.")
            
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
                print("GitHub Actions mettra automatiquement à jour votre calendrier chaque jour à une heure aléatoire entre 18h et 20h.")
                
        except KeyboardInterrupt:
            print("\n\nInstallation annulée par l'utilisateur.")
        except Exception as e:
            print(f"\n❌ Une erreur s'est produite: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    installer = CyCalendarInstaller()
    installer.run()