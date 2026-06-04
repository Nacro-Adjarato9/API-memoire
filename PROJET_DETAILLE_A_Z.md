# Projet LogCiv - API Immobilière Django

## 1. Présentation générale

LogCiv est une API REST Django conçue pour une plateforme immobilière complète. Elle gère les utilisateurs, les biens, les réservations, les messages, les favoris, les avis, les notifications, les agences, les tarifs et les fonctionnalités d'IA. L'objectif est de fournir un backend robuste capable de servir un frontend web ou mobile.

## 2. Objectifs du projet

- Centraliser la gestion des biens immobiliers.
- Permettre la recherche et la réservation de biens.
- Offrir une messagerie interne entre utilisateurs.
- Gérer les avis, les favoris et les notifications.
- Proposer des fonctionnalités avancées comme les abonnements et les recommandations IA.
- Assurer une sécurité fiable avec JWT et validation d'e-mail.

## 3. Architecture technique

- Framework principal : **Django**.
- API : **Django REST Framework**.
- Authentification : **JWT** via SimpleJWT.
- Documentation API : **Swagger** et **ReDoc**.
- Base de données : **SQLite** en développement, PostgreSQL recommandé en production.
- Tâches asynchrones : **Celery** et **Redis** (configuration présente).
- Stockage d'images et de documents géré via des modèles Django.

## 4. Structure du projet

```
API_DJANGO_WEB/
├── agences/
├── avis/
├── biens/
├── chat/
├── config/
├── documents/
├── favoris/
├── images/
├── notifications/
├── reservations/
├── tarifs/
├── utilisateurs/
├── ia/
├── templates/emails/
├── db.sqlite3
├── manage.py
├── README.md
├── README_COMPLETE.md
├── API_DOCUMENTATION.md
├── CONFIG_GUIDE.md
├── SECURITY_NOTES.md
└── PROJET_DETAILLE_A_Z.md
```

## 5. Applications Django et responsabilités

- `utilisateurs` : gestion des comptes, profils, rôle utilisateur, vérification d'e-mail, réinitialisation de mot de passe, signalements.
- `biens` : création, lecture, mise à jour, suppression des biens immobiliers et filtres de recherche.
- `images` : gestion des images liées aux biens.
- `reservations` : gestion des réservations, calendrier, statuts.
- `chat` : gestion des messages et des conversations.
- `avis` : enregistrement et consultation des avis sur les biens.
- `favoris` : gestion des biens favoris des utilisateurs.
- `notifications` : gestion des notifications utilisateur.
- `agences` : gestion des agences immobilières.
- `tarifs` : consultation des tarifs et gestion des abonnements.
- `ia` : recherche intelligente, recommandations et vérification de documents.
- `config` : configuration globale du projet, URL, paramètres Django.

## 6. Authentification et sécurité

### Authentification

- Inscription avec création de compte.
- Connexion avec génération de token JWT.
- Refresh token pour prolonger la session.
- Vérification d'e-mail obligatoire avant accès complet.
- Déconnexion et invalidation des tokens.

### Sécurité

- Mots de passe hachés par Django.
- Permissions et restrictions d'accès aux API.
- Protection contre les injections SQL grâce à l'ORM.
- Configuration prévue pour `DEBUG=False` en production.
- Gestion des secrets via variables d'environnement.
- Recommandation : configurer `ALLOWED_HOSTS`, HTTPS, et une base PostgreSQL.

## 7. Fonctionnalités principales

### 7.1 Utilisateurs

- Création et connexion de comptes.
- Mise à jour du profil utilisateur.
- Profils détaillés pour propriétaires, agences et utilisateurs standard.
- Vérification des profils propriétaires et agences.
- Gestion des signalements.
- Suppression de compte.

### 7.2 Biens immobiliers

- CRUD complet de biens.
- Filtres par prix, ville, type, statut, nombre de chambres.
- Consultation des biens d'un propriétaire.
- Calendrier simplifié de disponibilités.

### 7.3 Réservations

