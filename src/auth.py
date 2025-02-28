import os
import re
import time
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pyvirtualdisplay import Display

def setup_chrome_driver():
    """Configuration du driver Chrome pour GitHub Actions et environnement local"""
    chrome_options = Options()
    
    # Configuration spécifique pour GitHub Actions et environnement local
    if os.getenv('SELENIUM_HEADLESS'):
        print("Configuration du mode headless...")
        chrome_options.add_argument('--headless=new')
        chrome_options.binary_location = "/usr/bin/chromium-browser"  # Chemin vers Chromium
    
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
    print("Binaire Chrome:", chrome_options.binary_location)
    
    try:
        service = Service("/usr/bin/chromedriver")  # Chemin explicite vers chromedriver
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_page_load_timeout(30)
        print("Driver Chrome initialisé avec succès")
        return driver
    except Exception as e:
        print(f"Erreur lors de l'initialisation du driver Chrome: {str(e)}")
        return None

def get_auth_info():
    """
    Se connecte au portail CY et récupère les cookies et informations nécessaires
    Returns:
        tuple: (cookies, student_number) ou (None, None) en cas d'erreur
    """
    driver = None
    display = None
    
    try:
        # Initialisation de l'affichage virtuel
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
        
        # Processus global avec maximum de tentatives
        global_max_attempts = 3
        for global_attempt in range(global_max_attempts):
            print(f"=== Tentative globale {global_attempt + 1}/{global_max_attempts} ===")
            
            # 1. Connexion
            connection_success = False
            for login_attempt in range(3):
                try:
                    print(f"Tentative de connexion {login_attempt + 1}/3...")
                    driver.get('https://services-web.cyu.fr/calendar/LdapLogin')
                    
                    # Attendre et remplir le formulaire
                    username_field = WebDriverWait(driver, 20).until(
                        EC.presence_of_element_located((By.ID, "Name"))
                    )
                    password_field = driver.find_element(By.ID, "Password")
                    
                    username_field.send_keys(username)
                    password_field.send_keys(password)
                    
                    # Soumettre le formulaire
                    password_field.submit()
                    
                    # Attendre la redirection avec un timeout
                    WebDriverWait(driver, 20).until(
                        EC.url_contains('/calendar')
                    )
                    connection_success = True
                    break
                    
                except Exception as e:
                    print(f"ERREUR: Tentative de connexion {login_attempt + 1} échouée: {str(e)}")
                    if login_attempt < 2:
                        print("Nouvelle tentative de connexion dans 5 secondes...")
                        time.sleep(5)
                    else:
                        print("Échec de toutes les tentatives de connexion.")
            
            if not connection_success:
                if global_attempt < global_max_attempts - 1:
                    print("Échec de connexion, nouvelle tentative globale dans 10 secondes...")
                    time.sleep(10)
                    continue
                else:
                    print("Toutes les tentatives globales ont échoué.")
                    return None, None
                    
            # 2. Extraction du numéro étudiant
            current_url = driver.current_url
            print("URL après connexion:", current_url)
            print("Extraction du numéro étudiant...")
            student_match = re.search(r'fid0=(\d+)', current_url)
            
            if not student_match:
                print("ERREUR: Impossible de trouver le numéro étudiant dans l'URL")
                print(f"URL actuelle: {current_url}")
                print(f"Titre de la page: {driver.title}")
                print("Contenu HTML de la page (premiers 500 caractères):")
                print(driver.page_source[:500])
                
                if global_attempt < global_max_attempts - 1:
                    print("Échec de l'extraction du numéro étudiant, nouvelle tentative globale dans 10 secondes...")
                    time.sleep(10)
                    continue
                else:
                    print("Toutes les tentatives globales ont échoué.")
                    return None, None
                    
            student_number = student_match.group(1)
            print(f"Numéro étudiant trouvé: {student_number}")
            
            # 3. Récupération des cookies
            print("Récupération des cookies...")
            cookies = driver.get_cookies()
            calendar_cookie = next(
                (cookie for cookie in cookies if cookie['name'] == '.Calendar.Cookies'),
                None
            )
            
            if not calendar_cookie:
                print("ERREUR: Cookie .Calendar.Cookies non trouvé")
                print("Cookies disponibles:", [c['name'] for c in cookies])
                
                if global_attempt < global_max_attempts - 1:
                    print("Échec de récupération du cookie, nouvelle tentative globale dans 10 secondes...")
                    time.sleep(10)
                    continue
                else:
                    print("Toutes les tentatives globales ont échoué.")
                    return None, None
            
            # Si on arrive ici, tout a réussi
            return calendar_cookie, student_number
            
    except Exception as e:
        print(f"ERREUR CRITIQUE: {str(e)}")
        if driver:
            try:
                print("URL actuelle:", driver.current_url)
                print("Titre de la page:", driver.title)
                print("Contenu HTML de la page (premiers 500 caractères):")
                print(driver.page_source[:500])
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