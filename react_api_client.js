// Client API React pour consommer l'API Django
// Utilisation recommandée:
// - copie ce fichier dans ton projet React, par exemple: src/services/api.js
// - configure REACT_APP_API_URL ou VITE_API_URL

const API_BASE_URL =
  (typeof import.meta !== "undefined" &&
    import.meta.env &&
    import.meta.env.VITE_API_URL) ||
  (typeof process !== "undefined" &&
    process.env &&
    process.env.REACT_APP_API_URL) ||
  "http://127.0.0.1:8000/api";

const TOKEN_KEY = "accessToken";
const REFRESH_TOKEN_KEY = "refreshToken";

function getToken() {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setTokens({ access, refresh }) {
  if (typeof window === "undefined") return;
  if (access) localStorage.setItem(TOKEN_KEY, access);
  if (refresh) localStorage.setItem(REFRESH_TOKEN_KEY, refresh);
}

export function clearTokens() {
  if (typeof window === "undefined") return;
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
}

export function getStoredTokens() {
  if (typeof window === "undefined") {
    return { access: null, refresh: null };
  }
  return {
    access: localStorage.getItem(TOKEN_KEY),
    refresh: localStorage.getItem(REFRESH_TOKEN_KEY),
  };
}

async function apiRequest(path, options = {}) {
  const isFormData = typeof FormData !== "undefined" && options.body instanceof FormData;
  const headers = {
    ...(options.headers || {}),
  };

  const token = getToken();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  if (!isFormData && options.body && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  });

  const contentType = response.headers.get("content-type") || "";
  const data = contentType.includes("application/json")
    ? await response.json()
    : await response.text();

  if (!response.ok) {
    const message =
      (data && typeof data === "object" && (data.detail || data.message)) ||
      `Erreur API (${response.status})`;
    const error = new Error(message);
    error.status = response.status;
    error.data = data;
    throw error;
  }

  return data;
}

function jsonBody(payload) {
  return payload === undefined ? undefined : JSON.stringify(payload);
}

// -------------------------
// Authentification
// -------------------------
export const authAPI = {
  register(payload) {
    return apiRequest("/auth/register/", {
      method: "POST",
      body: jsonBody(payload),
    });
  },

  login(payload) {
    return apiRequest("/auth/login/", {
      method: "POST",
      body: jsonBody(payload),
    }).then((data) => {
      if (data && typeof data === "object" && (data.access || data.refresh)) {
        setTokens({
          access: data.access,
          refresh: data.refresh,
        });
      }
      return data;
    });
  },

  refresh(payload) {
    return apiRequest("/auth/refresh/", {
      method: "POST",
      body: jsonBody(payload),
    }).then((data) => {
      if (data && typeof data === "object" && data.access) {
        setTokens({
          access: data.access,
        });
      }
      return data;
    });
  },

  logout() {
    return apiRequest("/auth/logout/", {
      method: "POST",
    }).finally(() => {
      clearTokens();
    });
  },

  verifyEmail(payload) {
    return apiRequest("/auth/verify-email/", {
      method: "POST",
      body: jsonBody(payload),
    });
  },

  resendVerification(payload) {
    return apiRequest("/auth/resend-verification/", {
      method: "POST",
      body: jsonBody(payload),
    });
  },
};

