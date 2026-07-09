# 🏠 LogeCiv - IA Immobilière Intelligente

Application Django complète avec **API IA Groq** intégrée pour la recherche immobilière en Côte d'Ivoire.

## 🚀 Démarrage Rapide

### 1. Installation des dépendances
```bash
pip install -r requirements.txt
```

### 2. Configuration de l'API Groq
```bash
# Créer le fichier .env avec la clé API
cp .env.example .env

# Éditer .env et ajouter votre clé (déjà configurée):
GROQ_API_KEY=your_groq_api_key_here
GROQ_API_URL=https://api.groq.com/openai/v1/chat/completions
GROQ_MODEL=mixtral-8x7b-32768
```

### 3. Base de données
```bash
# Migrations
python manage.py migrate

# Créer données de test (optionnel)
python manage.py loaddata test_data.json
```

### 4. Démarrer le serveur
```bash
python manage.py runserver
```

Le serveur est maintenant sur **http://localhost:8000/api**

---

## 📚 Endpoints API IA

### 🔍 Recherche Intelligente
```bash
POST /api/ia/recommendation/
```
Recherche immobilière avancée avec critères multiples.

### 💬 Chat Immobilier
```bash
POST /api/ia/chat/
```
Conversation naturelle avec l'IA pour trouver des logements.

### 💰 Conseil Budgétaire
```bash
POST /api/ia/budget-advisory/
```
Recommandations de villes selon le budget.

### 📋 Vérification de Documents
```bash
POST /api/ia/verify-document/
```
Vérification et validation de documents immobiliers.

---

## 🧪 Tests

### Tester tous les endpoints
```bash
python test_ia_api.py
```

### Tests unitaires
```bash
python manage.py test ia.test_ai_integration
```

---

## 📂 Structure du Projet

```
API_DJANGO_WEB/
├── config/              # Configuration Django
│   ├── settings.py      # Paramètres (inclut Groq API)
│   ├── urls.py          # Routes principales
│   └── wsgi.py
├── ia/                  # 🧠 Application IA principale
│   ├── views.py         # Endpoints API
│   ├── services.py      # Logique IA & recherche
│   ├── serializers.py   # Validation & sérialisation
│   ├── models.py        # Modèles de données
│   ├── urls.py          # Routes IA
│   └── tests.py         # Tests
├── biens/               # Gestion des logements
│   ├── models.py        # Modèle Bien & Document
│   ├── views.py
│   └── serializers.py
├── .env                 # Variables d'environnement (clé API)
├── .env.example         # Template .env
├── requirements.txt     # Dépendances Python
└── IA_DOCUMENTATION.md  # Documentation API détaillée
```

---

## 🤖 Fonctionnalités IA

### 1. Extraction Intelligente de Critères
```
Input: "Je cherche un appartement 3 chambres à Cocody pour 500000 FCFA"
Output: {
  "ville": "Cocody",
  "type_bien": "appartement",
  "nombre_chambres": 3,
  "budget_max": 500000
}
```

### 2. Recherche avec Alternatives
- ✅ Résultats directs si disponibles
- ✨ Propose zones alternatives intelligentes
- 💡 Élargit recherche progressivement
- 📊 Classe par rapport qualité-prix

### 3. Chat Conversationnel
- Comprend l'intention utilisateur
- Pose des questions de clarification
- Suggère villes adaptées au budget
- Fournit conseils pratiques

### 4. Vérification de Documents
- 🔐 Valide cohérence & authenticité
- ⚠️ Détecte risques de fraude
- 📋 Recommande actions à prendre
- 🛡️ Score de confiance

---

## 🌍 Zones Abidjan Reconnues

L'IA comprend automatiquement :
- Cocody, Riviera, Angré, Bingerville
- Marcory, Treichville, Koumassi
- Yopougon, Abobo, Adjamé
- Plateau, Gesco, Niangon

---

## 🏙️ Villes Secondaires

L'IA recommande intelligemment :

| Budget | Villes recommandées |
|--------|-------------------|
| 50K-100K | Korhogo, Daloa |
| 100K-150K | Yamoussoukro, Gagnoa, Man |
| 150K-250K | Bouaké, San Pedro, Abengourou |

---

## 🔐 Sécurité

- ✅ Validation de tous les inputs
- ✅ Clé API sécurisée en variables d'environnement
- ✅ HTTPS recommandé en production
- ✅ Rate limiting sur endpoints IA

---

## ⚙️ Configuration Avancée

### Variables d'environnement
```bash
# IA
GROQ_API_KEY=votre_clé
GROQ_API_URL=https://api.groq.com/openai/v1/chat/completions
GROQ_MODEL=mixtral-8x7b-32768

# Django
DEBUG=True
SECRET_KEY=votre_clé_secrète
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_ENGINE=django.db.backends.sqlite3
DB_NAME=db.sqlite3
```

### Production
```bash
# Avec Gunicorn
gunicorn config.wsgi --bind 0.0.0.0:8000

# Avec Nginx (reverse proxy)
# Configuration Nginx requise pour HTTPS
```

---

## 🐛 Dépannage

### "IA key missing"
```bash
# Vérifiez le fichier .env
cat .env | grep GROQ_API_KEY

# Si vide, mettez à jour:
export GROQ_API_KEY=your_groq_api_key_here
```

### "Connection refused"
```bash
# Assurez-vous que Django tourne
python manage.py runserver

# Port 8000 en écoute?
lsof -i :8000
```

### "No results found"
- Normal ! L'IA propose toujours des alternatives
- Vérifiez les données en base : `python manage.py shell`

---

## 📖 Documentation Détaillée

Voir **IA_DOCUMENTATION.md** pour :
- Exemples API complets
- Tous les types de documents acceptés
- Paramètres de recherche avancés
- Meillures pratiques

---

## 🛠️ Développement

### Format du code
```bash
# Black code formatter
black ia/ --line-length 100

# Lint
flake8 ia/ --max-line-length=100
```

### Ajouter une nouvelle fonctionnalité IA
1. Ajouter fonction dans `ia/services.py`
2. Créer endpoint dans `ia/views.py`
3. Ajouter serializer si nécessaire
4. Créer tests dans `ia/tests.py`
5. Mettre à jour URLs dans `ia/urls.py`

---

## 📞 Support

Pour des questions ou problèmes :
1. Vérifiez la documentation : `IA_DOCUMENTATION.md`
2. Consultez les tests : `ia/test_ai_integration.py`
3. Vérifiez les logs Django

---

## 📄 Licence

© 2024 LogeCiv - Tous droits réservés

---

**Prêt à commencer ? 🚀**
```bash
python manage.py runserver
# Accédez à http://localhost:8000/api/ia/chat/
```
