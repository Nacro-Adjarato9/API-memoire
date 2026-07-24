# LogCiv — Plateforme immobilière (Côte d'Ivoire)
### Document de synthèse pour la soutenance

---

## 1. Présentation générale

**LogCiv** est une plateforme immobilière complète pour la Côte d'Ivoire, permettant de publier, rechercher, réserver et gérer des biens immobiliers (location et vente). Le projet est composé de **trois applications distinctes** partageant une seule API backend :

| Application | Rôle | Technologie |
|---|---|---|
| **API backend** | Cœur métier, base de données, logique IA | Django REST Framework |
| **Application Web** | Site web + tableau de bord propriétaire/agence | React + Vite |
| **Application Mobile** | App pour les locataires (recherche, réservation, chat) | React Native + Expo |

---

## 2. Architecture technique

```
┌─────────────────┐     ┌─────────────────┐
│   Site Web       │     │   App Mobile     │
│  (React/Vite)    │     │ (Expo/React      │
│                   │     │  Native)         │
└────────┬─────────┘     └────────┬─────────┘
         │                          │
         │      HTTPS / REST API    │
         └──────────┬───────────────┘
                     │
           ┌─────────▼──────────┐
           │   API Django REST   │
           │  (api-memoire-o2mk  │
           │   .onrender.com)    │
           └─────────┬──────────┘
                     │
           ┌─────────▼──────────┐
           │  Base de données     │
           │  PostgreSQL          │
           │  (Render)            │
           └───────────────────────┘
```

### 2.1 Backend — API Django REST Framework

- **Langage / Framework** : Python, Django 6 + Django REST Framework
- **Base de données** : PostgreSQL (hébergée sur Render, persistante)
- **Authentification** : JWT (JSON Web Tokens) via `djangorestframework-simplejwt`
- **Documentation API** : Swagger / drf-yasg (documentation interactive auto-générée)
- **Serveur de fichiers statiques** : WhiteNoise
- **Serveur d'application** : Gunicorn

**Modules principaux (apps Django)** :
- `utilisateurs` — comptes, rôles (locataire, propriétaire, agent, agence), profils, authentification
- `biens` — annonces immobilières, documents justificatifs
- `reservations` — demandes de visite et réservations
- `chat` — messagerie interne entre utilisateurs
- `avis` — système de notation et commentaires
- `favoris` — biens sauvegardés par les utilisateurs
- `notifications` — notifications en temps réel (réservation, message, document...)
- `images` — gestion des photos de biens
- `agences` — gestion des agences immobilières
- `tarifs` — plans d'abonnement (Gratuit / Premium)
- `kyc` — vérification d'identité automatique (Didit)
- `ia` — modules intelligence artificielle (voir section 4)

### 2.2 Frontend Web

- **Framework** : React 18 + TypeScript
- **Build tool** : Vite
- **Style** : Tailwind CSS
- **Gestion des requêtes serveur** : TanStack React Query
- **Routing** : Wouter
- **Fonctions principales** : vitrine publique, inscription/connexion, tableau de bord propriétaire/agence (gestion des biens, réservations, messages, statistiques)

### 2.3 Application Mobile

- **Framework** : React Native + Expo (SDK 54)
- **Routing** : Expo Router (navigation par fichiers)
- **Cible** : Android (package `com.affisate.logciv`) et iOS
- **Fonctions principales** : recherche de biens, carte interactive, favoris, réservation de visite, messagerie, notifications, chat IA

**Écrans clés de l'app mobile** :
- Authentification : connexion, inscription, vérification email, mot de passe oublié
- Accueil : liste des biens, filtres par catégorie
- Recherche avancée avec carte
- Fiche détaillée d'un bien
- Réservation de visite
- Favoris
- Messagerie / conversations
- Notifications
- Profil utilisateur

---

## 3. Fonctionnalités clés

### Pour les locataires
- Recherche de biens avec filtres (ville, quartier, type, budget, nombre de chambres...)
- Recherche intelligente avec repli en cascade (élargit automatiquement le budget/zone si peu de résultats)
- Visualisation sur carte interactive (OpenStreetMap / Google Maps)
- Réservation de visite en ligne
- Messagerie directe avec le propriétaire/agence
- Favoris
- Avis et notation des biens
- Assistant conversationnel IA ("LOGI") pour la recherche de logement
- Signalement d'annonces suspectes

