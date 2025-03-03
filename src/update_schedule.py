import os
import random
import re
from datetime import datetime

def generate_random_schedule():
    """
    Génère une heure aléatoire entre 18h et 20h et une minute aléatoire
    Format: HH:MM
    """
    # Choix d'une heure aléatoire entre 18h et 19h (donc jusqu'à 19h59)
    hour = random.randint(18, 19)
    # Choix d'une minute aléatoire entre 0 et 59
    minute = random.randint(0, 59)
    # Formatage de l'heure avec minutes à deux chiffres (ex: 18:05 et non 18:5)
    return f"{hour}:{minute:02d}"

def update_github_workflow(time_str):
    """
    Met à jour le fichier de workflow GitHub Actions avec une nouvelle programmation
    
    Args:
        time_str (str): L'heure au format "HH:MM" à définir pour la prochaine exécution
        
    Returns:
        bool: True si la mise à jour a réussi, False sinon
    """
    # Chemin complet vers le fichier workflow à modifier
    workflow_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.github', 'workflows', 'update_calendar.yml')
    
    # Vérification que le fichier existe
    if not os.path.exists(workflow_path):
        print(f"Erreur: Le fichier {workflow_path} n'existe pas.")
        return False
    
    try:
        # Lecture du fichier ligne par ligne
        with open(workflow_path, 'r') as file:
            lines = file.readlines()
        
        # Extraction de l'heure et des minutes depuis la chaîne "HH:MM"
        local_hour, local_minute = map(int, time_str.split(':'))
        
        # Format pour la syntaxe cron: "minute heure * * *" (* = tous les jours/mois/jours de la semaine)
        # Note: GitHub Actions utilise UTC comme timezone, donc cette heure sera interprétée comme UTC
        # Pour l'exécuter à 18h-20h heure française (UTC+1/UTC+2), il faudrait ajuster l'heure en conséquence
        new_cron = f"{local_minute} {local_hour} * * *"
        
        # Recherche de la ligne contenant la définition du cron
        found = False
        for i, line in enumerate(lines):
            if "cron:" in line:
                # Remplacement complet de la ligne, en préservant l'indentation
                indent = re.match(r'^(\s*)', line).group(1)
                lines[i] = f'{indent}- cron: "{new_cron}" # Prochaine exécution à {time_str} (heure locale)\n'
                found = True
                break
        
        # Si on a trouvé et modifié la ligne du cron
        if found:
            # Écriture du fichier modifié
            with open(workflow_path, 'w') as file:
                file.writelines(lines)
            
            print(f"Schedule mis à jour avec succès: exécution à {time_str} (heure locale)")
            return True
        else:
            # En cas d'échec, affichage d'informations de débogage
            print("Aucune ligne contenant 'cron:' n'a été trouvée dans le fichier.")
            print("Contenu des 10 premières lignes:")
            for i, line in enumerate(lines[:10]):
                print(f"{i+1}: {line.strip()}")
            return False
            
    except Exception as e:
        # Gestion des erreurs avec affichage de la trace complète
        print(f"Erreur lors de la mise à jour du workflow: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

# Point d'entrée principal du script
if __name__ == "__main__":
    # Génération d'une nouvelle heure d'exécution aléatoire
    random_time = generate_random_schedule()
    print(f"Génération d'un nouveau planning: {random_time} (heure locale)")
    
    # Mise à jour du fichier workflow avec cette nouvelle heure
    success = update_github_workflow(random_time)
    
    # Affichage du résultat
    if success:
        print("Le fichier de workflow a été mis à jour avec succès.")
    else:
        print("Échec de la mise à jour du workflow.")