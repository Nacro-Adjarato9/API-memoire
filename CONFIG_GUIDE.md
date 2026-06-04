# ⚙️ Guide de Configuration & Déploiement

## 🚀 Démarrage Rapide Local

### Première Installation

```bash
# 1. Cloner/Naviguer au projet
cd "C:\Users\NACRO ADJARATOU\PROJET SOUTENANCE L3\APPLICATION WEB\API_DJANGO_WEB"

# 2. Activer l'environnement virtuel
.\venv\Scripts\Activate.ps1

# 3. Installer les dépendances
pip install -r requirements.txt  # (créer ce fichier ou installer manuellement)

# 4. Appliquer les migrations
python manage.py migrate

# 5. Créer un superuser (pour admin panel)
python manage.py createsuperuser

# 6. Lancer le serveur
python manage.py runserver 127.0.0.1:8000 --noreload

Sous Windows, tu peux aussi lancer:

```powershell
.\start_backend.ps1
```
```

Le serveur démarre sur: `http://127.0.0.1:8000/`

---

## 📦 Créer requirements.txt

```bash
# Générer automatiquement (depuis le venv actif)
pip freeze > requirements.txt

# Manuellement (si besoin):
# requirements.txt
Django==6.0.1
djangorestframework==3.16.1
djangorestframework-simplejwt==5.5.1
celery==5.6.3
redis==7.4.0
django-ratelimit==4.1.0
django-redis==6.0.0
django-cors-headers==4.9.0
Pillow==10.4.0
```

---

## 🔐 Configuration d'Email

### 1. Mode Console (Dev)
```python
# settings.py - Par défaut
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Emails s'affichent dans le terminal
```

### 2. Gmail SMTP

```python
# settings.py
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-specific-password'  # NOT your Gmail password!
DEFAULT_FROM_EMAIL = 'your-email@gmail.com'
```

