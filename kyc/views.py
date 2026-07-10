"""
Vues DRF pour la verification d'identite (Didit) des proprietaires et agences.
"""
import json
import logging

from django.conf import settings
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from utilisateurs.models import KycStatus, ProfilAgence, ProfilProprietaire

from . import didit_service

logger = logging.getLogger(__name__)

FRONTEND_RETURN_URL = getattr(settings, "DIDIT_FRONTEND_RETURN_URL", "")


def _get_kyc_profile(user):
    """Renvoie le ProfilProprietaire ou ProfilAgence de l'utilisateur connecte,
    selon son role (meme logique que biens/utilisateurs pour distinguer
    proprietaire vs agence/agent). Renvoie None si ce profil n'a pas encore ete
    cree (aucun signal ne le cree automatiquement, contrairement a UserProfile)."""
    profile = getattr(user, "profile", None)
    role = getattr(profile, "role", None)
    if role in ("agent", "agence"):
        return getattr(user, "profil_agence", None)
    return getattr(user, "profil_proprietaire", None)


class StartKycView(APIView):
    """
    POST /api/kyc/start/
    Cree une session Didit pour l'utilisateur connecte (proprietaire ou agence)
    et renvoie l'URL a laquelle le rediriger pour qu'il/elle scanne sa piece
    d'identite.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        profil = _get_kyc_profile(request.user)
        if profil is None:
            return Response(
                {
                    "error": "Complétez d'abord votre profil (propriétaire ou agence) "
                    "avant de vérifier votre identité."
                },
                status=400,
            )

        try:
            session = didit_service.create_verification_session(
                vendor_data=f"{profil.__class__.__name__}:{profil.id}",
                callback_url=FRONTEND_RETURN_URL,
            )
        except didit_service.DiditError as exc:
            return Response({"error": str(exc)}, status=502)

        profil.kyc_status = KycStatus.PENDING
        profil.kyc_session_id = session["session_id"]
        profil.save(update_fields=["kyc_status", "kyc_session_id"])

        return Response({"session_id": session["session_id"], "verification_url": session["url"]})


class KycStatusView(APIView):
    """
    GET /api/kyc/status/
    Renvoie le statut de verification Didit de l'utilisateur connecte, pour
    que le frontend affiche un badge "non vérifié / en cours / vérifié".
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        profil = _get_kyc_profile(request.user)
        if profil is None:
            return Response({"kyc_status": KycStatus.NOT_STARTED, "kyc_verified_at": None})

        # Rafraichissement "best effort" : utile en developpement quand le webhook
        # Didit ne peut pas atteindre localhost. En cas d'echec on garde simplement
        # la derniere valeur connue (normalement mise a jour par le webhook).
        if profil.kyc_status == KycStatus.PENDING and profil.kyc_session_id:
            try:
                decision = didit_service.get_session_decision(profil.kyc_session_id)
                statut_distant = decision.get("status")
                if statut_distant == "Approved":
                    profil.kyc_status = KycStatus.APPROVED
                    profil.kyc_verified_at = timezone.now()
                    profil.save(update_fields=["kyc_status", "kyc_verified_at"])
                elif statut_distant == "Declined":
                    profil.kyc_status = KycStatus.DECLINED
                    profil.save(update_fields=["kyc_status"])
            except didit_service.DiditError:
                pass

        return Response({"kyc_status": profil.kyc_status, "kyc_verified_at": profil.kyc_verified_at})


@csrf_exempt
@api_view(["POST"])
@permission_classes([AllowAny])  # la securite vient de la signature HMAC, pas de la session Django
def didit_webhook(request):
    """
    POST /api/kyc/webhook/
    Appele automatiquement par Didit quand le statut d'une session change.
    Doit repondre en moins de 5 secondes.

    IMPORTANT : cette URL doit etre enregistree dans le dashboard Didit et etre
    accessible publiquement (pas localhost - utiliser ngrok ou equivalent en dev).
    """
    raw_body = request.body
    signature = request.headers.get("X-Signature-V2", "")

    if not didit_service.verify_webhook_signature(raw_body, signature):
        return Response({"error": "signature invalide"}, status=401)

    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError:
        return Response({"error": "payload invalide"}, status=400)

    session_id = payload.get("session_id")
    status_value = payload.get("status")  # ex: "Approved", "Declined", "In Review"

    if not session_id:
        return Response({"error": "session_id manquant"}, status=400)

    # Aucun utilisateur authentifie dans une requete webhook : on cherche la
    # session dans les deux modeles possibles (proprietaire puis agence).
    profil = ProfilProprietaire.objects.filter(kyc_session_id=session_id).first()
    if profil is None:
        profil = ProfilAgence.objects.filter(kyc_session_id=session_id).first()

    if profil is None:
        logger.warning("Webhook Didit recu pour une session inconnue: %s", session_id)
        return Response({"ok": True})

    if status_value == "Approved":
        profil.kyc_status = KycStatus.APPROVED
        profil.kyc_verified_at = timezone.now()
    elif status_value == "Declined":
        profil.kyc_status = KycStatus.DECLINED
    else:
        profil.kyc_status = KycStatus.PENDING

    profil.save(update_fields=["kyc_status", "kyc_verified_at"])

    return Response({"ok": True})
