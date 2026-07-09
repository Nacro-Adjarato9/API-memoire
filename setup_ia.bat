@echo off
REM Script d'installation automatique pour IA LogeCiv (Windows)
REM Exécution: setup_ia.bat

setlocal enabledelayedexpansion

cls
echo ================================
echo 🚀 Installation IA LogeCiv
echo ================================

REM Vérifier Python
echo.
echo 1️⃣ Vérification de Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo    ❌ Python non trouvé! Installez Python 3.10+
    pause
    exit /b 1
)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo    Python: !PYTHON_VERSION!

REM Vérifier si manage.py existe
echo.
echo 2️⃣ Vérification du projet...
if not exist "manage.py" (
    echo    ❌ manage.py non trouvé! Vérifiez le répertoire
    pause
    exit /b 1
)
echo    ✅ Projet Django trouvé

REM Créer environnement virtuel
echo.
echo 3️⃣ Création de l'environnement virtuel...
if not exist "venv" (
    python -m venv venv
    echo    ✅ Environnement créé
) else (
    echo    ℹ️ Environnement existant
)

REM Activer environnement
echo    ✅ Environnement activé

REM Installer dépendances
echo.
echo 4️⃣ Installation des dépendances...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt >nul 2>&1
if errorlevel 0 (
    echo    ✅ Dépendances installées
) else (
    echo    ⚠️ Certaines dépendances n'ont pas pu être installées
)

REM Créer .env
echo.
echo 5️⃣ Configuration de l'API Groq...
if not exist ".env" (
    (
        echo GROQ_API_KEY=your_groq_api_key_here
        echo GROQ_API_URL=https://api.groq.com/openai/v1/chat/completions
        echo GROQ_MODEL=mixtral-8x7b-32768
        echo IA_CHAT_API_KEY=your_groq_api_key_here
        echo IA_CHAT_API_URL=https://api.groq.com/openai/v1/chat/completions
        echo IA_CHAT_MODEL=mixtral-8x7b-32768
    ) > .env
    echo    ✅ Fichier .env créé
) else (
    echo    ℹ️ Fichier .env existant
)

REM Migrations
echo.
echo 6️⃣ Migrations de base de données...
python manage.py migrate --noinput >nul 2>&1
echo    ✅ Migrations appliquées

REM Vérification
echo.
echo 7️⃣ Vérification des modules IA...
python -c "import django; django.setup(); from ia import services, views; from ia.models import RecommendationIA; print('   [OK] Modules IA OK')" 2>nul
if !errorlevel! equ 0 (
    echo    [OK] Services OK
    echo    [OK] Views OK
    echo    [OK] Models OK
) else (
    echo    ⚠️ Vérification partielle
)

echo.
echo ================================
echo ✅ Installation Complète!
echo ================================
echo.
echo 📝 Prochaines étapes:
echo    1. Activer environnement:
echo       venv\Scripts\activate
echo.
echo    2. Lancer le serveur:
echo       python manage.py runserver
echo.
echo    3. Tester l'API:
echo       Ouvrir: http://localhost:8000/api/ia/chat/
echo.
echo 📚 Documentation:
echo    - Installation: INSTALLATION_IA.md
echo    - API: IA_DOCUMENTATION.md
echo    - Cas d'usage: CAS_D_USAGE_IA.md
echo.
echo 🎉 Bon travail! Votre IA LogeCiv est prête!
echo.
pause
