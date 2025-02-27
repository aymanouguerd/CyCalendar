import base64
import os

def token_to_base64():
    token_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'google', 'token.pickle')
    
    try:
        # Lire le fichier token.pickle
        with open(token_path, 'rb') as token_file:
            token_bytes = token_file.read()
        
        # Convertir en base64
        token_base64 = base64.b64encode(token_bytes).decode('utf-8')
        
        # Afficher le token en base64
        print(token_base64)
            
    except FileNotFoundError:
        print("Erreur: Le fichier token.pickle n'a pas été trouvé.")
    except Exception as e:
        print(f"Une erreur est survenue: {str(e)}")

if __name__ == "__main__":
    token_to_base64()