// -------------------------
// Utilisateurs
// -------------------------
export const usersAPI = {
  me() {
    return apiRequest("/utilisateurs/me/");
  },

  updateMe(payload) {
    return apiRequest("/utilisateurs/me/update/", {
      method: "PUT",
      body: jsonBody(payload),
    });
  },

  profile() {
    return apiRequest("/utilisateurs/profile/");
  },

  profilProprietaire() {
    return apiRequest("/utilisateurs/profil-proprietaire/");
  },

  updateProfilProprietaire(payload) {
    return apiRequest("/utilisateurs/profil-proprietaire/", {
      method: "PUT",
      body: jsonBody(payload),
    });
  },

  verifierProfilProprietaire(payload) {
    return apiRequest("/utilisateurs/profil-proprietaire/verifier/", {
      method: "POST",
      body: payload instanceof FormData ? payload : jsonBody(payload),
    });
  },

  profilAgence() {
    return apiRequest("/utilisateurs/profil-agence/");
  },

  updateProfilAgence(payload) {
    return apiRequest("/utilisateurs/profil-agence/", {
      method: "PUT",
      body: jsonBody(payload),
    });
  },

  verifierProfilAgence(payload) {
    return apiRequest("/utilisateurs/profil-agence/verifier/", {
      method: "POST",
      body: payload instanceof FormData ? payload : jsonBody(payload),
    });
  },

  passwordReset(payload) {
    return apiRequest("/utilisateurs/password-reset/", {
      method: "POST",
      body: jsonBody(payload),
    });
  },

  signalementsList() {
    return apiRequest("/utilisateurs/signalements/");
  },

  createSignalement(payload) {
    return apiRequest("/utilisateurs/signalements/", {
      method: "POST",
      body: jsonBody(payload),
    });
  },

  signalementDetail(id) {
    return apiRequest(`/utilisateurs/signalements/${id}/`);
  },

  deleteSignalement(id) {
    return apiRequest(`/utilisateurs/signalements/${id}/`, {
      method: "DELETE",
    });
  },

  deleteAccount() {
    return apiRequest("/utilisateurs/delete/", {
      method: "DELETE",
    });
  },

  locataires() {
    return apiRequest("/locataires/");
  },

  acteurs() {
    return apiRequest("/acteurs/");
  },

  agents() {
    return apiRequest("/agents/");
  },

  agentDetail(id) {
    return apiRequest(`/agents/${id}/`);
  },

  agentBiens(id) {
    return apiRequest(`/agents/${id}/biens/`);
  },

  agentAvis(id) {
    return apiRequest(`/agents/${id}/avis/`);
  },

  laisserAvisAgent(id, payload) {
    return apiRequest(`/agents/${id}/avis/ajouter/`, {
      method: "POST",
      body: jsonBody(payload),
    });
  },
};

// -------------------------
// Biens / Documents / Images
// -------------------------
export const biensAPI = {
  list(params = {}) {
    const query = new URLSearchParams(params).toString();
    return apiRequest(`/biens/${query ? `?${query}` : ""}`);
  },

  detail(id) {
    return apiRequest(`/biens/${id}/`);
  },

  create(payload) {
    return apiRequest("/biens/", {
      method: "POST",
      body: jsonBody(payload),
    });
  },

  update(id, payload) {
    return apiRequest(`/biens/${id}/`, {
      method: "PUT",
      body: jsonBody(payload),
    });
  },

  patch(id, payload) {
    return apiRequest(`/biens/${id}/`, {
      method: "PATCH",
      body: jsonBody(payload),
    });
  },

  remove(id) {
    return apiRequest(`/biens/${id}/`, {
      method: "DELETE",
    });
  },

  mesBiens() {
    return apiRequest("/biens/mes_biens/");
  },

  disponibilites(id) {
    return apiRequest(`/biens/${id}/disponibilites/`);
  },

  documents(params = {}) {
    const query = new URLSearchParams(params).toString();
    return apiRequest(`/documents/${query ? `?${query}` : ""}`);
  },

  documentDetail(id) {
    return apiRequest(`/documents/${id}/`);
  },

  createDocument(payload) {
    return apiRequest("/documents/", {
      method: "POST",
      body: jsonBody(payload),
    });
  },

  mesDocuments() {
    return apiRequest("/documents/mes_documents/");
  },
};

export const imagesAPI = {
  list(params = {}) {
    const query = new URLSearchParams(params).toString();
    return apiRequest(`/images/${query ? `?${query}` : ""}`);
  },

  detail(id) {
    return apiRequest(`/images/${id}/`);
  },

  create(payload) {
    return apiRequest("/images/", {
      method: "POST",
      body: jsonBody(payload),
    });
  },

  uploadMultiple(payload) {
    return apiRequest("/images/upload_multiple/", {
      method: "POST",
      body: jsonBody(payload),
    });
  },

  mesImages() {
    return apiRequest("/images/mes_images/");
  },
};

// -------------------------
// Réservations
// -------------------------
export const reservationsAPI = {
  list(params = {}) {
    const query = new URLSearchParams(params).toString();
    return apiRequest(`/reservations/${query ? `?${query}` : ""}`);
  },

  detail(id) {
    return apiRequest(`/reservations/${id}/`);
  },

  create(payload) {
    return apiRequest("/reservations/", {
      method: "POST",
      body: jsonBody(payload),
    });
  },

  update(id, payload) {
    return apiRequest(`/reservations/${id}/`, {
      method: "PUT",
      body: jsonBody(payload),
    });
  },

  patch(id, payload) {
    return apiRequest(`/reservations/${id}/`, {
      method: "PATCH",
      body: jsonBody(payload),
    });
  },

  remove(id) {
    return apiRequest(`/reservations/${id}/`, {
      method: "DELETE",
    });
  },

  mesReservations() {
    return apiRequest("/reservations/mes_reservations/");
  },

  reservationsPourMesBiens() {
    return apiRequest("/reservations/reservations_pour_mes_biens/");
  },

  calendrier(params) {
    const query = new URLSearchParams(params).toString();
    return apiRequest(`/reservations/calendrier/${query ? `?${query}` : ""}`);
  },

  updateStatus(id, payload) {
    return apiRequest(`/reservations/${id}/status/`, {
      method: "PUT",
      body: jsonBody(payload),
    });
  },
};

