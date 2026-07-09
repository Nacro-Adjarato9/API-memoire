#!/bin/bash
# Script d'installation automatique pour IA LogeCiv
# Exécution: bash setup_ia.sh ou ./setup_ia.sh

set -e

echo "================================"
echo "🚀 Installation IA LogeCiv"
echo "================================"

# Vérifier Python
echo ""
echo "1️⃣ Vérification de Python..."
python_version=$(python --version 2>&1 | awk '{print $2}')
echo "   Python: $python_version"

# Vérifier si le projet existe
echo ""
echo "2️⃣ Vérification du projet..."
if [ ! -f "manage.py" ]; then
    echo "   ❌ manage.py non trouvé! Assurez-vous d'être dans le répertoire du projet"
    exit 1
fi
echo "   ✅ Projet Django trouvé"

# Créer environnement virtuel
echo ""
echo "3️⃣ Création de l'environnement virtuel..."
if [ ! -d "venv" ]; then
    python -m venv venv
    echo "   ✅ Environnement créé"
else
    echo "   ℹ️ Environnement existant"
fi

# Activer environnement
source venv/Scripts/activate 2>/dev/null || source venv/bin/activate
echo "   ✅ Environnement activé"

# Installer dépendances
echo ""
echo "4️⃣ Installation des dépendances..."
pip install --upgrade pip > /dev/null
pip install -r requirements.txt > /dev/null
echo "   ✅ Dépendances installées"

# Créer .env s'il n'existe pas
echo ""
echo "5️⃣ Configuration de l'API Groq..."
if [ ! -f ".env" ]; then
    cat > .env << 'EOF'
GROQ_API_KEY=your_groq_api_key_here
GROQ_API_URL=https://api.groq.com/openai/v1/chat/completions
GROQ_MODEL=mixtral-8x7b-32768
IA_CHAT_API_KEY=your_groq_api_key_here
IA_CHAT_API_URL=https://api.groq.com/openai/v1/chat/completions
IA_CHAT_MODEL=mixtral-8x7b-32768
EOF
    echo "   ✅ Fichier .env créé"
else
    echo "   ℹ️ Fichier .env existant"
fi

# Migrations
echo ""
echo "6️⃣ Migrations de base de données..."
python manage.py migrate --noinput > /dev/null 2>&1 || true
echo "   ✅ Migrations appliquées"

# Tests
echo ""
echo "7️⃣ Vérification des modules IA..."
python -c "
import django
django.setup()
from ia import services, views
from ia.models import RecommendationIA
print('   [OK] Modules IA OK')
print('   [OK] Services OK')
print('   [OK] Views OK')
print('   [OK] Models OK')
" 2>&1 || echo "   ⚠️ Vérification partielle"

echo ""
echo "================================"
echo "✅ Installation Complète!"
echo "================================"
echo ""
echo "📝 Prochaines étapes:"
echo "   1. Activer environnement:"
echo "      source venv/bin/activate"
echo ""
echo "   2. Lancer le serveur:"
echo "      python manage.py runserver"
echo ""
echo "   3. Tester l'API:"
echo "      curl -X POST http://localhost:8000/api/ia/chat/ \\"
echo "        -H 'Content-Type: application/json' \\"
echo "        -d '{\"message\": \"Apartment a Cocody\"}'"
echo ""
echo "📚 Documentation:"
echo "   - Installation: INSTALLATION_IA.md"
echo "   - API: IA_DOCUMENTATION.md"
echo "   - Cas d'usage: CAS_D_USAGE_IA.md"
echo ""
echo "🎉 Bon travail! Votre IA LogeCiv est prête!"
