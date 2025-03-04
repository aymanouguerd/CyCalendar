import requests
from datetime import datetime, timedelta
import uuid
from icalendar import Calendar, Event
import pytz
import os
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

def create_session():
    """
    Creates an optimized session with retry strategy
    """
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=[500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def get_calendar_data(cookie, student_number, range='year'):
    """
    Récupère les données du calendrier de l'étudiant
    
    Args:
        cookie: Cookie d'authentification
        student_number: Numéro étudiant
        range: Plage de dates ('year', 'month', 'week')
        
    Returns:
        Liste des événements du calendrier
    """
    # Paramètres pour la plage de dates
    current_date = datetime.now()
    current_year = current_date.year
    current_month = current_date.month
    
    if range == 'year':
        # Calculer la date de fin (2 mois après la date actuelle)
        end_date = current_date + timedelta(days=60)
        end_date_str = end_date.strftime('%Y-%m-%d')
        
        # Si on est entre janvier et août, on prend depuis janvier de l'année en cours
        if current_month < 9:  # Avant septembre
            start_date = datetime(current_year, 1, 1)
            start_date_str = start_date.strftime('%Y-%m-%d')
            print(f"Récupération du calendrier du {start_date_str} au {end_date_str}")
        else:  # À partir de septembre, on prend depuis septembre de l'année en cours
            start_date = datetime(current_year, 9, 1)
            start_date_str = start_date.strftime('%Y-%m-%d')
            print(f"Récupération du calendrier du {start_date_str} au {end_date_str}")
    elif range == 'month':
        # Du premier jour du mois actuel au dernier jour du mois actuel
        start_date = datetime(current_year, current_month, 1)
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date = (start_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        end_date_str = end_date.strftime('%Y-%m-%d')
        print(f"Récupération du calendrier du mois: {start_date_str} au {end_date_str}")
    elif range == 'week':
        # Du lundi de la semaine actuelle au dimanche de la semaine actuelle
        start_date = current_date - timedelta(days=current_date.weekday())
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date = start_date + timedelta(days=6)
        end_date_str = end_date.strftime('%Y-%m-%d')
        print(f"Récupération du calendrier de la semaine: {start_date_str} au {end_date_str}")
    else:
        raise ValueError("Range must be 'year', 'month', or 'week'")
    
    url = "https://services-web.cyu.fr/calendar/Home/GetCalendarData"
    
    # Préparer les cookies pour la requête
    request_cookies = {cookie['name']: cookie['value']}
    
    # Ajout du paramètre colourScheme dans le payload
    payload = f'start={start_date_str}&end={end_date_str}&resType=104&calView=month&federationIds%5B%5D={student_number}&colourScheme=3'
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest',
        'Origin': 'https://services-web.cyu.fr',
        'Referer': f'https://services-web.cyu.fr/calendar/cal?vt=month&dt={current_date.strftime("%Y-%m-%d")}&et=student&fid0={student_number}',
    }
    
    events = None
    try:
        session = create_session()
        response = session.post(
            url,
            headers=headers,
            data=payload,
            cookies=request_cookies,
            timeout=(5, 15),  # (connect timeout, read timeout)
            verify=True  # Ensure SSL verification is enabled
        )
        response.raise_for_status()
        events = response.json()
        
        if not events:
            print("Aucun événement reçu!")
            return None
        
        print(f"{len(events)} événements récupérés")
        return events
        
    except requests.exceptions.Timeout:
        print("Timeout lors de la récupération du calendrier. Le serveur met trop de temps à répondre.")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de la récupération du calendrier: {e}")
        return None
    finally:
        if 'session' in locals():
            session.close()

def parse_description(description):
    """
    Parse la description des événements pour extraire les informations importantes
    """
    parts = description.split('<br />')
    parts = [p.strip() for p in parts if p.strip()]
    
    event_type = parts[0] if parts else ""  # TD, CM, etc.
    group = parts[1] if len(parts) > 1 else ""  # ING1 GI Apprentissage...
    subject = parts[2] if len(parts) > 2 else ""  # Subject name
    location = parts[3] if len(parts) > 3 else ""  # Room number
    professor = parts[4] if len(parts) > 4 else ""  # Professor name

    # Remove occurrences of (TD, CM, TP) in subject
    event_types = ['TD', 'CM', 'TP']
    for et in event_types:
        subject = subject.replace(et, '').strip()
            
    return event_type, group, subject, location, professor

def get_google_calendar_color(bg_color):
    """
    Convertit une couleur hex en ID de couleur Google Calendar
    Voir: https://developers.google.com/calendar/api/v3/reference/colors/get
    """
    # Mapping des couleurs CY vers les IDs de couleur Google Calendar
    color_mapping = {
        '#FF0000': '11',  # Rouge - pour les CM
        '#4A4AFF': '9',   # Bleu - pour les TD
        '#FF8000': '6',   # Orange - pour les TP
        '#00FF00': '2',   # Vert
        '#FFA500': '5',   # Orange clair
    }
    return color_mapping.get(bg_color, '1')  # 1 = Bleu lavande par défaut

def create_ics_file(events_data, output_file='cy_calendar.ics'):
    """
    Crée un fichier ICS à partir des données du calendrier
    """
    # Create the generated directory if it doesn't exist
    generated_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'generated')
    os.makedirs(generated_dir, exist_ok=True)
    
    # Set the full output path in the generated directory
    output_path = os.path.join(generated_dir, output_file)
    
    cal = Calendar()
    cal.add('prodid', '-//CY University Calendar//FR')
    cal.add('version', '2.0')
    
    paris_tz = pytz.timezone('Europe/Paris')
    
    events_count = 0
    for event_data in events_data:
        try:
            event = Event()
            
            # Parse description
            event_type, group, subject, location, professor = parse_description(event_data['description'])
            
            # Ajouter les informations de base
            event.add('uid', str(uuid.uuid4()))
            event.add('summary', f"{subject} - {event_type}")
            event.add('location', location)
            
            # Formatter la description
            description = f"{group}\\nProfesseur: {professor}"
            event.add('description', description)
            
            # Ajouter la couleur de l'événement
            if 'backgroundColor' in event_data:
                color_id = get_google_calendar_color(event_data['backgroundColor'])
                event.add('X-GOOGLE-CALENDAR-COLOR', color_id)
                
            # Dates de début et fin
            try:
                start = datetime.strptime(event_data['start'], '%Y-%m-%dT%H:%M:%S')
                # Si pas de date de fin, ajouter 2h par défaut
                if not event_data.get('end'):
                    end = start + timedelta(hours=2)
                else:
                    end = datetime.strptime(event_data['end'], '%Y-%m-%dT%H:%M:%S')
                
                # Ajouter le fuseau horaire
                start = paris_tz.localize(start)
                end = paris_tz.localize(end)
                
                event.add('dtstart', start)
                event.add('dtend', end)
                
                # Ajouter l'événement au calendrier
                cal.add_component(event)
                events_count += 1
            except (ValueError, TypeError) as e:
                print(f"Erreur avec les dates de l'événement: {e}")
                continue
            
        except Exception as e:
            print(f"Erreur lors du traitement d'un événement: {e}")
            continue
    
    if events_count == 0:
        print("Aucun événement n'a pu être traité!")
        return None
    
    # Écrire le fichier ICS
    with open(output_path, 'wb') as f:
        f.write(cal.to_ical())
    
    print(f"Fichier ICS créé avec succès: {output_path} ({events_count} événements)")
    return output_path

if __name__ == "__main__":
    from auth import get_auth_info
    
    # Test de la création du fichier ICS
    cookie, student_id = get_auth_info()
    if cookie and student_id:
        events_data = get_calendar_data(cookie, student_id)
        if events_data:
            create_ics_file(events_data)