@echo off
cd /d "%~dp0"
echo Demarrage du serveur Django (accessible depuis le telephone)...
call venv\Scripts\activate.bat
python manage.py runserver 0.0.0.0:8000
pause
