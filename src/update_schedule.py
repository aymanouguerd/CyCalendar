import os
import random
import re
from datetime import datetime

def generate_random_schedule():
    """
    Génère une heure aléatoire entre 18h et 20h et une minute aléatoire
    Format: HH:MM
    """
    hour = random.randint(18, 19)
    minute = random.randint(0, 59)
    return f"{hour}:{minute:02d}"

def update_github_workflow(time_str):
    """
    Met à jour le fichier de workflow GitHub Actions avec une nouvelle programmation
    """
    workflow_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.github', 'workflows', 'update_calendar.yml')
    
    if not os.path.exists(workflow_path):
        print(f"Erreur: Le fichier {workflow_path} n'existe pas.")
        return False
    
    try:
        with open(workflow_path, 'r') as file:
            content = file.read()
        
        # Extraire l'heure UTC à partir du temps local (Paris = UTC+2 en été, UTC+1 en hiver)
        now = datetime.now()
        # Supposons UTC+2 pour simplifier (à adapter selon la saison)
        local_hour, local_minute = map(int, time_str.split(':'))
        utc_hour = (local_hour - 2) % 24  # Conversion en UTC (UTC+2)
        
        # Remplacer le cron schedule
        # Format: "minute heure * * *"
        new_cron = f"{local_minute} {utc_hour} * * *"
        
        # Rechercher et remplacer le cron existant
        pattern = r'(cron:\s*")([0-9]+\s+[0-9]+\s+\*\s+\*\s+\*)(\")'
        if re.search(pattern, content):
            new_content = re.sub(pattern, f'\\1{new_cron}\\3', content)
            
            # Écrire le nouveau contenu
            with open(workflow_path, 'w') as file:
                file.write(new_content)
                
            print(f"Schedule mis à jour avec succès: exécution à {time_str} local / {utc_hour}:{local_minute:02d} UTC")
            return True
        else:
            print("Modèle de cron non trouvé dans le fichier workflow.")
            return False
            
    except Exception as e:
        print(f"Erreur lors de la mise à jour du workflow: {str(e)}")
        return False

if __name__ == "__main__":
    random_time = generate_random_schedule()
    print(f"Génération d'un nouveau planning: {random_time}")
    success = update_github_workflow(random_time)
    if success:
        print("Le fichier de workflow a été mis à jour avec succès.")
    else:
        print("Échec de la mise à jour du workflow.")