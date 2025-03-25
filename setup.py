import sys
import platform
import subprocess
import getpass
import base64
import time
import shutil
import random
import webbrowser
from pathlib import Path
from urllib.parse import urlparse
import os

class CyCalendarInstaller:
    def __init__(self):
        self.os_type = platform.system()
        self.platform = self.os_type.lower()  # Pour faciliter les comparaisons
        self.project_root = Path.cwd()
        self.env_path = self.project_root / '.env'
        self.google_dir = self.project_root / 'google'
        self.credentials_path = None
        self.mode = None
        
    def write_log(self, step):
        # Écriture du log
        try:
            with open(".setup.log", "w") as f:
                f.write(str(step))
        except Exception as e:
            print(f"⚠️ Impossible d'écrire dans le fichier .setup.log: {e}")

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
        
        if self.platform == "linux":
            print("Installation des dépendances Linux...")
            try:
                subprocess.run(["bash", "setup.bash"], check=True)
                print("✅ Dépendances Linux installées avec succès.")
                self.write_log(1)
            except subprocess.CalledProcessError:
                print("⚠️ Erreur lors de l'installation des dépendances Linux.")
                print("Tentative d'installation manuelle des dépendances Python...")
                self.install_python_dependencies()
        
        elif self.platform == "darwin":
            print("Installation des dépendances macOS...")
            try:
                # Vérifier si brew est installé
                subprocess.run(["which", "brew"], check=True, capture_output=True)
                
                # Installer les dépendances avec Homebrew
                print("Installation de Google Chrome...")
                subprocess.run(["brew", "install", "--cask", "google-chrome"], check=True)
                
                print("Installation de Python et pip...")
                subprocess.run(["brew", "install", "python"], check=True)
                
                print("✅ Dépendances macOS installées avec succès.")
                self.write_log(1)
            except subprocess.CalledProcessError:
                print("⚠️ Erreur lors de l'installation des dépendances macOS.")
                print("Tentative d'installation manuelle des dépendances Python...")
                self.install_python_dependencies()
        
        else:
            print(f"Système d'exploitation non pris en charge: {self.os_type}")
            print("Ce script est conçu pour Linux et macOS uniquement.")
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
        cy_username = ""
        while not cy_username:
            cy_username = input("Entrez votre identifiant CY Tech (e-1erelettreprenom+nom): ")
            if not cy_username:
                print("Identifiant vide, veuillez réessayer.")
        
        # Utiliser getpass pour une saisie sécurisée
        cy_password = getpass.getpass("Entrez votre mot de passe CY Tech: ")
        
        # Créer le fichier .env
        with open(self.env_path, 'w') as env_file:
            env_file.write(f"CY_USERNAME={cy_username}\n")
            env_file.write(f"CY_PASSWORD={cy_password}\n")
        
        print("✅ Fichier .env créé avec succès.")
        self.write_log(2)

    def setup_google_api(self):
        if self.mode == 1:
            print("\n[3/5] Mode manuel sélectionné - Étape Google API ignorée.")
            return True
            
        print("\n[3/5] Configuration de l'API Google Calendar...")
        
        # Vérifier si un fichier de credentials existe déjà
        credentials_files = list(self.google_dir.glob('client_secret_*.apps.googleusercontent.com.json'))

        if credentials_files:
            print(f"Fichier de credentials trouvé : {credentials_files[0]}")
            choice = input("Voulez-vous utiliser ce fichier ? (y/n): ")
            if choice.lower() == 'y':
                self.credentials_path = credentials_files[0]
                self.write_log(3)
                return True
        
        print("\nConfiguration automatique avec redirections...")
        print("Plusieurs pages vont s'ouvrir, suivez les instructions sur le terminal afin de compléter la configuration google.")

        print("\nOuverture de https://console.cloud.google.com/ ...")
        print("Sur cette page il vous suffit de créer un projet avec le nom que vous voulez. (Connectez vous au compte google que vous souhaitez utiliser)")
        time.sleep(2)        
        webbrowser.open("https://console.cloud.google.com/")
        
        input("\nAppuyez sur Entrée une fois que le projet est créé et a fini de charger...")

        print("\nOuverture de https://console.cloud.google.com/marketplace/product/google/calendar-json.googleapis.com ...")
        print("Sur cette page, cliquez sur le bouton 'Activer' pour activer l'API Google Calendar.")
        time.sleep(2)
        webbrowser.open("https://console.cloud.google.com/marketplace/product/google/calendar-json.googleapis.com")

        input("\nAppuyez sur Entrée une fois que l'API Google Calendar est activée et a fini de charger...")

        print("\nOuverture de https://console.cloud.google.com/auth/overview ...")
        print("Sur cette page, cliquez sur le bouton premiers pas puis complétez comme suit :")
        print("-> Nom d'application : cycalendar et mettez votre adresse mail en adresse d'assistance")
        print("-> Cible : externe")
        print("-> Coordonées : votre adresse mail")
        print("-> Acceptez puis créer")
        time.sleep(2)
        webbrowser.open("https://console.cloud.google.com/auth/overview")

        input("\nAppuyez sur Entrée une fois que la page Présentation d'OAuth a fini de charger...")

        print("\nOuverture de https://console.cloud.google.com/auth/audience ...")
        print("Sur cette page, sous utilisateurs tests cliquez sur ADD USERS, entrez votre adresse mail et cliquez sur Enregistrer.")
        time.sleep(2)
        webbrowser.open("https://console.cloud.google.com/auth/audience")

        input("\nAppuyez sur Entrée une fois que vous avez ajouté votre adresse mail...")

        print("\nOuverture de https://console.cloud.google.com/auth/clients/create ...")
        print("Sur cette page, choisissez application de bureau pour le type et mettez le nom que vous souhaitez puis cliquez sur créer")
        time.sleep(2)
        webbrowser.open("https://console.cloud.google.com/auth/clients/create")

        input("\nAppuyez sur Entrée une fois que le client OAuth 2.0 a été créé et a fini de charger...")

        print("\nIl ne vous reste plus qu'à cliquer sur l'icone de téléchargement tout à droite de votre clé créée, puis sur télécharger au format json.")       
        
        input("\nAppuyez sur Entrée une fois que le fichier de credentials a été téléchargé...")

        # Try to find the credentials file in common Downloads locations
        possible_paths = [
            Path.home() / "Downloads",
            Path.home() / "Téléchargements",
            Path("/data/Downloads"),
            Path("/data/Téléchargements"),
            Path("/tmp")
        ]
        
        credentials_files = []
        for path in possible_paths:
            if path.exists():
                credentials_files.extend(list(path.glob('client_secret_*.apps.googleusercontent.com.json')))

        if credentials_files:
            latest_file = max(credentials_files, key=lambda x: x.stat().st_mtime)
            print(f"\nFichier de credentials trouvé dans vos téléchargements: {latest_file}")
            choice = input("Est ce le bon ? (y/n): ")
            if choice.lower() == 'y':
                try:
                    # Try to use project directory first
                    self.google_dir.mkdir(exist_ok=True)
                    shutil.copy2(latest_file, self.google_dir)
                    self.credentials_path = self.google_dir / latest_file.name
                except PermissionError:
                    print(f"\n❌ Permission refusée pour copier le fichier de credentials de {latest_file} vers {self.google_dir}, veuillez le faire manuellement sans changer le nom ni le contenu.")
                    input("\nAppuyez sur Entrée une fois que vous avez copié le fichier...")
                    self.credentials_path = self.google_dir / latest_file

        # If not found automatically or user declined, ask for manual path
        if not self.credentials_path:
            while True:
                manual_path = Path(input("Entrez le chemin du fichier de credentials téléchargé: "))
                if "client_secret_" in manual_path.name and ".apps.googleusercontent.com.json" in manual_path.name:
                    self.google_dir.mkdir(exist_ok=True) 
                    shutil.copy(manual_path, self.google_dir)
                    self.credentials_path = self.google_dir / manual_path.name
                    break
                else:
                    print("Fichier de credentials invalide. Veuillez réessayer.")
                    
        self.write_log(3)
        
        return True

    def install_gh_cli(self):
        """Installation de GitHub CLI pour Linux et macOS."""
        try:
            # Vérifier si GitHub CLI est déjà installé
            subprocess.run(["gh", "--version"], check=True, capture_output=True)
            print("✅ GitHub CLI est déjà installé!")
            return "gh"
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("Installation de GitHub CLI...")
            try:
                if self.platform == "linux":
                    # Détection de la distribution Linux
                    if os.path.exists("/etc/debian_version"):
                        # Debian, Ubuntu, etc.
                        print("Distribution basée sur Debian détectée")
                        subprocess.run(["curl", "-fsSL", "https://cli.github.com/packages/githubcli-archive-keyring.gpg", "|", 
                                        "sudo", "dd", "of=/usr/share/keyrings/githubcli-archive-keyring.gpg"], 
                                        shell=True, check=True)
                        subprocess.run(["echo", "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main", 
                                        "|", "sudo", "tee", "/etc/apt/sources.list.d/github-cli.list"], 
                                        shell=True, check=True)
                        subprocess.run(["sudo", "apt", "update"], check=True)
                        subprocess.run(["sudo", "apt", "install", "gh", "-y"], check=True)
                    elif os.path.exists("/etc/fedora-release") or os.path.exists("/etc/redhat-release"):
                        # Fedora, RHEL, CentOS
                        print("Distribution basée sur RHEL/Fedora détectée")
                        subprocess.run(["sudo", "dnf", "install", "gh", "-y"], check=True)
                    elif os.path.exists("/etc/arch-release"):
                        # Arch Linux
                        print("Arch Linux détectée")
                        subprocess.run(["sudo", "pacman", "-S", "github-cli"], check=True)
                    else:
                        print("Distribution Linux non reconnue, tentative avec snap...")
                        subprocess.run(["sudo", "snap", "install", "gh"], check=True)
                
                elif self.platform == "darwin":
                    # macOS - utilisation de Homebrew
                    print("Installation de GitHub CLI avec Homebrew...")
                    try:
                        # Vérifier si Homebrew est installé
                        subprocess.run(["which", "brew"], check=True, capture_output=True)
                        subprocess.run(["brew", "install", "gh"], check=True)
                    except subprocess.CalledProcessError:
                        print("❌ Homebrew n'est pas installé.")
                        print("Veuillez installer Homebrew (https://brew.sh/) puis réexécuter ce script.")
                        sys.exit(1)
                
                else:
                    print(f"❌ Système d'exploitation non pris en charge: {self.platform}")
                    print("Ce script est conçu pour Linux et macOS uniquement.")
                    sys.exit(1)
                
                # Vérification de l'installation
                subprocess.run(["gh", "--version"], check=True)
                print("✅ GitHub CLI installé avec succès!")
                return "gh"
            
            except subprocess.CalledProcessError as e:
                print(f"❌ Erreur lors de l'installation de GitHub CLI: {e}")
                print("Veuillez l'installer manuellement depuis: https://cli.github.com/")
                
                install_manually = input("Souhaitez-vous continuer une fois l'installation manuelle effectuée? (y/n): ")
                if install_manually.lower() == 'y':
                    print("Veuillez installer GitHub CLI puis redémarrer ce script.")
                sys.exit(1)

    def github_login(self):
        try:
            # Vérifier la connexion
            result = subprocess.run(["gh", "auth", "status"], capture_output=True, text=True)
            
            # Si déjà connecté, récupérer le token
            if "Logged in to" in result.stdout:
                print("✅ Déjà connecté à GitHub!")
                return subprocess.run(["gh", "auth", "token"], capture_output=True, text=True).stdout.strip()
            
            print("\nOuverture de la page de création de token...")
            print("Créez le token en suivant ces instructions :")
            print("- Nom : Votre choix")
            print("- Expiration : Jamais ou selon vos préférences (l'app ne marchera plus après l'expiration)")
            print("- Permissions : sous Repository cochez (en read/write) Actions, Contents, Pull Requests, Secrets et Workflows")
            print("Puis cliquez sur Generate token et copiez le token généré.")
            time.sleep(3)
            webbrowser.open("https://github.com/settings/personal-access-tokens/new")
            
            token = input("\nCollez votre Personal Access Token : ")
            
            # Connexion avec le token
            subprocess.run(["gh", "auth", "login", "--with-token"], 
                           input=token.encode(), 
                           check=True)
            
            return token
        
        except subprocess.CalledProcessError as e:
            print(f"❌ Erreur de connexion : {e}")
            sys.exit(1)

    def select_repo(self):
        while True:
            try:
                # Vérifier si un fork existe déjà
                repos = subprocess.run(["gh", "repo", "list", "--limit", "100"], 
                                    capture_output=True, 
                                    text=True, 
                                    check=True).stdout.strip().split('\n')
                
                # Vérifier si CyCalendar est déjà forké
                cy_repos = [repo for repo in repos if "CyCalendar" in repo]
                
                print("\nVos dépôts GitHub :")
                print(f"0. Je n'ai pas encore fork le repo CyCalendar et donc je ne le vois pas dans les options")
                
                if cy_repos:
                    print("Dépôts CyCalendar existants :")
                    for i, repo in enumerate(cy_repos, 1):
                        print(f"{i}. {repo} [RECOMMANDÉ]")
                    
                print("\nAutres dépôts :")
                for i, repo in enumerate(repos, len(cy_repos) + 1):
                    if repo not in cy_repos:
                        print(f"{i}. {repo}")
                
                choice = input("\nSélectionnez votre fork de CyCalendar (ou 0 pour en créer un nouveau) : ")
                
                if choice == "0":
                    print("\nCréation d'un fork du dépôt CyCalendar...")
                    # Ne pas cloner le repo, juste le forker
                    fork_result = subprocess.run(
                        ["gh", "repo", "fork", "NayJi7/CyCalendar", "--clone=false"],
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    
                    print("✅ Fork de CyCalendar effectué avec succès!")
                    
                    # Extraire le nom du fork à partir des résultats
                    for line in fork_result.stdout.splitlines():
                        if "Created fork" in line:
                            parts = line.split()
                            for part in parts:
                                if "/" in part and "CyCalendar" in part:
                                    return part.strip()
                    
                    # Si on ne peut pas extraire le nom automatiquement
                    username_result = subprocess.run(
                        ["gh", "api", "user", "-q", ".login"],
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    username = username_result.stdout.strip()
                    
                    if username:
                        fork_name = f"{username}/CyCalendar"
                        print(f"Fork créé sous: {fork_name}")
                        # Activer les workflows pour le fork nouvellement créé
                        print("\nActivation des workflows pour le nouveau fork...")
                        try:
                            # Ouvrir la page des actions pour activer manuellement
                            print(f"Veuillez ouvrir: https://github.com/{fork_name}/actions et activer les workflows")
                            webbrowser.open(f"https://github.com/{fork_name}/actions")
                            input("Appuyez sur Entrée une fois que vous avez activé les workflows...")
                        except Exception as e:
                            print(f"⚠️ Erreur lors de l'activation des workflows: {e}")
                        return fork_name
                    
                    raise ValueError("Impossible de déterminer le nom du dépôt forké")
                
                # Sélectionner un repo existant
                choice = int(choice)
                if 1 <= choice <= len(cy_repos):
                    # Sélection d'un dépôt CyCalendar
                    selected_repo = cy_repos[choice - 1].split()[0]
                else:
                    # Sélection d'un autre dépôt
                    index = choice - len(cy_repos) - 1
                    if 0 <= index < len(repos):
                        selected_repo = repos[index].split()[0]
                    else:
                        print("❌ Choix invalide.")
                        continue
                
                print(f"Dépôt sélectionné: {selected_repo}")
                return selected_repo
            
            except subprocess.CalledProcessError as e:
                print(f"❌ Erreur lors de l'accès aux dépôts: {e}")
                print(f"Détails: {e.stderr if hasattr(e, 'stderr') else 'Aucun détail disponible'}")
                
                # Proposer de créer manuellement un fork
                print("\nImpossible de lister ou créer un fork automatiquement.")
                print("Veuillez vous rendre sur https://github.com/NayJi7/CyCalendar et cliquer sur 'Fork'.")
                
                manual_fork = input("\nAvez-vous créé manuellement un fork? (y/n): ")
                if manual_fork.lower() == 'y':
                    username = input("Entrez votre nom d'utilisateur GitHub: ")
                    return f"{username}/CyCalendar"
                else:
                    sys.exit(1)

    def setup_github_actions(self):
        """Configure GitHub Actions."""
        if self.mode != 3:
            print("\n[4/5] Mode GitHub Actions non sélectionné - Étape ignorée.")
            return
            
        print("\n[4/5] Configuration de GitHub Actions...")
        
        # Installation de GitHub CLI
        gh_path = self.install_gh_cli()
        
        # Connexion à GitHub
        gh_token = self.github_login()
        
        # Ajouter le token au fichier .env pour une utilisation future
        print("Sauvegarde du token GitHub dans le fichier .env...")
        try:
            with open(self.env_path, 'a') as env_file:
                env_file.write(f"WORKFLOW_PAT={gh_token}\n")
            print("✅ Token GitHub ajouté au fichier .env")
        except Exception as e:
            print(f"⚠️ Erreur lors de l'ajout du token au fichier .env: {e}")
        
        # Mise à jour de la variable d'environnement pour cette session
        os.environ["WORKFLOW_PAT"] = gh_token
        
        # Sélection ou création du dépôt
        repo_name = self.select_repo()
        
        print(f"\nConfiguration des actions pour le dépôt {repo_name}...")
        
        try:
            # Vérifier si le dépôt existe et est accessible
            try:
                subprocess.run(["gh", "repo", "view", repo_name], 
                              capture_output=True, check=True)
                print(f"✅ Dépôt {repo_name} accessible")
            except subprocess.CalledProcessError:
                print(f"❌ Impossible d'accéder au dépôt {repo_name}")
                print("Veuillez vérifier si le dépôt existe et si vous avez les permissions nécessaires.")
                return
            
            # Préparation des secrets
            with open(self.env_path, 'r') as f:
                env_content = f.read()
                cy_username = env_content.split('CY_USERNAME=')[1].split('\n')[0]
                cy_password = env_content.split('CY_PASSWORD=')[1].split('\n')[0]
            
            # Récupération des credentials Google
            credentials_files = list(self.google_dir.glob('client_secret_*.apps.googleusercontent.com.json'))
            if not credentials_files:
                print("❌ Fichier de credentials Google introuvable")
                sys.exit(1)
            
            with open(credentials_files[0], 'r') as f:
                google_credentials = f.read()

            google_token = None
            while google_token == None:
                try:
                    # Lecture du token Google
                    with open(self.google_dir / "token.pickle", 'rb') as f:
                        google_token = base64.b64encode(f.read()).decode('utf-8')
                except FileNotFoundError:
                    print("Fichier de token Google non généré.")
                    print("Execution de cyCalendar.py pour générer le token...")
                    print("Veuillez suivre les instructions affichées.")
                    time.sleep(3)
                    subprocess.run([sys.executable, "cyCalendar.py"], check=True)

            # Ajout des secrets avec spécification explicite du repo
            print("\nConfiguration des secrets GitHub...")
            secrets = {
                'CY_USERNAME': cy_username,
                'CY_PASSWORD': cy_password,
                'GOOGLE_CREDENTIALS': google_credentials,
                'GOOGLE_TOKEN': google_token,
                'WORKFLOW_PAT': gh_token
            }

            for secret_name, secret_value in secrets.items():
                print(f"Ajout du secret {secret_name}...")
                # Utiliser -R pour spécifier explicitement le dépôt
                subprocess.run(["gh", "secret", "set", secret_name, "-R", repo_name, "-b", secret_value], check=True)
                print(f"✅ Secret {secret_name} ajouté avec succès!")

            # Liste et activation du workflow avec spécification du dépôt
            print("\nRécupération de la liste des workflows...")
            try:
                result = subprocess.run(["gh", "workflow", "list", "-R", repo_name], 
                                       capture_output=True, text=True, check=True)
                print(result.stdout)

                # Extraction de l'ID du workflow
                workflows = result.stdout.splitlines()
                workflow_line = next((line for line in workflows if "Update Google Calendar" in line), None)
                
                if workflow_line:
                    workflow_id = workflow_line.split()[-1]  # Dernier élément (ID)
                    
                    # Activation du workflow
                    print("\nActivation du workflow...")
                    subprocess.run(["gh", "workflow", "enable", workflow_id, "-R", repo_name], check=True)
                    print("✅ Workflow GitHub Actions activé!")
                    
                    # Lancement du workflow
                    print("\nLancement du workflow...")
                    subprocess.run(["gh", "workflow", "run", workflow_id, "-R", repo_name], check=True)
                    print("✅ Workflow lancé!")
                else:
                    print("⚠️ Workflow 'Update Google Calendar' non trouvé")
                    print("Vérifiez que les workflows sont activés dans votre dépôt GitHub")
                    
                    # Ouvrir la page des actions pour activation manuelle
                    open_actions = input("Voulez-vous ouvrir la page des actions pour activer manuellement les workflows? (y/n): ")
                    if open_actions.lower() == 'y':
                        webbrowser.open(f"https://github.com/{repo_name}/actions")
                        print("Cliquez sur le bouton 'I understand my workflows, go ahead and enable them'")
                        input("Appuyez sur Entrée une fois que vous avez activé les workflows...")
                        
                        # Nouvelle tentative de lister les workflows
                        print("Nouvelle tentative de récupération des workflows...")
                        result = subprocess.run(["gh", "workflow", "list", "-R", repo_name], 
                                               capture_output=True, text=True, check=True)
                        workflows = result.stdout.splitlines()
                        workflow_line = next((line for line in workflows if "Update Google Calendar" in line), None)
                        
                        if workflow_line:
                            workflow_id = workflow_line.split()[-1]
                            print("\nActivation du workflow...")
                            subprocess.run(["gh", "workflow", "enable", workflow_id, "-R", repo_name], check=True)
                            print("✅ Workflow GitHub Actions activé!")
                            subprocess.run(["gh", "workflow", "run", workflow_id, "-R", repo_name], check=True)
                            print("✅ Workflow lancé!")

            except subprocess.CalledProcessError as e:
                print(f"❌ Erreur lors de la configuration du workflow : {e}")
                print(f"Détails: {e.stderr if hasattr(e, 'stderr') else 'Aucun détail disponible'}")
                
                # Proposer une activation manuelle
                print("\nVous pouvez activer manuellement les workflows en visitant:")
                print(f"https://github.com/{repo_name}/actions")
                
                open_page = input("Ouvrir cette page maintenant? (y/n): ")
                if open_page.lower() == 'y':
                    webbrowser.open(f"https://github.com/{repo_name}/actions")
            except Exception as e:
                print(f"❌ Une erreur s'est produite : {e}")
                import traceback
                traceback.print_exc()

            print("\n✅ Configuration de GitHub Actions terminée!")
            
            # Écriture du log
            self.write_log(4)

        except subprocess.CalledProcessError as e:
            print(f"❌ Erreur lors de l'ajout des secrets: {e}")
            print(f"Détails: {e.stderr if hasattr(e, 'stderr') else 'Aucun détail disponible'}")
            print("Veuillez résoudre l'erreur affichée ou les ajouter manuellement dans les paramètres de votre repo GitHub")
        except Exception as e:
            print(f"❌ Une erreur s'est produite: {e}")
            print("Veuillez résoudre l'erreur affichée ou ajouter les secrets manuellement dans les paramètres de votre repo GitHub")
            import traceback
            traceback.print_exc()

    def run(self):
        try:
            try:
                with open(".setup.log", "r") as f:
                    log = f.read()
                    log = int(log)
                    choice = input("Une installation précédente a été détectée. Souhaitez-vous reprendre cette installation ? (y/n): ")
                    if choice.lower() != 'y':
                        log = 0
            except FileNotFoundError:
                log = 0
                pass
            
            self.display_welcome()
            self.select_installation_mode()
            if log < 1: self.install_dependencies()
            if log < 2: self.setup_environment()
            
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