import os
import re
import time
import platform
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from webdriver_manager.core.utils import ChromeType

# Import Display uniquement sous Linux
if platform.system() != "Windows":
    from pyvirtualdisplay import Display

def setup_chrome_driver():
    """Configuration du driver Chrome pour Windows, Linux et GitHub Actions"""
    chrome_options = Options()
    
    # Détection du système d'exploitation
    os_system = platform.system()
    print(f"Système d'exploitation détecté : {os_system}")
    
    # Configuration spécifique pour GitHub Actions et environnement headless
    if os.getenv('SELENIUM_HEADLESS', 'true').lower() == 'true':
        print("Configuration du mode headless...")
        chrome_options.add_argument('--headless=new')
        
        # Chemin spécifique pour Ubuntu/Linux en CI
        if os_system == "Linux":
            # Vérifier si le binaire existe avant de le spécifier
            chrome_paths = [
                "/usr/bin/chromium",
                "/usr/bin/chromium-browser",
                "/usr/bin/google-chrome",
                "/usr/bin/chrome"
            ]
            
            for path in chrome_paths:
                if os.path.exists(path):
                    chrome_options.binary_location = path
                    print(f"Binaire Chrome trouvé: {path}")
                    break
    
    # Options communes à toutes les plateformes
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.page_load_strategy = 'eager'
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-infobars')
    chrome_options.add_argument('--disable-notifications')
    chrome_options.add_argument('--allow-running-insecure-content')
    chrome_options.add_argument('--ignore-certificate-errors')
        
    # Ajout des options depuis CHROME_OPTS
    chrome_opts = os.getenv('CHROME_OPTS', '').split()
    for opt in chrome_opts:
        chrome_options.add_argument(opt)
        
    print("Options Chrome configurées:", chrome_options.arguments)
    
    try:
        driver = None
        # Installation et configuration spécifique selon la plateforme
        if os_system == "Windows":
            print("Configuration pour Windows...")
            try:
                print("Tentative avec Chrome...")
                service = Service(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=chrome_options)
                print("Driver Chrome initialisé avec succès sur Windows")
            except Exception as chrome_error:
                print(f"Erreur Chrome sur Windows: {chrome_error}")
                
                print("Tentative d'utilisation de Microsoft Edge...")
                try:
                    edge_options = webdriver.EdgeOptions()
                    for arg in chrome_options.arguments:
                        edge_options.add_argument(arg)
                    
                    service = Service(EdgeChromiumDriverManager().install())
                    driver = webdriver.Edge(service=service, options=edge_options)
                    print("Driver Edge initialisé avec succès sur Windows")
                except Exception as edge_error:
                    print(f"Erreur Edge sur Windows: {edge_error}")
                    raise Exception("Tous les navigateurs ont échoué")
        else:
            # Configuration pour Linux/Mac
            try:
                # Vérifier les chemins possibles pour chromedriver
                chromedriver_paths = [
                    "/usr/bin/chromedriver",
                    "/usr/local/bin/chromedriver"
                ]
                
                driver_path = None
                for path in chromedriver_paths:
                    if os.path.exists(path):
                        driver_path = path
                        print(f"Chromedriver trouvé: {path}")
                        break
                
                # Si un chemin a été trouvé, l'utiliser
                if driver_path:
                    service = Service(driver_path)
                    driver = webdriver.Chrome(service=service, options=chrome_options)
                    print("Driver Chrome initialisé avec succès sur Linux/Mac")
                else:
                    print("Aucun chromedriver trouvé dans les chemins standards")
                    raise Exception("Chromedriver non trouvé")
                    
            except Exception as e:
                print(f"Erreur lors de l'initialisation du driver: {e}")
                return None
        
        if driver:
            driver.set_page_load_timeout(30)
            return driver
        else:
            raise Exception("Aucun driver n'a pu être initialisé")
    
    except Exception as e:
        print(f"Erreur lors de l'initialisation du driver: {str(e)}")
        return None

# Le reste du code reste inchangé
def check_login_success(driver):
    """Vérifie si la connexion a réussi en vérifiant différents éléments sur la page"""
    try:
        # Vérifier si l'URL contient '/calendar'
        if '/calendar' not in driver.current_url:
            print("L'URL ne contient pas '/calendar'")
            return False
            
        # Vérifier si l'URL contient des paramètres comme 'fid0='
        if 'fid0=' not in driver.current_url:
            print("L'URL ne contient pas 'fid0='")
            return False
            
        # Vérifier si le titre de la page est correct
        if 'Calendrier' not in driver.title and 'Calendar' not in driver.title:
            print(f"Le titre de la page ne correspond pas: '{driver.title}'")
            return False
            
        return True
    except Exception as e:
        print(f"Erreur lors de la vérification du succès de connexion: {e}")
        return False

