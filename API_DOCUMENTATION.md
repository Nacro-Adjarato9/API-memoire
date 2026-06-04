# API Django REST Framework - Documentation Detaillee

Cette documentation resume les endpoints exposes par le projet `API_DJANGO_WEB`.

Base URL conseillee:

```http
http://127.0.0.1:8000/api/
```

Docs automatiques:

```http
/swagger/
/redoc/
```

## 1. Authentification

Les endpoints ci-dessous servent a creer un compte, se connecter et gerer le token JWT.

| Methode | Endpoint | Description |
| --- | --- | --- |
| POST | `/api/auth/register/` | Creer un compte utilisateur |
| POST | `/api/auth/login/` | Authentifier un utilisateur et retourner les tokens JWT |
| POST | `/api/auth/logout/` | Deconnecter l utilisateur |
| POST | `/api/auth/refresh/` | Renouveler le token access |
| POST | `/api/auth/verify-email/` | Verifier l adresse email |
| POST | `/api/auth/resend-verification/` | Renvoyer le lien de verification |

Exemple de login:

```json
{
  "username": "john_doe",
  "password": "MotDePasseSecurise123"
}
```

## 2. Utilisateurs

| Methode | Endpoint | Description |
| --- | --- | --- |
| GET | `/api/utilisateurs/me/` | Recuperer le profil de l utilisateur connecte |
| PUT | `/api/utilisateurs/me/update/` | Mettre a jour le profil de l utilisateur connecte |
| GET | `/api/utilisateurs/profile/` | Recuperer le profil detaille |
| GET | `/api/utilisateurs/profil-proprietaire/` | Recuperer le profil proprietaire |
| POST | `/api/utilisateurs/profil-proprietaire/verifier/` | Verifier un profil proprietaire |
| GET | `/api/utilisateurs/profil-agence/` | Recuperer le profil agence |
| POST | `/api/utilisateurs/profil-agence/verifier/` | Verifier un profil agence |
| POST | `/api/utilisateurs/password-reset/` | Demander une reinitialisation de mot de passe |
| GET | `/api/utilisateurs/signalements/` | Lister les signalements |
| POST | `/api/utilisateurs/signalements/` | Creer un signalement |
| GET | `/api/utilisateurs/signalements/{id}/` | Voir un signalement |
| PUT | `/api/utilisateurs/signalements/{id}/` | Modifier un signalement |
| DELETE | `/api/utilisateurs/signalements/{id}/` | Supprimer un signalement |
| DELETE | `/api/utilisateurs/delete/` | Supprimer le compte connecte |

### Agents

| Methode | Endpoint | Description |
| --- | --- | --- |
| GET | `/api/agents/` | Lister les agents |
| GET | `/api/agents/{id}/` | Voir un agent |
| GET | `/api/agents/{id}/biens/` | Lister les biens d un agent |
| GET | `/api/agents/{id}/avis/` | Lister les avis d un agent |
| POST | `/api/agents/{id}/avis/` | Ajouter un avis pour un agent |

Note: le chemin `/api/agents/{id}/avis/` est defini deux fois dans `utilisateurs/urls.py`.
Si tu relies ce endpoint au frontend, verifie le comportement effectif au moment de l integration.

## 3. Biens

### Routes standards

| Methode | Endpoint | Description |
| --- | --- | --- |
| GET | `/api/biens/` | Lister les biens |
| POST | `/api/biens/` | Creer un bien |
| GET | `/api/biens/{id}/` | Voir un bien |
| PUT | `/api/biens/{id}/` | Modifier un bien |
| PATCH | `/api/biens/{id}/` | Modifier partiellement un bien |
| DELETE | `/api/biens/{id}/` | Supprimer un bien |

### Filtres disponibles

| Parametre | Exemple | Description |
| --- | --- | --- |
| `prix_min` | `?prix_min=100000` | Prix minimum en FCFA |
| `prix_max` | `?prix_max=500000` | Prix maximum en FCFA |
| `ville` | `?ville=Abidjan` | Filtrer par ville |
| `type` | `?type=maison` | Filtrer par type de bien |
| `statut` | `?statut=disponible` | Filtrer par statut |
| `nombre_chambres` | `?nombre_chambres=3` | Filtrer par nombre minimum de chambres |

### Actions custom

| Methode | Endpoint | Description |
| --- | --- | --- |
| GET | `/api/biens/mes_biens/` | Biens du proprietaire connecte |
| GET | `/api/biens/{id}/disponibilites/` | Calendrier simplifie des disponibilites |

## 4. Documents

| Methode | Endpoint | Description |
| --- | --- | --- |
| GET | `/api/documents/` | Lister les documents |
| POST | `/api/documents/` | Creer un document |
| GET | `/api/documents/{id}/` | Voir un document |
| PUT | `/api/documents/{id}/` | Modifier un document |
| PATCH | `/api/documents/{id}/` | Modifier partiellement un document |
| DELETE | `/api/documents/{id}/` | Supprimer un document |
| GET | `/api/documents/mes_documents/` | Documents de l utilisateur connecte |

