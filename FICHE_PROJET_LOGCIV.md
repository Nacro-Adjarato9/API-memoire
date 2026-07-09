# Fiche projet LogCiv

## 1. Nom du projet
**LogCiv**  
API web immobilière construite avec Django.

## 2. Idée générale
LogCiv est un backend REST qui sert à gérer une plateforme immobilière.  
Le projet centralise:
- les comptes utilisateurs
- les biens immobiliers
- les réservations
- les images et documents
- les avis et favoris
- la messagerie
- les notifications
- les agences
- les tarifs et abonnements
- les fonctions d’intelligence artificielle

## 3. Comment le projet est construit
Le projet suit l’architecture classique Django REST:
- `models.py` définit les données
- `serializers.py` transforme les objets en JSON et valide les entrées
- `views.py` contient la logique API
- `urls.py` expose les routes
- `admin.py` permet l’administration
- `tests.py` contient les tests

En pratique, il y a 3 façons principales de construire les API:
- `ModelViewSet` pour les CRUD standards
- `ReadOnlyModelViewSet` pour les données seulement en lecture
- `APIView` ou `generics` pour les actions personnalisées

## 4. Technologies utilisées
- **Backend**: Django
- **API REST**: Django REST Framework
- **Authentification**: JWT via SimpleJWT
- **Documentation**: Swagger et Redoc
- **Base de données**: SQLite en local
- **Cache / tâches**: configuration prévue pour Redis et Celery
- **Frontend autorisé**: React local via CORS

## 5. Les apps du projet
Le dépôt contient les modules suivants:
- `utilisateurs`
- `biens`
- `reservations`
- `images`
- `chat`
- `avis`
- `favoris`
- `notifications`
- `agences`
- `tarifs`
- `ia`

## 6. Comment chaque API est faite

### 6.1 API utilisateurs
Cette partie est construite avec plusieurs vues:
- `RegisterView` pour l’inscription
- `LoginView` pour la connexion
- `LogoutView` pour la déconnexion
- `VerifyEmailView` et `ResendVerificationView` pour la vérification email
- `ChangePasswordView` et `PasswordResetView` pour le mot de passe
- `MeView` et `MeUpdateView` pour le profil connecté
- `UtilisateurViewSet`, `ProfilViewSet`, `VisiteViewSet`, `PaiementViewSet`, `TransactionViewSet`, `VilleViewSet`, `QuartierViewSet`, `TicketViewSet`, `SignalementViewSet`, `HistoriqueRechercheViewSet` pour les objets métier

La logique est faite avec:
- des serializers pour valider les données
- des tokens JWT pour l’authentification
- des vues génériques pour les profils
- des ViewSets pour les ressources CRUD

### 6.2 API biens
L’API des biens repose sur:
- `BienViewSet` pour le CRUD des biens
- `DocumentViewSet` pour les documents liés aux biens

Le fonctionnement est le suivant:
- `ModelViewSet` gère automatiquement liste, création, détail, mise à jour et suppression
- le serializer change selon l’action: lecture ou création
- des filtres sont appliqués via les paramètres GET comme `prix_min`, `prix_max`, `ville`, `type`, `statut`, `nombre_chambres`
- l’utilisateur peut avoir des actions personnalisées comme `mes_biens` et `disponibilites`
- les documents acceptent aussi des fichiers liés à un bien, à un propriétaire ou à une agence

### 6.3 API réservations
Cette API est composée de:
- `ReservationViewSet` pour les opérations CRUD
- `ReservationStatusUpdateView` pour changer le statut d’une réservation

Le principe:
- le ViewSet gère les réservations normales
- une vue APIView séparée gère la mise à jour d’état, ce qui est utile pour traiter une action spécifique sans mélanger toute la logique CRUD

### 6.4 API chat
L’API chat est construite autour de:
- `MessageViewSet` pour gérer les messages
- `MessageConversationView` pour récupérer une conversation

Le choix technique est simple:
- le ViewSet sert au CRUD des messages
- la vue de conversation est dédiée à la lecture d’un fil de discussion précis

### 6.5 API avis
Cette API utilise:
- `AvisViewSet`

Elle est surtout basée sur un `ModelViewSet`, donc elle fournit:
- liste
- création
- modification
- suppression

### 6.6 API favoris
Cette API repose sur:
- `FavoriViewSet`

Elle suit la même logique que les autres CRUD:
- un ViewSet pour gérer les favoris
- les routes sont automatiquement générées par le routeur