def get_auth_info():
    """
    Se connecte au portail CY et récupère les cookies et informations nécessaires
    Returns:
        tuple: (cookies, student_number) ou (None, None) en cas d'erreur
    """
    driver = None
    display = None
    
    try:
        # Initialisation de l'affichage virtuel uniquement sous Linux
        if platform.system() != "Windows" and os.getenv('SELENIUM_HEADLESS', 'true').lower() == 'true':
            print("Initialisation de l'affichage virtuel (Linux/Mac)...")
            display = Display(visible=0, size=(1920, 1080))
            display.start()
        
        # Chargement des variables d'environnement
        load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
        username = os.getenv('CY_USERNAME')
        password = os.getenv('CY_PASSWORD')
        
        if not username or not password:
            print("ERREUR: Les identifiants CY_USERNAME et CY_PASSWORD ne sont pas définis")
            return None, None
        
        # Initialisation du driver Chrome
        driver = setup_chrome_driver()
        if not driver:
            print("ERREUR: Impossible d'initialiser le driver Chrome")
            return None, None
        
        # Le reste du code reste inchangé
        # Processus global avec maximum de tentatives
        global_max_attempts = 3
        for global_attempt in range(global_max_attempts):
            print("\n" + "=" * 60)
            print(f"===== TENTATIVE GLOBALE {global_attempt + 1}/{global_max_attempts} =====")
            print("=" * 60)
            
            # 1. Connexion
            print("\n" + "-" * 40)
            print("ÉTAPE 1: CONNEXION AU PORTAIL CY")
            print("-" * 40)
            connection_success = False
            for login_attempt in range(3):
                try:
                    print(f"\nTentative de connexion {login_attempt + 1}/3...")
                    print("·" * 30)
                    
                    # D'abord, accéder à la page d'accueil du service
                    driver.get('https://services-web.cyu.fr/calendar/')
                    time.sleep(2)
                    
                    # Vérifier si nous sommes déjà connectés
                    if check_login_success(driver):
                        print("Déjà connecté, pas besoin d'authentification!")
                        connection_success = True
                        break
                    
                    # Sinon, aller à la page de connexion
                    print("Accès à la page de connexion...")
                    driver.get('https://services-web.cyu.fr/calendar/LdapLogin')
                    time.sleep(2)
                    
                    # Attendre et vérifier que la page de login est bien chargée
                    try:
                        WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.ID, "Name"))
                        )
                    except:
                        print("Impossible de trouver le champ 'Name' sur la page de login")
                        print(f"URL actuelle: {driver.current_url}")
                        print(f"Titre: {driver.title}")
                        raise Exception("Page de login non chargée correctement")
                    
                    # Remplir le formulaire
                    username_field = driver.find_element(By.ID, "Name")
                    password_field = driver.find_element(By.ID, "Password")
                    
                    username_field.clear()  # S'assurer que le champ est vide
                    password_field.clear()
                    
                    username_field.send_keys(username)
                    password_field.send_keys(password)
                    
                    # Soumettre le formulaire
                    print("Soumission du formulaire...")
                    password_field.submit()
                    
                    # Attendre un peu pour permettre la redirection
                    time.sleep(5)
                    
                    # Attendre la redirection vers la page du calendrier
                    try:
                        WebDriverWait(driver, 20).until(
                            EC.url_contains('/calendar')
                        )
                        print(f"URL après redirection: {driver.current_url}")
                    except Exception as e:
                        print(f"Erreur lors de l'attente de redirection: {e}")
                        raise
                    
                    # Vérifier explicitement si la connexion a réussi
                    if check_login_success(driver):
                        print("\n✓ Connexion réussie !")
                        connection_success = True
                        break
                    else:
                        print("\n✗ La connexion semble avoir échoué malgré la redirection.")
                        raise Exception("Échec de connexion après redirection")
                    
                except Exception as e:
                    print(f"\n✗ ERREUR: Tentative de connexion {login_attempt + 1} échouée: {str(e)}")
                    
                    if login_attempt < 2:
                        print("Nouvelle tentative de connexion dans 5 secondes...")
                        time.sleep(5)
                    else:
                        print("Échec de toutes les tentatives de connexion.")
            
            if not connection_success:
                if global_attempt < global_max_attempts - 1:
                    print("\n✗ Échec de connexion, nouvelle tentative globale dans 10 secondes...")
                    time.sleep(10)
                    continue
                else:
                    print("\n✗ Toutes les tentatives globales ont échoué.")
                    return None, None
            
            # 2. Extraction du numéro étudiant
            print("\n" + "-" * 40)
            print("ÉTAPE 2: EXTRACTION DU NUMÉRO ÉTUDIANT")
            print("-" * 40)
            current_url = driver.current_url
            print("URL après connexion:", current_url)
            
            print("Extraction du numéro étudiant...")
            student_match = re.search(r'fid0=(\d+)', current_url)
            
            if not student_match:
                print("✗ ERREUR: Impossible de trouver le numéro étudiant dans l'URL")
                print(f"URL actuelle: {current_url}")
                print(f"Titre de la page: {driver.title}")
                
                # Essayer une URL alternative ou rechercher ailleurs
                print("\nTentative d'accès à la page de l'agenda...")
                try:
                    driver.get('https://services-web.cyu.fr/calendar/Home/ReadCalendar/')
                    time.sleep(3)
                    
                    # Vérifier la nouvelle URL
                    current_url = driver.current_url
                    print("Nouvelle URL:", current_url)
                    student_match = re.search(r'fid0=(\d+)', current_url)
                    
                    if not student_match:
                        print("✗ Toujours pas de numéro étudiant trouvé.")
                        print("Contenu HTML de la page (premiers 1000 caractères):")
                        print(driver.page_source[:1000])
                        
                        if global_attempt < global_max_attempts - 1:
                            print("\n✗ Échec de l'extraction du numéro étudiant, nouvelle tentative globale dans 10 secondes...")
                            time.sleep(10)
                            continue
                        else:
                            print("\n✗ Toutes les tentatives globales ont échoué.")
                            return None, None
                except Exception as e:
                    print(f"\n✗ Erreur lors de l'accès à la page de l'agenda: {e}")
                    if global_attempt < global_max_attempts - 1:
                        continue
                    else:
                        return None, None
            
            student_number = student_match.group(1)
            print(f"✓ Numéro étudiant trouvé: {student_number}")
            
            # 3. Récupération des cookies
            print("\n" + "-" * 40)
            print("ÉTAPE 3: RÉCUPÉRATION DES COOKIES")
            print("-" * 40)
            print("Récupération des cookies...")
            cookies = driver.get_cookies()
            print(f"Cookies trouvés: {len(cookies)}")
            print("Noms des cookies:", [c['name'] for c in cookies])
            
            calendar_cookie = next(
                (cookie for cookie in cookies if cookie['name'] == '.Calendar.Cookies'),
                None
            )
            
            if not calendar_cookie:
                print("✗ ERREUR: Cookie .Calendar.Cookies non trouvé")
                
                # Essayer de rafraîchir la page pour avoir tous les cookies
                print("Tentative de rafraîchissement de la page...")
                driver.refresh()
                time.sleep(5)
                
                cookies = driver.get_cookies()
                print(f"Cookies après rafraîchissement: {len(cookies)}")
                print("Noms des cookies après rafraîchissement:", [c['name'] for c in cookies])
                
                calendar_cookie = next(
                    (cookie for cookie in cookies if cookie['name'] == '.Calendar.Cookies'),
                    None
                )
                
                if not calendar_cookie:
                    print("✗ Cookie toujours introuvable après rafraîchissement")
                    if global_attempt < global_max_attempts - 1:
                        print("\n✗ Échec de récupération du cookie, nouvelle tentative globale dans 10 secondes...")
                        time.sleep(10)
                        continue
                    else:
                        print("\n✗ Toutes les tentatives globales ont échoué.")
                        return None, None
            
            # Si on arrive ici, tout a réussi
            print("\n" + "=" * 60)
            print("✓✓✓ AUTHENTIFICATION COMPLÈTE RÉUSSIE ! ✓✓✓")
            print("=" * 60)
            return calendar_cookie, student_number
            
    except Exception as e:
        print("\n" + "!" * 60)
        print(f"✗✗✗ ERREUR CRITIQUE: {str(e)}")
        print("!" * 60)
        if driver:
            try:
                print("URL actuelle:", driver.current_url)
                print("Titre de la page:", driver.title)
            except:
                print("Impossible d'accéder aux informations de la page")
        return None, None
        
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass
        if display:
            try:
                display.stop()
            except Exception:
                pass

if __name__ == "__main__":
    cookie, student_id = get_auth_info()
    if cookie and student_id:
        print("Authentification réussie!")
        print(f"Cookie et numéro étudiant ({student_id}) récupérés avec succès.")
    else:
        print("Échec de l'authentification.")
        exit(1)