- Création et modification des réservations.
- Consultation des réservations personnelles.
- Consultation des réservations reçues pour les biens d'un propriétaire.
- Calendrier de réservation par bien.
- Mise à jour du statut d'une réservation.

### 7.4 Messages et conversations

- Envoi et réception de messages.
- Liste des conversations.
- Marquer un message comme lu.
- Consultation des messages d'une conversation.

### 7.5 Avis

- Publication d'avis et de notes.
- Consultation des avis d'un bien.
- Consultation des avis de l'utilisateur connecté.
- Statistiques d'avis pour un bien.

### 7.6 Favoris

- Ajout et suppression de favoris.
- Consultation de la liste de favoris.
- Compteur de favoris.
- Activation/désactivation d'un favori.

### 7.7 Images

- Upload des images liées aux biens.
- Consultation des images.
- Upload multiple d'images pour un bien.

### 7.8 Notifications

- Création et consultation des notifications.
- Notification non lue/lue.
- Marquer toutes les notifications comme lues.
- Calcul du nombre de notifications non lues.

### 7.9 Agences

- CRUD complet sur les agences.
- Consultation des informations d'une agence.

### 7.10 Tarifs et abonnements

- Consultation des tarifs actifs.
- Gestion des abonnements de l'utilisateur.
- Souscription à un plan tarifaire.

### 7.11 IA

- Recommandations de biens.
- Recherche intelligente par texte.
- Vérification automatisée de documents.

## 8. Endpoints API par domaine

### 8.1 Authentification

- `POST /api/auth/register/` : inscription utilisateur.
- `POST /api/auth/login/` : connexion.
- `POST /api/auth/logout/` : déconnexion.
- `POST /api/auth/refresh/` : renouvellement du token.
- `POST /api/auth/verify-email/` : vérification de l'adresse e-mail.
- `POST /api/auth/resend-verification/` : renvoi du lien de vérification.

### 8.2 Utilisateurs

- `GET /api/utilisateurs/me/` : profil utilisateur connecté.
- `PUT /api/utilisateurs/me/update/` : mise à jour du profil.
- `GET /api/utilisateurs/profile/` : profil détaillé.
- `GET /api/utilisateurs/profil-proprietaire/` : profil propriétaire.
- `POST /api/utilisateurs/profil-proprietaire/verifier/` : vérification propriétaire.
- `GET /api/utilisateurs/profil-agence/` : profil agence.
- `POST /api/utilisateurs/profil-agence/verifier/` : vérification agence.
- `POST /api/utilisateurs/password-reset/` : demande réinitialisation mot de passe.
- `GET/POST /api/utilisateurs/signalements/` : gestion des signalements.
- `GET/PUT/DELETE /api/utilisateurs/signalements/{id}/` : signalement spécifique.
- `DELETE /api/utilisateurs/delete/` : suppression de compte.

### 8.3 Agents

- `GET /api/agents/` : liste des agents.
- `GET /api/agents/{id}/` : détail d'un agent.
- `GET /api/agents/{id}/biens/` : biens d'un agent.
- `GET /api/agents/{id}/avis/` : avis d'un agent.
- `POST /api/agents/{id}/avis/` : ajouter un avis pour un agent.

### 8.4 Biens

- `GET /api/biens/` : liste des biens.
- `POST /api/biens/` : création d'un bien.
- `GET /api/biens/{id}/` : détail d'un bien.
- `PUT/PATCH /api/biens/{id}/` : mise à jour d'un bien.
- `DELETE /api/biens/{id}/` : suppression d'un bien.
- `GET /api/biens/mes_biens/` : biens du propriétaire connecté.
- `GET /api/biens/{id}/disponibilites/` : calendrier de disponibilités.

### 8.5 Documents

- `GET /api/documents/` : liste des documents.
- `POST /api/documents/` : création d'un document.
- `GET /api/documents/{id}/` : détail d'un document.
- `PUT/PATCH /api/documents/{id}/` : mise à jour d'un document.
- `DELETE /api/documents/{id}/` : suppression d'un document.
- `GET /api/documents/mes_documents/` : documents de l'utilisateur connecté.

