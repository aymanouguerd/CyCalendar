import requests
from datetime import datetime, timedelta
import uuid
from icalendar import Calendar, Event
import pytz
import os
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import re
import html

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
    current_date = datetime.now()
    current_year = current_date.year
    current_month = current_date.month
    
    if range == 'year':
        end_date = current_date + timedelta(days=60)
        end_date_str = end_date.strftime('%Y-%m-%d')
        
        if current_month < 9:
            start_date = datetime(current_year, 1, 1)
            start_date_str = start_date.strftime('%Y-%m-%d')
        else:
            start_date = datetime(current_year, 9, 1)
            start_date_str = start_date.strftime('%Y-%m-%d')
    elif range == 'month':
        start_date = datetime(current_year, current_month, 1)
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date = (start_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        end_date_str = end_date.strftime('%Y-%m-%d')
    elif range == 'week':
        start_date = current_date - timedelta(days=current_date.weekday())
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date = start_date + timedelta(days=6)
        end_date_str = end_date.strftime('%Y-%m-%d')
    else:
        raise ValueError("Range must be 'year', 'month', or 'week'")
    
    url = "https://services-web.cyu.fr/calendar/Home/GetCalendarData"
    
    request_cookies = {cookie['name']: cookie['value']}
    
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
            timeout=(5, 15),  
            verify=True  
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

def clean_text(text):
    """
    Nettoie le texte en décodant les entités HTML et en retirant les balises
    """
    if not text:
        return ""
    
    # Décode les entités HTML (comme &amp;, &#233;, etc.)
    text = html.unescape(text)
    
    # Retire les caractères de retour chariot et les sauts de ligne
    text = text.replace('\r', '').replace('\n', ' ').strip()
    
    return text

def extract_clean_lines(description):
    """
    Extrait les lignes d'une description en respectant les balises <br> et en nettoyant le texte
    """
    # Remplace toutes les variantes de <br> par un séparateur unique
    description = re.sub(r'<br\s*\/?>(\s*<br\s*\/?>)*', '|LINEBREAK|', description)
    
    # Supprime les autres balises HTML
    description = re.sub(r'<[^>]*>', '', description)
    
    # Décode les entités HTML
    description = html.unescape(description)
    
    # Divise par le séparateur unique
    lines = description.split('|LINEBREAK|')
    
    # Nettoie chaque ligne
    lines = [line.strip() for line in lines if line.strip()]
    
    return lines

def parse_description(description):
    """
    Parse la description des événements pour extraire les informations importantes
    """
    lines = extract_clean_lines(description)
    
    if not lines:
        return "", "", "", "", "", False, "", ""
    
    event_type = lines[0]
    is_rattrapage = "rattrapage" in event_type.lower() or "examen" in event_type.lower()
    
    if is_rattrapage:
        return parse_rattrapage_description(lines)
    else:
        return parse_regular_description(lines)

def parse_regular_description(lines):
    """
    Parse la description d'un cours normal
    """
    event_type = lines[0] if lines else ""
    group = lines[1] if len(lines) > 1 else ""
    subject = lines[2] if len(lines) > 2 else ""
    location = lines[3] if len(lines) > 3 else ""
    professor = lines[4] if len(lines) > 4 else ""
    
    # Nettoie le sujet s'il contient des crochets
    if subject and '[' in subject and ']' in subject:
        subject = subject.split('[')[0].strip()
    
    # Retire le type d'événement du sujet
    event_types = ['TD', 'CM', 'TP']
    for et in event_types:
        if subject:
            subject = subject.replace(et, '').strip()
    
    return event_type, group, subject, location, professor, False, "", ""

def parse_rattrapage_description(lines):
    """
    Parse la description d'un rattrapage
    Améliore la détection du professeur et de la matière pour éviter les confusions
    """
    event_type = lines[0]
    
    # Pour les rattrapages, il y a souvent plusieurs groupes ensemble
    groups = []
    room_index = -1
    
    # Essaye de trouver les groupes et la salle
    for i, line in enumerate(lines[1:], 1):
        if "SALLE" in line or "Amphi" in line or any(bldg in line for bldg in ["FER", "CAU", "TUR", "CON"]):
            room_index = i
            location = line
            break
        else:
            groups.append(line)
    
    # Si on n'a pas trouvé de salle, utilisez les heuristiques
    if room_index == -1:
        # Cas rare, essayons une approche par défaut
        if len(lines) > 2:
            location = lines[2]
            room_index = 2
        else:
            location = ""
            room_index = len(lines)  # Après la fin
    
    # Joints les groupes en une chaîne
    group = ", ".join(groups)
    
    # Professeur et matière sont après la salle
    professor = ""
    exam_subject = ""
    
    # Vérifie s'il y a d'autres informations après la salle
    remaining_lines = lines[room_index+1:] if room_index < len(lines) else []
    
    if remaining_lines:
        # Détermine lesquelles sont le prof et lesquelles sont la matière
        for line in remaining_lines:
            if "Rattrapage Partiel" in line or "Matière" in line:
                exam_subject = line
            elif len(line.split()) <= 4:  # Les noms de profs sont généralement courts
                professor = line
    
    # Si on n'a pas encore identifié la matière mais qu'il reste une ligne
    if not exam_subject and remaining_lines and not professor:
        exam_subject = remaining_lines[0]
    elif not exam_subject and remaining_lines and professor and len(remaining_lines) > 1:
        exam_subject = remaining_lines[1]
    
    return event_type, group, "", location, professor, True, exam_subject, ""

def escape_ical_chars(text):
    """
    Échappe correctement les caractères spéciaux pour le format iCalendar selon RFC 5545
    """
    if not text:
        return ""
    
    # Échappe les caractères spéciaux dans l'ordre correct
    text = text.replace('\\', '\\\\')  # Backslash doit être échappé en premier
    text = text.replace(';', '\\;')    # Point-virgule
    text = text.replace(',', '\\,')    # Virgule
    text = text.replace('\n', '\\n')   # Saut de ligne
    
    return text

def create_ics_file(events_data, output_file='cy_calendar.ics'):
    """
    Crée un fichier ICS à partir des données du calendrier
    """
    # Crée le répertoire de sortie si nécessaire
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, 'generated')
    os.makedirs(output_dir, exist_ok=True)
    
    output_path = os.path.join(output_dir, output_file)
    
    cal = Calendar()
    cal.add('prodid', '-//CY University Calendar//FR')
    cal.add('version', '2.0')
    
    paris_tz = pytz.timezone('Europe/Paris')
    
    events_count = 0
    for event_data in events_data:
        try:
            event = Event()
            
            # Parse la description pour extraire les informations
            event_type, group, subject, location, professor, is_rattrapage, exam_subject, name = parse_description(event_data['description'])
            
            # Crée le résumé et la description selon le type d'événement
            if is_rattrapage:
                if exam_subject:
                    if "rattrapage" in exam_subject.lower():
                        summary = exam_subject
                    else:
                        summary = f"Rattrapage {exam_subject}"
                else:
                    summary = f"{event_type}"
                
                if professor:
                    description = f"{group}\nMatière: {exam_subject or 'Non spécifiée'}\nProfesseur: {professor}"
                else:
                    description = f"{group}\nMatière: {exam_subject or 'Non spécifiée'}"
            else:
                if not subject.strip():
                    summary = f"{group} - {event_type}"
                else:
                    summary = f"{subject} - {event_type}"
                
                description = f"{group}\nProfesseur: {professor}"
            
            # Ajoute les propriétés à l'événement
            event.add('summary', summary)
            event.add('location', location)
            event.add('description', description)
            
            # Ajoute les propriétés supplémentaires
            if 'backgroundColor' in event_data:
                event.add('X-ORIGINAL-BG-COLOR', event_data['backgroundColor'])
            
            try:
                # Parse les dates et heures
                start = datetime.strptime(event_data['start'], '%Y-%m-%dT%H:%M:%S')
                if not event_data.get('end'):
                    end = start + timedelta(hours=2)
                else:
                    end = datetime.strptime(event_data['end'], '%Y-%m-%dT%H:%M:%S')
                
                # Ajoute le fuseau horaire
                start = paris_tz.localize(start)
                end = paris_tz.localize(end)
                
                event.add('dtstart', start)
                event.add('dtend', end)
                
                # Ajoute le type d'événement
                if is_rattrapage:
                    event.add('X-EVENT-TYPE', 'rattrapage')
                else:
                    event.add('X-EVENT-TYPE', event_type)
                
                # Ajoute un UID unique
                event.add('uid', str(uuid.uuid4()))
                
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
    
    # Écrit le fichier ICS
    with open(output_path, 'wb') as f:
        f.write(cal.to_ical())
    
    print(f"Fichier ICS créé avec succès: {output_path} ({events_count} événements)")
    return output_path

