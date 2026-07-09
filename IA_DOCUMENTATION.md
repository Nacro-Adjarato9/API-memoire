# 🏠 API IA LogeCiv - Documentation Complète

## Vue d'ensemble

LogeCiv dispose d'une **IA intelligente** basée sur **Groq** pour :
- 🔍 Recherche immobilière avancée
- 💬 Chat conversationnel
- 📋 Vérification de documents
- 💰 Conseils budgétaires

---

## 1️⃣ Recherche Intelligente

### Endpoint
```
POST /api/ia/recommendation/
POST /api/ia/recherche/rechercher/
```

### Paramètres
```json
{
  "texte": "Texte libre pour recherche",
  "ville": "Cocody",
  "quartier": "Riviera",
  "type_bien": "appartement",
  "budget_min": 100000,
  "budget_max": 500000,
  "nombre_chambres": 2,
  "nombre_salles_bain": 1,
  "superficie_min": 60,
  "superficie_max": 200,
  "meuble": true,
  "parking": true,
  "piscine": false,
  "securite": true,
  "proximite": "école, commerce",
  "statut": "location"
}
```

### Réponse réussie
```json
{
  "type": "resultats",
  "message": "Voici des logements correspondant à votre recherche...",
  "analyse_ia": "Analyse détaillée par IA",
  "criteres": {...},
  "resultats": [
    {
      "id": 1,
      "titre": "Appartement Cocody",
      "prix": "500000",
      "ville": "Cocody",
      "type": "appartement",
      "nombre_chambres": 2,
      "meuble": true,
      "parking": true,
      "securite": true
    }
  ],
  "suggestions": [],
  "recommendation_id": 123
}
```

---

## 2️⃣ Chat Immobilier

### Endpoint
```
POST /api/ia/chat/
```

### Request
```json
{
  "message": "Je cherche un appartement pas cher à Cocody avec 300000 FCFA"
}
```

### Réponse
```json
{
  "message": "Je cherche un appartement pas cher à Cocody...",
  "reponse": "Voici ce que j'ai trouvé pour vous...",
  "criteres": {
    "ville": "Cocody",
    "budget_max": 300000,
    "type_bien": "appartement"
  },
  "resultats": [
    {
      "id": 1,
      "titre": "Appartement Cocody",
      "prix": "250000",
      "nombre_chambres": 2
    }
  ],
  "suggestions": []
}
```

### Exemples de messages
- "Je veux un studio à Yopougon avec 100000 FCFA"
- "Maison 3 chambres à Bingerville, sécurisée"
- "Déménager à l'intérieur avec 80000 FCFA"

---

## 3️⃣ Conseil Budgétaire

### Endpoint
```
POST /api/ia/budget-advisory/
```

### Request
```json
{
  "budget": 150000
}
```

### Réponse
```json
{
  "budget": 150000,
  "villes_recommandees": [
    {
      "ville": "Yamoussoukro",
      "prix_range": "50000 - 180000 FCFA",
      "description": "Capitale politique, cadre calme",
      "match_score": 95
    },
    {
      "ville": "Daloa",
      "prix_range": "40000 - 150000 FCFA",
      "description": "Zone agricole, très abordable",
      "match_score": 85
    }
  ],
  "conseil_ia": "Avec ce budget, Yamoussoukro offre..."
}
```

---

## 4️⃣ Vérification de Documents

### Endpoint
```
POST /api/ia/verify-document/
POST /api/ia/verifier-document/verifier/
```

### Request
```json
{
  "document_url": "https://example.com/document.jpg",
  "document_type": "cni",
  "document_data": {
    "numero": "123456789",
    "date_expiration": "2025-12-31"
  }
}
```

### Types de documents acceptés
- `cni` - Carte Nationale d'Identité
- `passeport` - Passeport
- `rccm` - Registre de Commerce
- `acte_propriete` - Acte de Propriété
- `justif_propriete` - Justificatif de Propriété

### Réponse
```json
{
  "verdict": "Valide",
  "confidence": 85,
  "message": "Document valide et cohérent",
  "details": {
    "type_document": "Carte Nationale d'Identité",
    "qualite": "Bon",
    "authentique": true,
    "risques": [],
    "recommandations": [
      "Vérifier auprès des autorités officielles",
      "Confirmer l'authenticité du numéro"
    ]
  },
  "ai_analysis": "..."
}
```

### Verdicts possibles
- ✅ `Valide` - Document accepté
- ⚠️ `Suspect` - Besoin de vérification supplémentaire
- ❌ `Incomplet` - Informations manquantes

---

## 🎯 Villes Recommandées par Budget

| Ville | Budget optimal | Description |
|-------|-----------------|-------------|
| 🏙️ Bouaké | 50K-200K | 2e ville, dynamique |
| 🏛️ Yamoussoukro | 50K-180K | Capitale, calme |
| 🌾 Daloa | 40K-150K | Très abordable |
| 🏞️ Korhogo | 35K-120K | Nord ivoirien |
| ⛴️ San Pedro | 60K-200K | Port actif |
| 🗻 Man | 40K-130K | Cadre naturel |
| 🌳 Gagnoa | 40K-140K | Centre-Ouest |
| 🏗️ Abengourou | 45K-160K | Croissance urbaine |
| 🏖️ Aboisso | 50K-170K | Sud-Est tranquille |

---

## 🔑 Configuration API

### Variables d'environnement
```bash
GROQ_API_KEY=your_groq_api_key_here
GROQ_API_URL=https://api.groq.com/openai/v1/chat/completions
GROQ_MODEL=mixtral-8x7b-32768
```

### Installation
```bash
# Installer python-dotenv
pip install python-dotenv

# Créer fichier .env
cp .env.example .env

# Charger les variables
source .env
```

---

## 📊 Logique Intelligente

### Extraction automatique de critères
L'IA extrait automatiquement les critères du texte libre :
- `"500000"` → `budget_max: 500000`
- `"appartement"` → `type_bien: "appartement"`
- `"Cocody"` → `ville: "Cocody"`
- `"2 chambres"` → `nombre_chambres: 2`

### Alternatives intelligentes
Si pas de résultats :
1. Cherche dans quartiers proches
2. Propose villes secondaires avec budget adapté
3. Élargit la recherche progressive
4. Suggère les meilleurs rapports qualité-prix

### Vérification de documents
1. Valide le type de document
2. Analyse la cohérence des données
3. Détecte les risques de fraude
4. Recommande des actions

---

## 🧪 Tests

Exécuter les tests :
```bash
python manage.py test ia.test_ai_integration
```

---

## 🚀 Déploiement

### Production
```bash
# Variables sécurisées
export GROQ_API_KEY=your_key
export DEBUG=False

# Migrations
python manage.py migrate

# Lancer serveur
gunicorn config.wsgi
```

---

## ⚡ Performance

- ⏱️ Temps de réponse : ~1-3 secondes
- 📦 Cache local pour suggestions récentes
- 🔄 Retry automatique en cas d'erreur API
- 🛡️ Fallback local si API indisponible

---

## 🔐 Sécurité

- ✅ Validation de tous les inputs
- ✅ Sanitization des URLs de documents
- ✅ Rate limiting sur les endpoints IA
- ✅ Stockage sécurisé des clés API
- ✅ HTTPS requis en production

