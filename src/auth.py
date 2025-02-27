import os
import requests
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from getpass import getpass
from pyvirtualdisplay import Display

def get_auth_info():
    """
    Se connecte au portail CY et récupère les cookies et informations nécessaires
    Returns:
        tuple: (cookies, student_number) ou (None, None) en cas d'erreur
    """
    try:
        # Initialisation de l'affichage virtuel
        display = Display(visible=0, size=(1920, 1080))
        display.start()

        # Configuration de Chrome pour GitHub Actions
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        
        # Initialisation du driver avec le chromedriver système
        service = Service('/usr/bin/chromedriver')
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Accéder à la page de connexion
        print("Accès à la page de connexion...")
        driver.get('https://services-web.cyu.fr/calendar/LdapLogin')
        
        # Chargement des variables d'environnement
        load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
        username = os.getenv('CY_USERNAME')
        password = os.getenv('CY_PASSWORD')
        
        if not username or not password:
            raise ValueError("Les identifiants CY_USERNAME et CY_PASSWORD doivent être définis dans les variables d'environnement")
        
        # Remplir le formulaire
        username_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "Name"))
        )
        password_field = driver.find_element(By.ID, "Password")
        
        username_field.send_keys(username)
        password_field.send_keys(password)
        
        # Soumettre le formulaire
        password_field.submit()
        
        # Attendre la redirection vers la page du calendrier
        WebDriverWait(driver, 10).until(
            EC.url_contains('/calendar')
        )
        
        # Extraire le student number de l'URL
        current_url = driver.current_url
        print("Extraction du numéro étudiant...")
        import re
        student_match = re.search(r'fid0=(\d+)', current_url)
        if not student_match:
            return None, None
        student_number = student_match.group(1)
        print(f"Numéro étudiant trouvé: {student_number}")
        
        print("Récupération des cookies...")
        
        # Récupérer les cookies
        cookies = driver.get_cookies()
        calendar_cookie = None
        
        # Chercher le cookie Calendar
        for cookie in cookies:
            if cookie['name'] == '.Calendar.Cookies':
                calendar_cookie = cookie
                break
        
        return calendar_cookie, student_number
            
    except Exception as e:
        print(f"Erreur lors de l'authentification: {str(e)}")
        if 'driver' in locals():
            driver.quit()
        if 'display' in locals():
            display.stop()
        raise
        
    finally:
        if 'driver' in locals():
            driver.quit()
        if 'display' in locals():
            display.stop()

if __name__ == "__main__":
    cookie, student_id = get_auth_info()
    if cookie and student_id:
        print("Authentification réussie!")
        print(f"Cookie et numéro étudiant ({student_id}) récupérés avec succès.")
    else:
        print("Échec de l'authentification.")