def parse_ics_to_json(ics_file):
    """
    Convertit un fichier ICS en format JSON
    Utile pour importer des données ICS vers une autre API
    """
    events_data = []
    
    try:
        with open(ics_file, 'rb') as f:
            cal = Calendar.from_ical(f.read())
            
            for component in cal.walk():
                if component.name == "VEVENT":
                    event = {}
                    
                    # Récupère les propriétés de base
                    if component.get('summary'):
                        event['summary'] = str(component.get('summary'))
                    
                    if component.get('description'):
                        event['description'] = str(component.get('description'))
                    
                    if component.get('location'):
                        event['location'] = str(component.get('location'))
                    
                    if component.get('dtstart'):
                        start = component.get('dtstart').dt
                        if isinstance(start, datetime):
                            event['start'] = start.strftime('%Y-%m-%dT%H:%M:%S')
                        else:
                            event['start'] = datetime.combine(start, datetime.min.time()).strftime('%Y-%m-%dT%H:%M:%S')
                    
                    if component.get('dtend'):
                        end = component.get('dtend').dt
                        if isinstance(end, datetime):
                            event['end'] = end.strftime('%Y-%m-%dT%H:%M:%S')
                        else:
                            event['end'] = datetime.combine(end, datetime.min.time()).strftime('%Y-%m-%dT%H:%M:%S')
                    
                    # Récupère les propriétés personnalisées
                    if component.get('X-ORIGINAL-BG-COLOR'):
                        event['backgroundColor'] = str(component.get('X-ORIGINAL-BG-COLOR'))
                    
                    if component.get('X-EVENT-TYPE'):
                        event['eventCategory'] = str(component.get('X-EVENT-TYPE'))
                    
                    events_data.append(event)
        
        print(f"{len(events_data)} événements extraits du fichier ICS")
        return events_data
        
    except Exception as e:
        print(f"Erreur lors de la conversion du fichier ICS en JSON: {e}")
        return None

if __name__ == "__main__":
    from auth import get_auth_info
    
    cookie, student_id = get_auth_info()
    if cookie and student_id:
        events_data = get_calendar_data(cookie, student_id)
        if events_data:
            create_ics_file(events_data)