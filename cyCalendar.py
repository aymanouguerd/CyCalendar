from src.auth import get_auth_info
from src.calendar_converter import get_calendar_data, create_ics_file
from src.google_calendar import import_to_google_calendar
import sys
import time
import traceback

def main():
    print("=== CY Calendar ===")
    
    # Étape 1 : Authentification avec retries
    print("\n1. Authentification CY...")
    print("=========================")
    
    max_retries = 3
    retry_delay = 10  # secondes
    
    for attempt in range(1, max_retries + 1):
        try:
            cookie, student_id = get_auth_info()
            if cookie and student_id:
                print(f"✓ Authentification réussie après {attempt} tentative(s)")
                break
            else:
                print(f"✗ Tentative d'authentification {attempt}/{max_retries} échouée")
                if attempt < max_retries:
                    print(f"Nouvelle tentative dans {retry_delay} secondes...")
                    time.sleep(retry_delay)
        except Exception as e:
            print(f"✗ Erreur lors de la tentative {attempt}/{max_retries}: {str(e)}")
            traceback.print_exc()
            if attempt < max_retries:
                print(f"Nouvelle tentative dans {retry_delay} secondes...")
                time.sleep(retry_delay)
    
    if not cookie or not student_id:
        print("Échec de l'authentification après plusieurs tentatives. Arrêt du programme.")
        sys.exit(1)
    
    # Étape 2 : Récupération et conversion du calendrier
    print("\n2. Récupération du calendrier...")
    print("================================")
    
    for attempt in range(1, max_retries + 1):
        try:
            events_data = get_calendar_data(cookie, student_id)
            if events_data:
                print(f"✓ Récupération du calendrier réussie après {attempt} tentative(s)")
                break
            else:
                print(f"✗ Tentative de récupération {attempt}/{max_retries} échouée")
                if attempt < max_retries:
                    print(f"Nouvelle tentative dans {retry_delay} secondes...")
                    time.sleep(retry_delay)
        except Exception as e:
            print(f"✗ Erreur lors de la tentative {attempt}/{max_retries}: {str(e)}")
            traceback.print_exc()
            if attempt < max_retries:
                print(f"Nouvelle tentative dans {retry_delay} secondes...")
                time.sleep(retry_delay)
    
    if not events_data:
        print("Erreur lors de la récupération du calendrier après plusieurs tentatives. Arrêt du programme.")
        sys.exit(1)
    
    # Création du fichier ICS
    try:
        ics_file = create_ics_file(events_data)
        print(f"✓ Fichier ICS créé avec succès: {ics_file}")
    except Exception as e:
        print(f"✗ Erreur lors de la création du fichier ICS: {str(e)}")
        traceback.print_exc()
        sys.exit(1)
    
    # Étape 3 : Import Google Calendar
    print("\n3. Import dans Google Calendar...")
    print("=================================")
    
    for attempt in range(1, max_retries + 1):
        try:
            result = import_to_google_calendar(ics_file)
            if result:
                print(f"✓ Import dans Google Calendar réussi après {attempt} tentative(s)")
                break
            else:
                print(f"✗ Tentative d'import {attempt}/{max_retries} échouée")
                if attempt < max_retries:
                    print(f"Nouvelle tentative dans {retry_delay} secondes...")
                    time.sleep(retry_delay)
        except Exception as e:
            print(f"✗ Erreur lors de la tentative d'import {attempt}/{max_retries}: {str(e)}")
            traceback.print_exc()
            if attempt < max_retries:
                print(f"Nouvelle tentative dans {retry_delay} secondes...")
                time.sleep(retry_delay)
    
    if result:
        print("Synchronisation terminée avec succès!")
        sys.exit(0)
    else:
        print("Échec de l'import dans Google Calendar après plusieurs tentatives.")
        sys.exit(1)

if __name__ == "__main__":
    main()