## 5. Reservations

| Methode | Endpoint | Description |
| --- | --- | --- |
| GET | `/api/reservations/` | Lister les reservations |
| POST | `/api/reservations/` | Creer une reservation |
| GET | `/api/reservations/{id}/` | Voir une reservation |
| PUT | `/api/reservations/{id}/` | Modifier une reservation |
| PATCH | `/api/reservations/{id}/` | Modifier partiellement une reservation |
| DELETE | `/api/reservations/{id}/` | Supprimer une reservation |

### Actions custom

| Methode | Endpoint | Description |
| --- | --- | --- |
| GET | `/api/reservations/mes_reservations/` | Reservations de l utilisateur connecte |
| GET | `/api/reservations/reservations_pour_mes_biens/` | Reservations recues pour les biens du proprietaire |
| GET | `/api/reservations/calendrier/` | Calendrier des reservations d un bien |
| PUT | `/api/reservations/{id}/status/` | Mettre a jour le statut d une reservation |

### Parametres utiles

| Endpoint | Parametres |
| --- | --- |
| `/api/reservations/` | `status`, `bien_id` |
| `/api/reservations/calendrier/` | `bien_id`, `mois`, `annee` |

Exemple pour le calendrier:

```http
GET /api/reservations/calendrier/?bien_id=1&mois=4&annee=2026
```

## 6. Messages

| Methode | Endpoint | Description |
| --- | --- | --- |
| GET | `/api/messages/` | Lister les messages |
| POST | `/api/messages/` | Envoyer un message |
| GET | `/api/messages/{id}/` | Voir un message |
| PUT | `/api/messages/{id}/` | Modifier un message |
| PATCH | `/api/messages/{id}/` | Modifier partiellement un message |
| DELETE | `/api/messages/{id}/` | Supprimer un message |

### Actions custom

| Methode | Endpoint | Description |
| --- | --- | --- |
| GET | `/api/messages/mes_messages/` | Messages de l utilisateur connecte |
| GET | `/api/messages/conversations/` | Liste des conversations |
| POST | `/api/messages/{id}/read/` | Marquer un message comme lu |
| GET | `/api/messages/conversation/{conversation_id}/` | Messages d une conversation |

### Parametres utiles

| Endpoint | Parametres |
| --- | --- |
| `/api/messages/` | `conversation_id`, `sender`, `receiver` |

## 7. Avis

| Methode | Endpoint | Description |
| --- | --- | --- |
| GET | `/api/avis/` | Lister les avis |
| POST | `/api/avis/` | Creer un avis |
| GET | `/api/avis/{id}/` | Voir un avis |
| PUT | `/api/avis/{id}/` | Modifier un avis |
| PATCH | `/api/avis/{id}/` | Modifier partiellement un avis |
| DELETE | `/api/avis/{id}/` | Supprimer un avis |

### Actions custom

| Methode | Endpoint | Description |
| --- | --- | --- |
| GET | `/api/avis/mes_avis/` | Avis de l utilisateur connecte |
| GET | `/api/avis/statistiques/` | Statistiques des avis pour un bien |

### Parametres utiles

| Endpoint | Parametres |
| --- | --- |
| `/api/avis/` | `bien_id`, `note_min` |
| `/api/avis/statistiques/` | `bien_id` requis |

## 8. Favoris

| Methode | Endpoint | Description |
| --- | --- | --- |
| GET | `/api/favoris/` | Lister les favoris de l utilisateur |
| POST | `/api/favoris/` | Ajouter un favori |
| GET | `/api/favoris/{id}/` | Voir un favori |
| PUT | `/api/favoris/{id}/` | Modifier un favori |
| PATCH | `/api/favoris/{id}/` | Modifier partiellement un favori |
| DELETE | `/api/favoris/{id}/` | Supprimer un favori |

### Actions custom

| Methode | Endpoint | Description |
| --- | --- | --- |
| GET | `/api/favoris/count/` | Nombre total de favoris |
| POST | `/api/favoris/{id}/toggle/` | Ajouter ou retirer un favori |

### Parametres utiles

| Endpoint | Parametres |
| --- | --- |
| `/api/favoris/` | `ville`, `type_bien`, `prix_min`, `prix_max` |

## 9. Images

| Methode | Endpoint | Description |
| --- | --- | --- |
| GET | `/api/images/` | Lister les images |
| POST | `/api/images/` | Creer une image |
| GET | `/api/images/{id}/` | Voir une image |
| PUT | `/api/images/{id}/` | Modifier une image |
| PATCH | `/api/images/{id}/` | Modifier partiellement une image |
| DELETE | `/api/images/{id}/` | Supprimer une image |

### Actions custom

| Methode | Endpoint | Description |
| --- | --- | --- |
| GET | `/api/images/mes_images/` | Images des biens du proprietaire |
| POST | `/api/images/upload_multiple/` | Envoyer plusieurs images pour un bien |

### Corps attendu pour `upload_multiple`