### 6.7 API images
Cette API est construite avec:
- `ImageViewSet`

Elle sert à:
- ajouter des images à un bien
- lister les images
- supprimer une image

### 6.8 API notifications
Cette API contient:
- `NotificationViewSet`
- `NotificationMarkAsReadView`

La structure est volontairement séparée:
- le ViewSet gère la lecture et la gestion des notifications
- la vue `mark as read` sert à une action métier précise

### 6.9 API agences
Cette API utilise:
- `AgenceViewSet`

Elle est totalement basée sur le CRUD classique, avec le routeur DRF.

### 6.10 API tarifs et abonnements
Cette partie contient:
- `TarifViewSet` en lecture seule
- `AbonnementViewSet` en CRUD complet

Le choix est logique:
- les tarifs sont exposés en consultation
- les abonnements peuvent être créés ou gérés par l’application

### 6.11 API IA
L’API IA est la partie la plus personnalisée du projet.  
Elle combine plusieurs vues et un fichier de services.

Vues présentes:
- `RecommendationAPIView`
- `RechercheIAView`
- `IAChatView`
- `MapLogementsAPIView`
- `GeocoderAPIView`
- `BudgetAdvisoryView`
- `IAVerifyDocumentView`
- `RecommendationIAViewSet`

Comment elle fonctionne:
- `serializers.py` valide les demandes IA
- `services.py` contient la logique métier et les appels IA
- les vues récupèrent les données, appellent les services, puis renvoient une réponse JSON
- certaines réponses enregistrent aussi un historique en base via `RecommendationIA`

Les endpoints IA servent à:
- faire une recherche intelligente
- discuter avec l’assistant immobilier
- donner des conseils par budget
- géocoder une adresse
- afficher des biens sur carte
- vérifier un document

### 6.12 API utilitaire globale
Dans `config/views.py`, il y a plusieurs endpoints transversaux:
- `APIRootView`
- `SearchView`
- `StatsView`
- `DashboardView`
- `TypesBienView`
- `LocatairesView`
- `ActeursView`

Ces vues servent à:
- centraliser la navigation API
- rechercher dans plusieurs modules
- afficher des statistiques
- alimenter les tableaux de bord
- lister les types de biens
- séparer les utilisateurs par profil

## 7. Routes principales
Les routes exposées les plus importantes sont:
- `/api/auth/register/`
- `/api/auth/login/`
- `/api/auth/logout/`
- `/api/auth/refresh/`
- `/api/auth/verify-email/`
- `/api/biens/`
- `/api/documents/`
- `/api/reservations/`
- `/api/messages/`
- `/api/avis/`
- `/api/favoris/`
- `/api/images/`
- `/api/notifications/`
- `/api/agences/`
- `/api/tarifs/`
- `/api/abonnements/`
- `/api/ia/recommendation/`
- `/api/ia/chat/`
- `/api/ia/budget-advisory/`
- `/api/ia/verify-document/`

## 8. Documentation disponible
Le dépôt contient déjà plusieurs fichiers utiles:
- `README.md`
- `PROJECT_OVERVIEW.md`
- `PROJET_DETAILLE_A_Z.md`
- `API_DOCUMENTATION.md`
- `CONFIG_GUIDE.md`
- `SECURITY_NOTES.md`
- `IA_DOCUMENTATION.md`
- `IA_README.md`
- `INSTALLATION_IA.md`
- `CAS_D_USAGE_IA.md`
- `SETUP_COMPLET_IA.md`

## 9. État actuel du projet
### Ce qui est déjà en place
- les principales apps Django existent
- les routes API sont déjà branchées
- la partie authentification est présente
- les modules métier principaux sont codés
- la documentation est riche
- la base SQLite locale existe déjà
- le module IA est intégré avec plusieurs endpoints

### Ce qui montre que le projet est encore en travail
- le dépôt contient beaucoup de fichiers modifiés localement
- plusieurs nouveaux fichiers de documentation ne sont pas encore commités
- cela ressemble à un état de développement avancé, pas à une version finale gelée

### Lecture réaliste de l’état
Le projet paraît **fonctionnel et très avancé**, mais l’état du dépôt montre qu’il reste une phase de validation avant livraison propre.

## 10. Conclusion courte
LogCiv est une API immobilière Django structurée en plusieurs apps spécialisées.  
Chaque API est construite avec des serializers, des ViewSets ou des vues API dédiées selon le besoin.  
Le projet est déjà solide, mais le dépôt actuel reste en **état de développement actif** avec des modifications locales à vérifier.
