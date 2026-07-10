"""
Service Didit - gere les appels a l'API Didit pour la verification KYC
(carte d'identite / passeport) des proprietaires et agences.

Variables d'environnement necessaires (voir .env.example) :
- DIDIT_API_KEY       : cle API Didit (dashboard > API & Webhooks)
- DIDIT_WORKFLOW_ID   : ID du workflow "KYC gratuit" cree dans le dashboard
- DIDIT_WEBHOOK_SECRET: secret de signature genere lors de la configuration
                        de l'URL de webhook dans le dashboard Didit
"""
import hashlib
import hmac
import os

import requests

DIDIT_API_KEY = os.environ.get("DIDIT_API_KEY")
DIDIT_WORKFLOW_ID = os.environ.get("DIDIT_WORKFLOW_ID")
DIDIT_WEBHOOK_SECRET = os.environ.get("DIDIT_WEBHOOK_SECRET")

BASE_URL = "https://verification.didit.me/v3"


class DiditError(Exception):
    """Erreur levee quand l'appel a l'API Didit echoue."""


def create_verification_session(vendor_data: str, callback_url: str) -> dict:
    """
    Cree une session de verification pour un utilisateur donne.

    vendor_data : identifiant interne stable (ex: str(profil.id)) -> permet de
                  retrouver a qui appartient la session quand le webhook revient.
    callback_url: URL vers laquelle Didit redirige l'utilisateur une fois la
                  verification terminee.

    Retourne un dict contenant notamment "session_id" et "url".
    """
    if not DIDIT_API_KEY or not DIDIT_WORKFLOW_ID:
        raise DiditError("DIDIT_API_KEY ou DIDIT_WORKFLOW_ID manquant dans l'environnement.")

    response = requests.post(
        f"{BASE_URL}/session/",
        headers={
            "x-api-key": DIDIT_API_KEY,
            "Content-Type": "application/json",
        },
        json={
            "workflow_id": DIDIT_WORKFLOW_ID,
            "vendor_data": vendor_data,
            "callback": callback_url,
        },
        timeout=15,
    )

    if response.status_code >= 400:
        raise DiditError(f"Erreur Didit ({response.status_code}): {response.text}")

    return response.json()


def get_session_decision(session_id: str) -> dict:
    """Recupere le resultat (decision) d'une session : document valide ou non, etc."""
    if not DIDIT_API_KEY:
        raise DiditError("DIDIT_API_KEY manquant dans l'environnement.")

    response = requests.get(
        f"{BASE_URL}/session/{session_id}/decision/",
        headers={"x-api-key": DIDIT_API_KEY},
        timeout=15,
    )

    if response.status_code >= 400:
        raise DiditError(f"Erreur Didit ({response.status_code}): {response.text}")

    return response.json()


def verify_webhook_signature(raw_body: bytes, signature_header: str) -> bool:
    """
    Verifie que le webhook recu vient bien de Didit (evite qu'un tiers envoie
    de faux resultats de verification au backend).

    raw_body        : corps brut (bytes) de la requete recue, AVANT json.loads().
    signature_header: valeur de l'en-tete "X-Signature-V2".
    """
    if not DIDIT_WEBHOOK_SECRET or not signature_header:
        return False

    expected_signature = hmac.new(
        DIDIT_WEBHOOK_SECRET.encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(expected_signature, signature_header)
