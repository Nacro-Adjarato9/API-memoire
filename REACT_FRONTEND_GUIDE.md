# Guide React pour consommer l'API

Ce document explique a React comment consommer l'API Django du projet, avec un front cible pour:
- proprietaires immobiliers
- agences immobilieres

## 1. Base URL

En local, l'API tourne sur:

```text
http://127.0.0.1:8000/api
```

Dans React, configure une variable d'environnement:

```env
VITE_API_URL=http://127.0.0.1:8000/api
```

Ou avec Create React App:

```env
REACT_APP_API_URL=http://127.0.0.1:8000/api
```

## 2. Authentification

Le frontend doit:
1. appeler `POST /api/auth/login/`
2. recuperer `access` et `refresh`
3. stocker les tokens en `localStorage`
4. envoyer ensuite le header:

```http
Authorization: Bearer <access_token>
```

### Claves de stockage recommandees

- `accessToken`
- `refreshToken`

## 3. Routes publiques

Ces routes peuvent etre appelees sans token:

- `POST /api/auth/register/`
- `POST /api/auth/login/`
- `POST /api/auth/refresh/`
- `POST /api/auth/verify-email/`
- `POST /api/auth/resend-verification/`
- `GET /api/biens/`
- `GET /api/biens/{id}/`
- `GET /api/villes/`
- `GET /api/types-bien/`
- `GET /api/search/`

## 4. Routes privees utiles pour proprietaire/agence

### Profil utilisateur

- `GET /api/utilisateurs/me/`
- `PUT /api/utilisateurs/me/update/`
- `GET /api/utilisateurs/profile/`
- `GET /api/utilisateurs/profil-proprietaire/`
- `GET /api/utilisateurs/profil-agence/`

### Biens

- `GET /api/biens/mes_biens/`
- `POST /api/biens/`
- `PUT /api/biens/{id}/`
- `PATCH /api/biens/{id}/`
- `DELETE /api/biens/{id}/`
- `GET /api/biens/{id}/disponibilites/`

### Documents

- `GET /api/documents/`
- `POST /api/documents/`
- `GET /api/documents/mes_documents/`
- `PUT /api/documents/{id}/`
- `DELETE /api/documents/{id}/`

### Images

- `GET /api/images/`
- `POST /api/images/`
- `GET /api/images/mes_images/`
- `DELETE /api/images/{id}/`

### Reservations

- `GET /api/reservations/`
- `POST /api/reservations/`
- `GET /api/reservations/mes_reservations/`
- `GET /api/reservations/reservations_pour_mes_biens/`
- `GET /api/reservations/calendrier/?bien_id=1&mois=5&annee=2026`
- `PUT /api/reservations/{id}/status/`

### Messages

- `GET /api/messages/`
- `POST /api/messages/`
- `GET /api/messages/mes_messages/`
- `GET /api/messages/conversations/`
- `GET /api/messages/conversation/{conversation_id}/`
- `POST /api/messages/{id}/read/`

### Notifications

- `GET /api/notifications/`
- `POST /api/notifications/`
- `GET /api/notifications/unread_count/`
- `POST /api/notifications/mark_all_as_read/`
- `PUT /api/notifications/{id}/read/`

### Agences

- `GET /api/agences/`
- `POST /api/agences/`
- `PUT /api/agences/{id}/`
- `DELETE /api/agences/{id}/`

### Tarifs et abonnements

- `GET /api/tarifs/`
- `GET /api/abonnements/`
- `POST /api/abonnements/`
- `POST /api/abonnements/souscrire/`

### IA

- `GET /api/ia/recommendations/`
- `POST /api/ia/recommendations/`
- `POST /api/ia/recommendations/generer_recommandations/`
- `POST /api/ia/recherche/rechercher/`
- `POST /api/ia/verifier-document/verifier/`

## 5. Exemple de client React

```javascript
const API_BASE_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000/api";

function getToken() {
  return localStorage.getItem("accessToken");
}

async function apiRequest(path, options = {}) {
  const headers = {
    ...(options.headers || {}),
  };

  const token = getToken();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  if (options.body && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || data.message || `HTTP ${response.status}`);
  }

  return data;
}
```

## 6. Exemple de login

```javascript
async function login(email, password) {
  const data = await apiRequest("/auth/login/", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });

  localStorage.setItem("accessToken", data.access);
  localStorage.setItem("refreshToken", data.refresh);

  return data;
}
```

## 7. Recommandations pour le front proprietaire/agence

- ne pas afficher les pages liees aux locataires si le projet est reserve aux proprietaires/agences
- verifier le role apres `GET /api/utilisateurs/me/`
- rediriger vers le dashboard proprietaire ou agence selon `profile.role`
- afficher un message clair si le token est absent ou expire
- utiliser `401` ou `403` pour forcer un refresh/login

## 8. Flux conseille

1. login
2. stockage des tokens
3. recuperation du profil via `/api/utilisateurs/me/`
4. lecture du `role`
5. chargement du dashboard correspondant
6. consommation des routes privees

## 9. Important

Si le serveur Django n'est pas lance, React affichera `ERR_CONNECTION_REFUSED`.

Si une route privee retourne `403`, le plus probable est:
- token absent
- token expire
- header `Authorization` manquant

## 10. Resumé rapide

- base URL: `http://127.0.0.1:8000/api`
- token access dans `localStorage`
- header obligatoire pour les routes privees
- front cible: proprietaire + agence uniquement
