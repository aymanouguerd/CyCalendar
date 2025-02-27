import os
import requests
import re
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pyvirtualdisplay import Display

def setup_chrome_driver():
    """Configuration du driver Chrome pour GitHub Actions"""
    chrome_options = Options()
    
    # Configuration spécifique pour GitHub Actions
    if os.getenv('SELENIUM_HEADLESS'):
        print("Configuration du mode headless...")
        chrome_options.add_argument('--headless=new')  # nouvelle syntaxe headless
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
        driver = webdriver.Chrome(options=chrome_options)
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
            raise ValueError("Les identifiants CY_USERNAME et CY_PASSWORD doivent être définis")

        # Initialisation du driver Chrome
        driver = setup_chrome_driver()
        if not driver:
            raise Exception("Impossible d'initialiser le driver Chrome")

        # Accès à la page de connexion avec retry
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"Tentative de connexion {attempt + 1}/{max_retries}...")
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
                
                # Attendre la redirection avec un timeout plus long
                WebDriverWait(driver, 20).until(
                    EC.url_contains('/calendar')
                )
                break
            except Exception as e:
                print(f"Tentative {attempt + 1} échouée: {str(e)}")
                if attempt == max_retries - 1:
                    raise
                continue

        # Extraire le student number
        current_url = driver.current_url
        print("Extraction du numéro étudiant...")
        student_match = re.search(r'fid0=(\d+)', current_url)
        if not student_match:
            return None, None
            
        student_number = student_match.group(1)
        print(f"Numéro étudiant trouvé: {student_number}")
        
        # Récupérer les cookies
        print("Récupération des cookies...")
        cookies = driver.get_cookies()
        calendar_cookie = next(
            (cookie for cookie in cookies if cookie['name'] == '.Calendar.Cookies'),
            None
        )
        
        return calendar_cookie, student_number
            
    except Exception as e:
        print(f"Erreur détaillée lors de l'authentification: {str(e)}")
        if driver:
            print("Page source:", driver.page_source)
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