### 8.6 Réservations

- `GET /api/reservations/` : liste des réservations.
- `POST /api/reservations/` : création d'une réservation.
- `GET /api/reservations/{id}/` : détail d'une réservation.
- `PUT/PATCH /api/reservations/{id}/` : mise à jour d'une réservation.
- `DELETE /api/reservations/{id}/` : suppression d'une réservation.
- `GET /api/reservations/mes_reservations/` : réservations de l'utilisateur connecté.
- `GET /api/reservations/reservations_pour_mes_biens/` : réservations reçues pour les biens du propriétaire.
- `GET /api/reservations/calendrier/` : calendrier des réservations d'un bien.
- `PUT /api/reservations/{id}/status/` : mise à jour du statut.

### 8.7 Messages

- `GET /api/messages/` : liste des messages.
- `POST /api/messages/` : envoi d'un message.
- `GET /api/messages/{id}/` : détail d'un message.
- `PUT/PATCH /api/messages/{id}/` : modification d'un message.
- `DELETE /api/messages/{id}/` : suppression d'un message.
- `GET /api/messages/mes_messages/` : messages de l'utilisateur connecté.
- `GET /api/messages/conversations/` : liste des conversations.
- `POST /api/messages/{id}/read/` : marquer un message comme lu.
- `GET /api/messages/conversation/{conversation_id}/` : messages d'une conversation.

### 8.8 Avis

- `GET /api/avis/` : liste des avis.
- `POST /api/avis/` : création d'un avis.
- `GET /api/avis/{id}/` : détail d'un avis.
- `PUT/PATCH /api/avis/{id}/` : modification d'un avis.
- `DELETE /api/avis/{id}/` : suppression d'un avis.
- `GET /api/avis/mes_avis/` : avis de l'utilisateur connecté.
- `GET /api/avis/statistiques/` : statistiques des avis pour un bien.

### 8.9 Favoris

- `GET /api/favoris/` : liste des favoris.
- `POST /api/favoris/` : création d'un favori.
- `GET /api/favoris/{id}/` : détail d'un favori.
- `PUT/PATCH /api/favoris/{id}/` : modification d'un favori.
- `DELETE /api/favoris/{id}/` : suppression d'un favori.
- `GET /api/favoris/count/` : nombre total de favoris.
- `POST /api/favoris/{id}/toggle/` : activer/désactiver un favori.

### 8.10 Images

- `GET /api/images/` : liste des images.
- `POST /api/images/` : création d'une image.
- `GET /api/images/{id}/` : détail d'une image.
- `PUT/PATCH /api/images/{id}/` : modification d'une image.
- `DELETE /api/images/{id}/` : suppression d'une image.
- `GET /api/images/mes_images/` : images des biens du propriétaire.
- `POST /api/images/upload_multiple/` : upload multiple d'images.

### 8.11 Notifications

- `GET /api/notifications/` : liste des notifications.
- `POST /api/notifications/` : création d'une notification.
- `GET /api/notifications/{id}/` : détail d'une notification.
- `PUT/PATCH /api/notifications/{id}/` : modification d'une notification.
- `DELETE /api/notifications/{id}/` : suppression d'une notification.
- `POST /api/notifications/mark_all_as_read/` : marquer toutes les notifications comme lues.
- `GET /api/notifications/unread_count/` : obtenir le nombre de notifications non lues.
- `PUT /api/notifications/{id}/read/` : marquer une notification comme lue.

### 8.12 Agences

- `GET /api/agences/` : liste des agences.
- `POST /api/agences/` : création d'une agence.
- `GET /api/agences/{id}/` : détail d'une agence.
- `PUT/PATCH /api/agences/{id}/` : modification d'une agence.
- `DELETE /api/agences/{id}/` : suppression d'une agence.

### 8.13 Tarifs et abonnements

