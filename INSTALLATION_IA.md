# Installation et Configuration IA LogeCiv

## Prérequis
- Python 3.10+
- pip (gestionnaire de paquets Python)
- Git (optionnel)

## Étape 1 : Cloner/Accéder au projet

```bash
cd "C:\Users\NACRO ADJARATOU\PROJET SOUTENANCE L3\APPLICATION WEB\API_DJANGO_WEB"
```

## Étape 2 : Créer un environnement virtuel (recommandé)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

## Étape 3 : Installer les dépendances

```bash
pip install -r requirements.txt
```

### Dépendances principales installées :
- Django 6.0.1
- Django REST Framework
- Requests (pour API Groq)
- Python-dotenv (pour variables d'environnement)
- Groq SDK (optionnel mais recommandé)

## Étape 4 : Configurer l'API Groq

### Créer le fichier .env
```bash
cp .env.example .env
```

### Contenu du .env (déjà configuré) :
```
GROQ_API_KEY=your_groq_api_key_here
GROQ_API_URL=https://api.groq.com/openai/v1/chat/completions
GROQ_MODEL=mixtral-8x7b-32768
```

**⚠️ Sécurité** : Ne commitez JAMAIS le fichier .env avec les vraies clés !

## Étape 5 : Base de données

```bash
# Appliquer les migrations
python manage.py migrate

# Créer un superutilisateur (optionnel)
python manage.py createsuperuser
```

## Étape 6 : Démarrer le serveur

```bash
python manage.py runserver
```

Le serveur démarre sur **http://localhost:8000**

API IA disponible sur : **http://localhost:8000/api/ia/**

## Vérification de l'installation

### Test rapide :
```bash
# Dans une autre console
PYTHONIOENCODING=utf-8 python test_ia_api.py
```

### Test avec curl (chat IA) :
```bash
curl -X POST http://localhost:8000/api/ia/chat/ \
  -H "Content-Type: application/json" \
  -d '{"message": "Je cherche un appartement a Cocody avec 500000 FCFA"}'
```

### Test avec Python requests :
```python
import requests

response = requests.post(
    "http://localhost:8000/api/ia/chat/",
    json={"message": "Je cherche un studio abordable"}
)
print(response.json())
```

## 🚀 Endpoints Disponibles

| Méthode | Endpoint | Fonction |
|---------|----------|----------|
| POST | `/api/ia/chat/` | Chat conversationnel |
| POST | `/api/ia/recommendation/` | Recherche intelligente |
| POST | `/api/ia/budget-advisory/` | Conseils budgétaires |
| POST | `/api/ia/verify-document/` | Vérification documents |

## 📋 Exemple d'utilisation - Chat IA

```bash
curl -X POST http://localhost:8000/api/ia/chat/ \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Je veux un appartement 2 chambres a Bingerville, pas cher"
  }'
```

Réponse :
```json
{
  "message": "Je veux un appartement 2 chambres a Bingerville, pas cher",
  "reponse": "J'ai trouvé plusieurs options intéressantes...",
  "criteres": {
    "ville": "Bingerville",
    "nombre_chambres": 2,
    "type_bien": "appartement"
  },
  "resultats": [
    {
      "id": 1,
      "titre": "Appartement Bingerville",
      "prix": "250000",
      "nombre_chambres": 2
    }
  ]
}
```

## 🔧 Commandes utiles

### Voir logs de Django
```bash
python manage.py runserver --verbosity=2
```

### Accéder à Django Shell (pour tests)
```bash
python manage.py shell
```

Exemple en shell :
```python
from ia.services import chat_immobilier
result = chat_immobilier("Appartement 2 chambres a Cocody")
print(result)
```

### Tester les migrations
```bash
python manage.py migrate --dry-run
```

### Recréer la base de données
```bash
# ⚠️ Cela supprime tout !
python manage.py flush
python manage.py migrate
```

## 🐛 Dépannage

### Erreur : "ModuleNotFoundError: No module named 'django'"
```bash
# Réinstaller les dépendances
pip install -r requirements.txt
```

### Erreur : "IA key missing"
```bash
# Vérifier que le fichier .env existe et contient la clé
cat .env | grep GROQ_API_KEY

# Si vide, ajouter :
export GROQ_API_KEY=your_groq_api_key_here
```

### Erreur : "Port 8000 already in use"
```bash
# Utiliser un autre port
python manage.py runserver 8001

# Ou tuer le processus qui utilise le port 8000 (Linux/Mac)
lsof -i :8000 | grep -v PID | awk '{print $2}' | xargs kill -9
```

### API Groq lente
- C'est normal, Groq met 1-3 secondes par réponse
- L'IA tente automatiquement un fallback local après 30s

## 📚 Documentation supplémentaire

Consultez :
- `IA_DOCUMENTATION.md` - Documentation complète API
- `IA_README.md` - Guide utilisateur IA
- `ia/tests.py` - Exemples de code

## 🎯 Prochaines étapes

1. **Charger des données de test**
   ```bash
   python manage.py loaddata test_data.json
   ```

2. **Accéder à l'admin Django**
   ```
   http://localhost:8000/admin
   ```

3. **Déployer en production**
   - Voir section Production dans IA_README.md
   - Configurer Gunicorn/Nginx
   - HTTPS obligatoire

## ✅ Checklist d'installation

- [ ] Python 3.10+ installé
- [ ] Environnement virtuel créé et activé
- [ ] Dépendances installées : `pip install -r requirements.txt`
- [ ] Fichier .env créé avec clé API
- [ ] Migrations appliquées : `python manage.py migrate`
- [ ] Serveur démarre sans erreur
- [ ] API répond : `curl http://localhost:8000/api/ia/chat/`

## 🎉 Installation complète !

Vous êtes prêt à utiliser l'IA immobilière LogeCiv. 

Consultez `IA_DOCUMENTATION.md` pour apprendre à utiliser tous les endpoints.

Besoin d'aide ? Vérifiez les logs ou consultez les tests dans `test_ia_api.py`.