**Générer App Password Gmail:**
1. Aller à [myaccount.google.com](https://myaccount.google.com/)
2. Security → App passwords
3. Sélectionner Mail & Windows Computer
4. Copier le mot de passe généré
5. Utiliser dans EMAIL_HOST_PASSWORD

### 3. SendGrid
```bash
pip install sendgrid

# settings.py
EMAIL_BACKEND = 'sendgrid_backend.SendgridBackend'
SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')
DEFAULT_FROM_EMAIL = 'your-email@sendgrid.com'
```

### 4. Mailgun
```bash
pip install django-anymail[mailgun]

# settings.py
EMAIL_BACKEND = 'anymail.backends.mailgun.EmailBackend'
ANYMAIL = {
    'MAILGUN_API_KEY': os.environ.get('MAILGUN_API_KEY'),
    'MAILGUN_SENDER_DOMAIN': 'your-domain.mailgun.org',
}
DEFAULT_FROM_EMAIL = 'hello@your-domain.com'
```

---

## 🔌 Configuration Celery pour Tasks Async

### 1. Installation
```bash
pip install celery redis
```

### 2. Créer celery.py

```python
# config/celery.py
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
```

### 3. Importer dans __init__.py

```python
# config/__init__.py
from .celery import app as celery_app

__all__ = ('celery_app',)
```

### 4. Settings Celery

```python
# settings.py
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
```

### 5. Créer une Task Async

```python
# utilisateurs/tasks.py
from celery import shared_task
from .emails import send_verification_email

@shared_task
def send_verification_email_async(user_id, token):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user = User.objects.get(id=user_id)
    send_verification_email(user, token)
```

### 6. Utiliser la Task

```python
# Dans RegisterView.perform_create()
from .tasks import send_verification_email_async

def perform_create(self, serializer):
    user = serializer.save()
    token = EmailVerificationTokenGenerator.generate_token(user)
    # Async task!
    send_verification_email_async.delay(user.id, token)  # Non-blocking
```

### 7. Lancer Celery Worker

```bash
# Terminal 1: Redis server
redis-server

# Terminal 2: Celery worker
celery -A config worker -l info

# Terminal 3: Django dev server
python manage.py runserver
```

---

## 🗄️ Migration vers PostgreSQL

### 1. Installation

```bash
pip install psycopg2-binary  # PostgreSQL adapter
```

### 2. Créer la Base de Données

```bash
# Sur PostgreSQL
CREATE DATABASE immobilier_db;
CREATE USER immobilier_user WITH PASSWORD 'strong_password';
ALTER ROLE immobilier_user SET client_encoding TO 'utf8';
ALTER ROLE immobilier_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE immobilier_user SET default_transaction_deferrable TO 'on';
GRANT ALL PRIVILEGES ON DATABASE immobilier_db TO immobilier_user;
```

### 3. Configurer Django

```python
# settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'immobilier_db',
        'USER': 'immobilier_user',
        'PASSWORD': 'strong_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### 4. Migrer les Données

```bash
# Dumper depuis SQLite
python manage.py dumpdata > data.json

# Charger dans PostgreSQL
python manage.py migrate
python manage.py loaddata data.json
```

---

## 🌐 Déployer sur Heroku

### 1. Préparer le Projet

```bash
# Installer CLI Heroku
# (Depuis: https://devcenter.heroku.com/articles/heroku-cli)

# Créer Procfile
echo "web: gunicorn config.wsgi" > Procfile

# Créer runtime.txt
echo "python-3.12.10" > runtime.txt

# Installer gunicorn
pip install gunicorn python-dotenv
pip freeze > requirements.txt
```

### 2. Configurer Settings pour Production

```python
# config/settings.py
import os
from pathlib import Path

# Production check
if 'DATABASE_URL' in os.environ:
    # Production environment
    DEBUG = False
    ALLOWED_HOSTS = ['your-app-name.herokuapp.com']
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    
    # Database from Heroku
    import dj_database_url
    DATABASES = {'default': dj_database_url.config()}
```

### 3. Déployer

```bash
# Login à Heroku
heroku login

# Créer app
heroku create your-app-name

# Set environment variables
heroku config:set SECRET_KEY='your-secret-key'
heroku config:set EMAIL_HOST_PASSWORD='gmail-app-password'
heroku config:set SENDGRID_API_KEY='your-sendgrid-key'

# Deploy via Git
git push heroku main

# Run migrations
heroku run python manage.py migrate

# Create superuser
heroku run python manage.py createsuperuser

# View logs
heroku logs --tail
```

---

## 🚀 Déployer sur Railway.app

### 1. Setup
```bash
# Installer Railway CLI
npm i -g @railway/cli

# Login
railway login

# Link project
railway init
```

### 2. Créer railway.toml
```toml
[build]
builder = "dockerfile"

[env]
DEBUG = "False"
SECRET_KEY = "${{ secrets.SECRET_KEY }}"
DATABASE_URL = "${{ Postgres.DATABASE_URL }}"
```

### 3. Déployer
```bash
railway up
```

---

## 🐳 Docker Deployment

### Créer Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health/')"

EXPOSE 8000

CMD ["gunicorn", "config.wsgi", "--bind", "0.0.0.0:8000", "--workers", "3"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: immobilier_db
      POSTGRES_USER: immobilier_user
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  web:
    build: .
    command: python manage.py runserver 0.0.0.0:8000
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    environment:
      DEBUG: "True"
      DATABASE_URL: postgresql://immobilier_user:password@db:5432/immobilier_db
      REDIS_URL: redis://redis:6379/0
    depends_on:
      - db
      - redis

  celery:
    build: .
    command: celery -A config worker -l info
    volumes:
      - .:/app
    environment:
      DEBUG: "True"
      DATABASE_URL: postgresql://immobilier_user:password@db:5432/immobilier_db
      REDIS_URL: redis://redis:6379/0
    depends_on:
      - db
      - redis

volumes:
  postgres_data:
```

### Lancer Docker

```bash
docker-compose up -d
docker-compose run web python manage.py migrate
docker-compose run web python manage.py createsuperuser
```

---

## 🧪 Tests & Quality

### Tests Unitaires

```bash
# Créer tests
python manage.py test

# Avec couverture
pip install coverage
coverage run --source='.' manage.py test
coverage report
coverage html  # Génère rapport HTML
```

### Linting & Format

```bash
pip install black flake8 isort

# Format code
black .
isort .

# Check errors
flake8 .
```

### Performance

```bash
pip install django-debug-toolbar django-extensions

# Dans settings.py pour dev uniquement
INSTALLED_APPS += ['debug_toolbar', 'django_extensions']
MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
INTERNAL_IPS = ['127.0.0.1']
```

---

## 📊 Monitoring en Production

### 1. Sentry.io (Error Tracking)

```bash
pip install sentry-sdk

# settings.py
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn="https://your-sentry-dsn@sentry.io/project-id",
    integrations=[DjangoIntegration()],
    traces_sample_rate=0.1,
    send_default_pii=False
)
```

### 2. New Relic (APM)

```bash
pip install newrelic

# Lancer avec monitoring
NEW_RELIC_CONFIG_FILE=newrelic.ini newrelic-admin run-program gunicorn config.wsgi
```

### 3. Logs Centralisés

```bash
# Avec ELK Stack (Elasticsearch, Logstash, Kibana)
pip install python-logstash

# settings.py
LOGGING = {
    'handlers': {
        'logstash': {
            'level': 'INFO',
            'class': 'logstash.TCPLogstashHandler',
            'host': 'logstash-server',
            'port': 5000,
            'version': 1,
            'message_type': 'django',
        },
    },
}
```

---

## ✅ Checklist Déploiement

### Avant le Déploiement
- [ ] DEBUG = False
- [ ] SECRET_KEY en variables d'env
- [ ] ALLOWED_HOSTS configuré
- [ ] HTTPS activé
- [ ] Database backups configurés
- [ ] Static files collectés
- [ ] Tests passent (100%+ coverage ideal)
- [ ] Code linting OK (flake8, black)
- [ ] Requirements.txt à jour
- [ ] .env et secrets non commités

### Après le Déploiement
- [ ] Email verification fonctionne
- [ ] Healthcheck endpoint OK
- [ ] Logs monitoring configuré
- [ ] Database migré
- [ ] Superuser créé
- [ ] CORS configuré pour frontend
- [ ] Rate limiting active
- [ ] Admin panel accessible
- [ ] API docs en ligne

---

## 🐛 Dépannage Courant

| Erreur | Cause | Solution |
|--------|-------|----------|
| Module not found | Dépendance manquante | `pip install package-name` |
| Connection refused | Redis/DB offline | Vérifier services |
| CORS error | Frontend domaine différent | Configurer CORS_ALLOWED_ORIGINS |
| Secret key invalid | Variable d'env manquante | `export SECRET_KEY='...'` |
| Static files 404 | collectstatic non exécuté | `python manage.py collectstatic` |
| Email non reçu | Backend/SMTP config | Vérifier EMAIL_BACKEND & credentials |
| Migrations conflicts | Merge branches | `python manage.py showmigrations` |

---

**Félicitations! L'API est prête pour production! 🎉**

**Support disponible pour:**
- Configuration serveur avancée
- Optimisation performance
- Scaling horizontal
- Intégration CI/CD