- `GET /api/tarifs/` : liste des tarifs actifs.
- `GET /api/tarifs/{id}/` : détail d'un tarif.
- `GET /api/abonnements/` : abonnements de l'utilisateur connecté.
- `POST /api/abonnements/` : création d'un abonnement.
- `GET /api/abonnements/{id}/` : détail d'un abonnement.
- `PUT/PATCH /api/abonnements/{id}/` : modification d'un abonnement.
- `DELETE /api/abonnements/{id}/` : suppression d'un abonnement.
- `POST /api/abonnements/souscrire/` : souscription à un plan tarifaire.

### 8.14 IA

- `GET /api/ia/recommendations/` : liste des recommandations.
- `POST /api/ia/recommendations/` : création d'une recommandation.
- `GET /api/ia/recommendations/{id}/` : détail d'une recommandation.
- `PUT/PATCH /api/ia/recommendations/{id}/` : modification d'une recommandation.
- `DELETE /api/ia/recommendations/{id}/` : suppression d'une recommandation.
- `POST /api/ia/recommendations/generer_recommandations/` : générer des recommandations IA.
- `POST /api/ia/recherche/rechercher/` : recherche intelligente par texte.
- `POST /api/ia/verifier-document/verifier/` : vérification d'un document par IA.

### 8.15 Endpoints utilitaires

- `GET /api/search/` : recherche globale.
- `GET /api/stats/` : statistiques pour le tableau de bord.
- `GET /api/villes/` : liste des villes disponibles.
- `GET /api/types-bien/` : liste des types de biens.

## 9. Paramètres et filtres importants

### Biens

- `prix_min`
- `prix_max`
- `ville`
- `type`
- `statut`
- `nombre_chambres`

### Réservations

- `status`
- `bien_id`
- `mois`
- `annee`

### Messages

- `conversation_id`
- `sender`
- `receiver`

### Avis

- `bien_id`
- `note_min`

### Favoris

- `ville`
- `type_bien`
- `prix_min`
- `prix_max`

## 10. Installation et démarrage

### Pré-requis

- Python 3.12+
- Pip
- Virtualenv ou venv
- Redis si Celery est utilisé

### Installation rapide

```powershell
cd "C:\Users\NACRO ADJARATOU\PROJET SOUTENANCE L3\APPLICATION WEB\API_DJANGO_WEB"
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### Accès utiles

- API root : `http://127.0.0.1:8000/api/`
- Swagger : `http://127.0.0.1:8000/swagger/`
- Redoc : `http://127.0.0.1:8000/redoc/`
- Admin Django : `http://127.0.0.1:8000/admin/`

## 11. Tests

- Exécuter la suite de tests Django :

```powershell
python manage.py test
```

- Le projet inclut des tests unitaires et des tests d'intégration pour les applications principales.

## 12. Déploiement recommandé

### En production

- `DEBUG=False`
- configurer `ALLOWED_HOSTS`
- utiliser PostgreSQL ou MySQL
- activer HTTPS
- stocker les secrets dans des variables d'environnement
- configurer Redis/Celery pour les tâches asynchrones
- utiliser un serveur WSGI comme Gunicorn ou Daphne

### Bonnes pratiques

- sauvegarder la base régulièrement
- surveiller les logs
- limiter les permissions des comptes de base de données
- vérifier les quotas et les ressources mémoire

## 13. Évolutions possibles

- ajout d'un système de paiement en ligne pour la réservation
- intégration de WebSockets pour le chat en temps réel
- gestion multi-langues
- déploiement Dockerisé
- optimisation des requêtes et pagination
- génération de rapports statistiques avancés

## 14. Résumé

LogCiv est conçue comme une API modulaire et évolutive pour une application immobilière moderne. Elle couvre l'ensemble du cycle utilisateur : inscription, gestion des biens, réservation, communication, avis, notifications, abonnements et IA.

> Pour des détails techniques supplémentaires, consultez aussi : `API_DOCUMENTATION.md`, `README_COMPLETE.md`, `CONFIG_GUIDE.md` et `SECURITY_NOTES.md`.
