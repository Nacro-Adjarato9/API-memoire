from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import RecommendationIA
from .serializers import (
    IAVerifyDocumentSerializer,
    IAChatSerializer,
    RecommendationIACreateSerializer,
    RecommendationIASerializer,
    RecommendationRequestSerializer,
)
from .services import call_ai, search_biens_intelligente, chat_immobilier, verify_document


def _call_grok(prompt, max_tokens=1000, temperature=0.7):
    return call_ai(
        [{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=temperature,
    )


class RecommendationAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RecommendationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        criteria = serializer.validated_data
        response = search_biens_intelligente(criteria)

        if request.user and request.user.is_authenticated:
            recommendation = RecommendationIA.objects.create(
                user=request.user,
                budget_min=criteria.get("budget_min"),
                budget_max=criteria.get("budget_max"),
                ville=criteria.get("ville") or "",
                type_bien=criteria.get("type_bien") or "",
                nombre_chambres_min=criteria.get("nombre_chambres"),
                localisation=criteria.get("quartier") or criteria.get("commune") or criteria.get("proximite") or "",
                resultats=response.get("resultats") or response.get("suggestions"),
                score=95 if response.get("resultats") else 80,
                analyse_ia=response.get("analyse_ia"),
                historique=response.get("criteres"),
            )
            response["recommendation_id"] = recommendation.id

        return Response(response)


class IAChatView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = IAChatSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = chat_immobilier(serializer.validated_data["message"])
        return Response(payload)


class RechercheIAView(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]

    @action(detail=False, methods=["post"])
    def rechercher(self, request):
        serializer = RecommendationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        response_data = search_biens_intelligente(serializer.validated_data)
        return Response(
            {
                "texte": response_data["criteres"].get("texte", ""),
                "type": response_data["type"],
                "message": response_data["message"],
                "analyse_ia": response_data["analyse_ia"],
                "criteres_extraits": response_data["criteres"],
                "resultats": response_data["resultats"],
                "suggestions": response_data["suggestions"],
            }
        )


class IAVerifyDocumentView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = IAVerifyDocumentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        document_url = serializer.validated_data["document_url"]
        document_type = serializer.validated_data.get("document_type", "cni")

        prompt = (
            "En tant qu'expert en verification de documents d'identite pour l'immobilier en Cote d'Ivoire, "
            f"analyse ce document de type '{document_type}' a l'URL : {document_url}. "
            "Retourne un JSON avec valide, confiance, message, details."
        )

        ai_response, error = _call_grok(prompt, max_tokens=800, temperature=0.2)
        valide = False
        confiance = 0
        message = "Verification manuelle recommandee"
        details = {
            "type_detecte": document_type.upper(),
            "qualite": "Non evaluee",
            "authentique": False,
            "recommandations": "Verification manuelle conseillee",
        }

        if ai_response:
            try:
                parsed = json.loads(ai_response)
                valide = bool(parsed.get("valide", parsed.get("valid", False)))
                confiance = int(parsed.get("confiance", parsed.get("confidence", 0)))
                message = parsed.get("message", message)
                details = parsed.get("details", details)
            except (ValueError, TypeError):
                message = "Analyse IA invalide ou mal formatée. Verification manuelle recommandée."
        else:
            message = f"Analyse IA indisponible. {error or ''}".strip()

        return Response(
            {
                "valide": valide,
                "confiance": confiance,
                "message": message,
                "details": details,
                "document_url": document_url,
                "document_type": document_type,
                "ai_response": ai_response,
            }
        )


class RecommendationIAViewSet(viewsets.ModelViewSet):
    queryset = RecommendationIA.objects.all().order_by("-created_at")
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "create":
            return RecommendationIACreateSerializer
        return RecommendationIASerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