// -------------------------
// Messages / Chat
// -------------------------
export const chatAPI = {
  list(params = {}) {
    const query = new URLSearchParams(params).toString();
    return apiRequest(`/messages/${query ? `?${query}` : ""}`);
  },

  detail(id) {
    return apiRequest(`/messages/${id}/`);
  },

  create(payload) {
    return apiRequest("/messages/", {
      method: "POST",
      body: jsonBody(payload),
    });
  },

  update(id, payload) {
    return apiRequest(`/messages/${id}/`, {
      method: "PUT",
      body: jsonBody(payload),
    });
  },

  patch(id, payload) {
    return apiRequest(`/messages/${id}/`, {
      method: "PATCH",
      body: jsonBody(payload),
    });
  },

  remove(id) {
    return apiRequest(`/messages/${id}/`, {
      method: "DELETE",
    });
  },

  mesMessages() {
    return apiRequest("/messages/mes_messages/");
  },

  conversations() {
    return apiRequest("/messages/conversations/");
  },

  conversation(conversationId) {
    return apiRequest(`/messages/conversation/${conversationId}/`);
  },

  markAsRead(messageId) {
    return apiRequest(`/messages/${messageId}/read/`, {
      method: "POST",
    });
  },
};

// -------------------------
// Avis / Favoris
// -------------------------
export const avisAPI = {
  list(params = {}) {
    const query = new URLSearchParams(params).toString();
    return apiRequest(`/avis/${query ? `?${query}` : ""}`);
  },

  detail(id) {
    return apiRequest(`/avis/${id}/`);
  },

  create(payload) {
    return apiRequest("/avis/", {
      method: "POST",
      body: jsonBody(payload),
    });
  },

  update(id, payload) {
    return apiRequest(`/avis/${id}/`, {
      method: "PUT",
      body: jsonBody(payload),
    });
  },

  patch(id, payload) {
    return apiRequest(`/avis/${id}/`, {
      method: "PATCH",
      body: jsonBody(payload),
    });
  },

  remove(id) {
    return apiRequest(`/avis/${id}/`, {
      method: "DELETE",
    });
  },

  mesAvis() {
    return apiRequest("/avis/mes_avis/");
  },

  statistiques(params) {
    const query = new URLSearchParams(params).toString();
    return apiRequest(`/avis/statistiques/${query ? `?${query}` : ""}`);
  },
};

export const favorisAPI = {
  list(params = {}) {
    const query = new URLSearchParams(params).toString();
    return apiRequest(`/favoris/${query ? `?${query}` : ""}`);
  },

  detail(id) {
    return apiRequest(`/favoris/${id}/`);
  },

  create(payload) {
    return apiRequest("/favoris/", {
      method: "POST",
      body: jsonBody(payload),
    });
  },

  update(id, payload) {
    return apiRequest(`/favoris/${id}/`, {
      method: "PUT",
      body: jsonBody(payload),
    });
  },

  patch(id, payload) {
    return apiRequest(`/favoris/${id}/`, {
      method: "PATCH",
      body: jsonBody(payload),
    });
  },

  remove(id) {
    return apiRequest(`/favoris/${id}/`, {
      method: "DELETE",
    });
  },

  count() {
    return apiRequest("/favoris/count/");
  },

  toggle(payload) {
    return apiRequest("/favoris/toggle/", {
      method: "POST",
      body: jsonBody(payload),
    });
  },
};

// -------------------------
// Notifications / Agences
// -------------------------
export const notificationsAPI = {
  list(params = {}) {
    const query = new URLSearchParams(params).toString();
    return apiRequest(`/notifications/${query ? `?${query}` : ""}`);
  },

  detail(id) {
    return apiRequest(`/notifications/${id}/`);
  },

  create(payload) {
    return apiRequest("/notifications/", {
      method: "POST",
      body: jsonBody(payload),
    });
  },

  update(id, payload) {
    return apiRequest(`/notifications/${id}/`, {
      method: "PUT",
      body: jsonBody(payload),
    });
  },

  patch(id, payload) {
    return apiRequest(`/notifications/${id}/`, {
      method: "PATCH",
      body: jsonBody(payload),
    });
  },

  remove(id) {
    return apiRequest(`/notifications/${id}/`, {
      method: "DELETE",
    });
  },

  markAllAsRead() {
    return apiRequest("/notifications/mark_all_as_read/", {
      method: "POST",
    });
  },

  unreadCount() {
    return apiRequest("/notifications/unread_count/");
  },

  markAsRead(id) {
    return apiRequest(`/notifications/${id}/read/`, {
      method: "PUT",
    });
  },
};

