import uuid

import requests
from django.conf import settings

CINETPAY_INIT_URL = "https://api-checkout.cinetpay.com/v2/payment"
CINETPAY_CHECK_URL = "https://api-checkout.cinetpay.com/v2/payment/check"


class CinetPayError(Exception):
    pass


def generer_reference_transaction():
    return f"LOGECIV-{uuid.uuid4().hex[:20]}"


def initier_paiement(*, montant, description, reference_transaction, client_nom, client_telephone, client_email):
    """Crée une transaction de paiement CinetPay et renvoie l'URL de paiement à ouvrir côté client."""
    api_key = getattr(settings, "CINETPAY_API_KEY", "")
    site_id = getattr(settings, "CINETPAY_SITE_ID", "")

    if not api_key or not site_id:
        raise CinetPayError("Configuration CinetPay manquante (CINETPAY_API_KEY / CINETPAY_SITE_ID).")

    payload = {
        "apikey": api_key,
        "site_id": site_id,
        "transaction_id": reference_transaction,
        "amount": int(montant),
        "currency": "XOF",
        "description": description or "Paiement LogeCiv",
        "notify_url": getattr(settings, "CINETPAY_NOTIFY_URL", ""),
        "return_url": getattr(settings, "CINETPAY_RETURN_URL", ""),
        "channels": "ALL",
        "customer_name": client_nom or "Client",
        "customer_surname": "",
        "customer_email": client_email or "client@logeciv.ci",
        "customer_phone_number": client_telephone or "",
    }

    try:
        response = requests.post(CINETPAY_INIT_URL, json=payload, timeout=15)
        data = response.json()
    except (requests.RequestException, ValueError) as exc:
        raise CinetPayError(f"Erreur de communication avec CinetPay: {exc}") from exc

    if data.get("code") != "201":
        raise CinetPayError(data.get("message") or "Échec de l'initialisation du paiement CinetPay.")

    return {
        "payment_url": data["data"]["payment_url"],
        "payment_token": data["data"]["payment_token"],
    }


def verifier_paiement(reference_transaction):
    """Interroge CinetPay pour connaître le statut réel d'une transaction (source de vérité, jamais le body du webhook)."""
    api_key = getattr(settings, "CINETPAY_API_KEY", "")
    site_id = getattr(settings, "CINETPAY_SITE_ID", "")

    if not api_key or not site_id:
        raise CinetPayError("Configuration CinetPay manquante (CINETPAY_API_KEY / CINETPAY_SITE_ID).")

    payload = {
        "apikey": api_key,
        "site_id": site_id,
        "transaction_id": reference_transaction,
    }

    try:
        response = requests.post(CINETPAY_CHECK_URL, json=payload, timeout=15)
        data = response.json()
    except (requests.RequestException, ValueError) as exc:
        raise CinetPayError(f"Erreur de communication avec CinetPay: {exc}") from exc

    statut_cinetpay = (data.get("data") or {}).get("status")
    if statut_cinetpay == "ACCEPTED":
        return "succes", data
    if statut_cinetpay in ("REFUSED", "CANCELLED"):
        return "echec", data
    return "en_attente", data
