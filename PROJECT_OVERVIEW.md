# LogCiv — Présentation du projet

## 1) Résumé
LogCiv est une API REST Django pour une plateforme immobilière. Elle permet l’inscription des utilisateurs (locataires, propriétaires, agences), la gestion des biens, des réservations, des favoris, des avis, des messages, des notifications et des abonnements. Le projet intègre aussi des fonctionnalités d’IA pour la recherche intelligente et la recommandation.

## 2) Objectifs
- Centraliser la gestion des biens immobiliers
- Faciliter la recherche et la réservation de biens
- Offrir une messagerie intégrée entre utilisateurs
- Gérer les abonnements et tarifs
- Améliorer l’expérience via l’IA (recherche, recommandation, vérification de documents)

## 3) Architecture technique
- **Framework** : Django + Django REST Framework
- **Auth** : JWT (SimpleJWT)
- **Documentation** : Swagger / Redoc
- **Base de données** : SQLite en dev (PostgreSQL recommandé en prod)
- **Tâches asynchrones** : Celery + Redis (config présent)

## 4) Applications principales
- **utilisateurs** : gestion profils, rôles, vérification, signalements
- **biens** : CRUD biens, documents
- **images** : images liées aux biens
- **reservations** : réservations et statuts
- **favoris** : favoris d’un utilisateur
- **avis** : notes et commentaires
- **chat** : messagerie
- **notifications** : alertes utilisateurs
- **agences** : gestion agences
- **tarifs** : plans et abonnements
- **ia** : recommandations, recherche, vérification doc

## 5) Fonctionnalités clés
- Inscription + login JWT
- CRUD biens + filtres avancés
- Réservations et calendrier
- Favoris + avis
- Messagerie interne
- Notifications
- Tarifs & abonnements
- IA : recommandations, recherche intelligente, vérification de documents

## 6) Exemples d’endpoints
- `POST /api/auth/register/`
- `POST /api/auth/login/`
- `GET /api/biens/`
- `POST /api/biens/`
- `POST /api/reservations/`
- `GET /api/avis/`
- `POST /api/messages/`
- `GET /api/notifications/`
- `GET /api/tarifs/`
- `POST /api/ia/recherche/rechercher/`

## 7) IA — rôle dans le projet
- **Recherche intelligente** : interprète les requêtes en langage naturel
- **Recommandation** : propose des biens personnalisés
- **Vérification** : aide à vérifier documents (CNI, registre, etc.)

## 8) Démarrage rapide
```powershell
# Activer l’environnement
.\venv\Scripts\Activate.ps1

# Migrer la base
python manage.py migrate

# Créer un admin
python manage.py createsuperuser

# Lancer le serveur
python manage.py runserver
```

## 9) Documentation API
- Swagger : `http://127.0.0.1:8000/swagger/`
- Redoc : `http://127.0.0.1:8000/redoc/`
- API root : `http://127.0.0.1:8000/api/`

## 10) Notes
- En production, activer `DEBUG=False`
- Configurer `ALLOWED_HOSTS`
- Remettre `IsAuthenticated` si besoin

---

Ce document est un résumé fonctionnel du projet LogCiv.