export const agencesAPI = {
  list() {
    return apiRequest("/agences/");
  },

  detail(id) {
    return apiRequest(`/agences/${id}/`);
  },

  create(payload) {
    return apiRequest("/agences/", {
      method: "POST",
      body: jsonBody(payload),
    });
  },

  update(id, payload) {
    return apiRequest(`/agences/${id}/`, {
      method: "PUT",
      body: jsonBody(payload),
    });
  },

  patch(id, payload) {
    return apiRequest(`/agences/${id}/`, {
      method: "PATCH",
      body: jsonBody(payload),
    });
  },

  remove(id) {
    return apiRequest(`/agences/${id}/`, {
      method: "DELETE",
    });
  },
};

// -------------------------
// Tarifs / Abonnements
// -------------------------
export const tarifsAPI = {
  list() {
    return apiRequest("/tarifs/");
  },

  detail(id) {
    return apiRequest(`/tarifs/${id}/`);
  },
};

export const abonnementsAPI = {
  list() {
    return apiRequest("/abonnements/");
  },

  detail(id) {
    return apiRequest(`/abonnements/${id}/`);
  },

  create(payload) {
    return apiRequest("/abonnements/", {
      method: "POST",
      body: jsonBody(payload),
    });
  },

  update(id, payload) {
    return apiRequest(`/abonnements/${id}/`, {
      method: "PUT",
      body: jsonBody(payload),
    });
  },

  patch(id, payload) {
    return apiRequest(`/abonnements/${id}/`, {
      method: "PATCH",
      body: jsonBody(payload),
    });
  },

  remove(id) {
    return apiRequest(`/abonnements/${id}/`, {
      method: "DELETE",
    });
  },

  souscrire(payload) {
    return apiRequest("/abonnements/souscrire/", {
      method: "POST",
      body: jsonBody(payload),
    });
  },
};

// -------------------------
// IA / Utilitaires
// -------------------------
export const iaAPI = {
  recommendationsList() {
    return apiRequest("/ia/recommendations/");
  },

  recommendationDetail(id) {
    return apiRequest(`/ia/recommendations/${id}/`);
  },

  createRecommendation(payload) {
    return apiRequest("/ia/recommendations/", {
      method: "POST",
      body: jsonBody(payload),
    });
  },

  updateRecommendation(id, payload) {
    return apiRequest(`/ia/recommendations/${id}/`, {
      method: "PUT",
      body: jsonBody(payload),
    });
  },

  patchRecommendation(id, payload) {
    return apiRequest(`/ia/recommendations/${id}/`, {
      method: "PATCH",
      body: jsonBody(payload),
    });
  },

  removeRecommendation(id) {
    return apiRequest(`/ia/recommendations/${id}/`, {
      method: "DELETE",
    });
  },

  genererRecommandations(payload) {
    return apiRequest("/ia/recommendations/generer_recommandations/", {
      method: "POST",
      body: jsonBody(payload),
    });
  },

  rechercher(payload) {
    return apiRequest("/ia/recherche/rechercher/", {
      method: "POST",
      body: jsonBody(payload),
    });
  },

  verifierDocument(payload) {
    return apiRequest("/ia/verifier-document/verifier/", {
      method: "POST",
      body: jsonBody(payload),
    });
  },
};

export const utilsAPI = {
  search(q, type) {
    const params = new URLSearchParams();
    if (q) params.set("q", q);
    if (type) params.set("type", type);
    const query = params.toString();
    return apiRequest(`/search/${query ? `?${query}` : ""}`);
  },

  stats() {
    return apiRequest("/stats/");
  },

  villes() {
    return apiRequest("/villes/");
  },

  typesBien() {
    return apiRequest("/types-bien/");
  },

  locataires() {
    return apiRequest("/locataires/");
  },

  acteurs() {
    return apiRequest("/acteurs/");
  },
};

// Export global pratique
export const api = {
  baseURL: API_BASE_URL,
  auth: authAPI,
  users: usersAPI,
  biens: biensAPI,
  images: imagesAPI,
  reservations: reservationsAPI,
  chat: chatAPI,
  avis: avisAPI,
  favoris: favorisAPI,
  notifications: notificationsAPI,
  agences: agencesAPI,
  tarifs: tarifsAPI,
  abonnements: abonnementsAPI,
  ia: iaAPI,
  utils: utilsAPI,
  setTokens,
  clearTokens,
  getStoredTokens,
};

export default api;