### Pour les propriétaires / agences
- Publication d'annonces avec photos, équipements, localisation GPS
- Tableau de bord : suivi des biens publiés, réservations, statistiques
- Gestion des statuts (disponible / réservé / loué / vendu) — **automatisée** selon la date de disponibilité renseignée
- Vérification d'identité (KYC manuel + automatique via Didit)
- Système d'abonnement (plans Gratuit / Premium) avec paiement Mobile Money (CinetPay)
- Support client intégré (tickets)

### Modules Intelligence Artificielle
1. **Détection de fraude/anomalie de prix** — score de suspicion calculé automatiquement à la publication (prix hors norme, mots-clés suspects, fréquence de publication anormale)
2. **Recherche intelligente avec repli progressif** — élargit automatiquement les critères si aucun résultat exact
3. **Recommandations personnalisées** — basées sur l'historique de recherche et les favoris
4. **Suggestion de zones voisines** — propose des quartiers alternatifs pertinents
5. **Analyse des tendances de prix** — moyenne/min/max par ville et type de bien
6. **Chat conversationnel** — assistant IA qui répond en langage naturel (Français/Anglais/Dioula)
7. **Vérification de documents par IA** — analyse automatique des pièces justificatives
8. **Notifications intelligentes** — alerte sur nouveaux biens correspondant aux recherches sauvegardées et baisses de prix

### Sécurité et fiabilité
- Authentification JWT avec durée de vie étendue (12 jours) pour éviter les déconnexions intempestives
- Vérification d'email obligatoire à l'inscription (code à 6 chiffres)
- Vérification d'identité KYC (manuelle + automatique via Didit)
- Détection automatique d'annonces suspectes (anti-fraude)

---

## 4. Déploiement — Infrastructure en production

Le projet est **entièrement déployé en ligne**, accessible depuis n'importe quel réseau (contrairement à un simple serveur local) :

| Composant | Plateforme | Détail |
|---|---|---|
| **API Backend** | Render (Web Service) | `https://api-memoire-o2mk.onrender.com` |
| **Base de données** | Render (PostgreSQL) | Base persistante, gérée séparément du serveur applicatif |
| **Code source** | GitHub | Déploiement automatique à chaque envoi de code (CI/CD basique) |
| **Application mobile** | Expo Application Services (EAS) | Build APK Android via `eas build`, connexion via `eas login` |
| **Serveur de fichiers médias** | Django (servis directement par l'API) | Photos de biens, documents |

### Points techniques du déploiement à retenir pour la soutenance
- **Environnement de production isolé** : variables d'environnement (clés secrètes, connexion base de données) gérées séparément du code source, jamais versionnées.
- **Build automatisé** : chaque `git push` déclenche automatiquement un nouveau déploiement sur Render (migrations de base de données + collecte des fichiers statiques + démarrage du serveur).
- **Application mobile packagée en APK** : build natif Android généré via **EAS Build** (Expo Application Services), permettant une installation directe sur smartphone sans passer par le Play Store — pratique pour une démonstration.
- **Résilience** : le backend gère les pics de charge gratuitement via le plan gratuit de Render (avec mise en veille après inactivité, réveil automatique à la première requête).

---

## 5. Chiffres clés du projet (base de données actuelle)

- **13 modules applicatifs** (apps Django) couvrant l'ensemble du cycle immobilier
- **~35 biens** enregistrés en base de démonstration
- **~26 comptes utilisateurs** (locataires, propriétaires, agences)
- **8 modules d'intelligence artificielle** intégrés nativement à la plateforme
- **3 applications synchronisées** (API + Web + Mobile) sur une seule source de vérité (la base de données)

---

## 6. Points forts à mettre en avant en soutenance

1. **Architecture multi-plateforme réelle** : une seule API sert un site web complet et une application mobile native, démontrant une architecture professionnelle découplée (API-first).
2. **Intelligence artificielle appliquée concrètement** : pas de gadget — détection de fraude, recherche intelligente et assistant conversationnel apportent une vraie valeur ajoutée métier.
3. **Automatisations métier** : le statut de disponibilité d'un bien se met à jour automatiquement en fonction de la date renseignée, sans intervention manuelle.
4. **Déploiement professionnel réel** : le projet n'est pas qu'un prototype local, il est hébergé en ligne, accessible publiquement, avec une vraie base de données persistante et une application mobile packagée en APK installable.
5. **Sécurité pensée dès la conception** : authentification JWT, vérification d'identité, détection d'anomalies de prix, modération des annonces.

---

*Document généré pour préparer la présentation PowerPoint de soutenance — à adapter/résumer selon le temps de présentation imparti.*
