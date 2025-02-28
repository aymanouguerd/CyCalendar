from src.auth import get_auth_info
from src.calendar_converter import get_calendar_data, create_ics_file
from src.google_calendar import import_to_google_calendar
import sys

def main():
    print("=== CY Calendar ===")
    
    # Étape 1 : Authentification
    print("\n1. Authentification CY...")
    print("=========================")
    cookie, student_id = get_auth_info()
    if not cookie or not student_id:
        print("Échec de l'authentification. Arrêt du programme.")
        sys.exit(1)  # Code d'erreur pour signaler l'échec à GitHub Actions
    
    # Étape 2 : Récupération et conversion du calendrier
    print("\n2. Récupération du calendrier...")
    print("================================")
    events_data = get_calendar_data(cookie, student_id)
    if not events_data:
        print("Erreur lors de la récupération du calendrier. Arrêt du programme.")
        sys.exit(1)  # Code d'erreur pour signaler l'échec à GitHub Actions
    
    # Création du fichier ICS
    ics_file = create_ics_file(events_data)
    
    # Étape 3 : Import Google Calendar
    print("\n3. Import dans Google Calendar...")
    print("=================================")
    
    # Interractive way
    # reponse = input("Voulez-vous importer ces événements dans Google Calendar ? (oui/non): ")
    # if reponse.lower() in ['oui', 'o', 'yes', 'y']:
    #     import_to_google_calendar(ics_file)
    # else:
    #     print(f"Import ignoré. Vous pouvez toujours importer manuellement le fichier {ics_file}")
    
    # Automatic way
    try:
        if True : 
            result = import_to_google_calendar(ics_file)
            if not result:
                print("Échec de l'import dans Google Calendar")
                sys.exit(1)
    except Exception as e:
        print(f"Erreur lors de l'import dans Google Calendar: {str(e)}")
        sys.exit(1)
        
    print("Synchronisation terminée avec succès!")
    sys.exit(0)  # Code de succès explicite

if __name__ == "__main__":
    main()