```json
{
  "bien_id": 1,
  "urls": [
    "https://exemple.com/image1.jpg",
    "https://exemple.com/image2.jpg"
  ]
}
```

## 10. Notifications

| Methode | Endpoint | Description |
| --- | --- | --- |
| GET | `/api/notifications/` | Lister les notifications |
| POST | `/api/notifications/` | Creer une notification |
| GET | `/api/notifications/{id}/` | Voir une notification |
| PUT | `/api/notifications/{id}/` | Modifier une notification |
| PATCH | `/api/notifications/{id}/` | Modifier partiellement une notification |
| DELETE | `/api/notifications/{id}/` | Supprimer une notification |

### Actions custom

| Methode | Endpoint | Description |
| --- | --- | --- |
| POST | `/api/notifications/mark_all_as_read/` | Marquer toutes les notifications comme lues |
| GET | `/api/notifications/unread_count/` | Obtenir le nombre de notifications non lues |
| PUT | `/api/notifications/{id}/read/` | Marquer une notification comme lue |

## 11. Agences

| Methode | Endpoint | Description |
| --- | --- | --- |
| GET | `/api/agences/` | Lister les agences |
| POST | `/api/agences/` | Creer une agence |
| GET | `/api/agences/{id}/` | Voir une agence |
| PUT | `/api/agences/{id}/` | Modifier une agence |
| PATCH | `/api/agences/{id}/` | Modifier partiellement une agence |
| DELETE | `/api/agences/{id}/` | Supprimer une agence |

## 12. Tarifs et abonnements

### Tarifs

| Methode | Endpoint | Description |
| --- | --- | --- |
| GET | `/api/tarifs/` | Lister les tarifs actifs |
| GET | `/api/tarifs/{id}/` | Voir un tarif |

### Abonnements

| Methode | Endpoint | Description |
| --- | --- | --- |
| GET | `/api/abonnements/` | Lister les abonnements de l utilisateur connecte |
| POST | `/api/abonnements/` | Creer un abonnement |
| GET | `/api/abonnements/{id}/` | Voir un abonnement |
| PUT | `/api/abonnements/{id}/` | Modifier un abonnement |
| PATCH | `/api/abonnements/{id}/` | Modifier partiellement un abonnement |
| DELETE | `/api/abonnements/{id}/` | Supprimer un abonnement |
| POST | `/api/abonnements/souscrire/` | Souscrire a un plan tarifaire |

## 13. IA

### Recommendations

| Methode | Endpoint | Description |
| --- | --- | --- |
| GET | `/api/ia/recommendations/` | Lister les recommendations IA |
| POST | `/api/ia/recommendations/` | Creer une recommendation IA |
| GET | `/api/ia/recommendations/{id}/` | Voir une recommendation |
| PUT | `/api/ia/recommendations/{id}/` | Modifier une recommendation |
| PATCH | `/api/ia/recommendations/{id}/` | Modifier partiellement une recommendation |
| DELETE | `/api/ia/recommendations/{id}/` | Supprimer une recommendation |
| POST | `/api/ia/recommendations/generer_recommandations/` | Generer des recommandations IA |

### Recherche et verification

| Methode | Endpoint | Description |
| --- | --- | --- |
| POST | `/api/ia/recherche/rechercher/` | Recherche intelligente par texte |
| POST | `/api/ia/verifier-document/verifier/` | Verification d un document par IA |

## 14. Endpoints utilitaires

| Methode | Endpoint | Description |
| --- | --- | --- |
| GET | `/api/search/` | Recherche globale |
| GET | `/api/stats/` | Statistiques du dashboard |
| GET | `/api/villes/` | Liste des villes disponibles |
| GET | `/api/types-bien/` | Liste des types de biens |

### Recherche globale

```http
GET /api/search/?q=Abidjan&type=utilisateur
```

### Statistiques

`/api/stats/` retourne des statistiques differentes selon le role de l utilisateur connecte.

## 15. Conseils d utilisation

1. Pour les routes liees a un utilisateur, envoyer le token JWT dans le header:

```http
Authorization: Bearer <token_access>
```

2. Les routes `list`, `detail`, `create`, `update` et `delete` suivent le comportement standard de Django REST Framework.

3. Les actions custom sont ajoutees a cote des routes standard et permettent d aller plus vite pour le frontend.

4. La documentation Swagger et ReDoc permet de tester les endpoints directement.

## 16. Resume rapide

- Authentification: `/api/auth/...`
- Utilisateurs: `/api/utilisateurs/...`
- Biens: `/api/biens/...`
- Documents: `/api/documents/...`
- Reservations: `/api/reservations/...`
- Messages: `/api/messages/...`
- Avis: `/api/avis/...`
- Favoris: `/api/favoris/...`
- Images: `/api/images/...`
- Notifications: `/api/notifications/...`
- Agences: `/api/agences/...`
- Tarifs: `/api/tarifs/...` et `/api/abonnements/...`
- IA: `/api/ia/...`
- Utilitaires: `/api/search/`, `/api/stats/`, `/api/villes/`, `/api/types-bien/`
