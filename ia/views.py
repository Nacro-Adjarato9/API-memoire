import json
from django.db.models import Q
from rest_framework import permissions, viewsets, status
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
from .services import (
    chat_immobilier, search_biens_intelligente, verify_document,
    recommande_villes_par_budget, extract_search_criteria, build_bien_queryset,
    serialize_biens_for_map, filter_points_by_radius, geocode_address, call_ai,
    suggerer_zones, recommend_for_user, get_trends,
)


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


class MapLogementsAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        criteria = extract_search_criteria(request.query_params)
        biens_queryset = list(build_bien_queryset(criteria)[:100])
        map_points = serialize_biens_for_map(biens_queryset, limit=100)

        lat = request.query_params.get("lat")
        lng = request.query_params.get("lng")
        rayon_km = request.query_params.get("rayon_km", 5)

        if lat is not None and lng is not None:
            try:
                map_points = filter_points_by_radius(
                    map_points,
                    float(lat),
                    float(lng),
                    float(rayon_km),
                )
            except (TypeError, ValueError):
                pass

        return Response(
            {
                "count": len(map_points),
                "results": map_points,
                "centre": {
                    "lat": float(lat) if lat is not None else None,
                    "lng": float(lng) if lng is not None else None,
                } if lat is not None and lng is not None else None,
            }
        )


class GeocoderAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        adresse = request.data.get("adresse", "").strip()
        ville = request.data.get("ville", "Abidjan")

        if not adresse:
            return Response({"error": "Adresse vide"}, status=status.HTTP_400_BAD_REQUEST)

        result = geocode_address(adresse, ville)
        if result:
            return Response(result)

        return Response({"error": "Adresse introuvable"}, status=status.HTTP_404_NOT_FOUND)


class BudgetAdvisoryView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        budget = request.data.get("budget")
        if not budget:
            return Response(
                {"error": "Budget requis"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            budget = int(budget)
        except (ValueError, TypeError):
            return Response(
                {"error": "Budget doit être un nombre"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        recommendations = recommande_villes_par_budget(budget)

        prompt = (
            f"Tu es conseiller immobilier expert en Côte d'Ivoire. "
            f"Un client dispose de {budget:,} FCFA pour chercher un logement. "
            f"Voici les villes recommandées: {json.dumps(recommendations, ensure_ascii=False)}. "
            f"Donne un conseil de 3-4 phrases sur le meilleur choix selon le rapport qualité-prix et les opportunités."
        )

        ai_advice, _ = call_ai(
            [
                {"role": "system", "content": "Tu es un expert immobilier conversationnel pour la Côte d'Ivoire."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=300,
            temperature=0.5,
        )

        return Response({
            "budget": budget,
            "villes_recommandees": recommendations,
            "conseil_ia": ai_advice or "Consultez nos experts pour une analyse personnalisée.",
        })


class TrendView(APIView):
    """Module 6 : lit uniquement le cache (pas de recalcul à la volée), rafraîchi par
    la commande `compute_trends` lancée périodiquement (cron/tâche planifiée)."""

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        trends = get_trends()
        ville = request.query_params.get("ville")
        if ville:
            trends = [t for t in trends if t["ville"].lower() == ville.lower()]
        return Response({"count": len(trends), "results": trends})


class RecommendationsPersonnaliseesView(APIView):
    """Module 2 : biens suggérés à partir de l'historique de recherche et des favoris."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        suggestions = recommend_for_user(request.user)
        return Response({"count": len(suggestions), "results": suggestions})


class ZoneSuggestionsView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        ville = request.query_params.get("ville")
        if not ville:
            return Response({"error": "Paramètre 'ville' requis"}, status=status.HTTP_400_BAD_REQUEST)

        budget_max = request.query_params.get("budget_max")
        type_bien = request.query_params.get("type")

        suggestions = suggerer_zones(ville, budget_max=budget_max, type_bien=type_bien)
        return Response({"ville": ville, "suggestions": suggestions})


class IAChatView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        message = request.data.get("message", "")
        history = request.data.get("history", [])
        lat = request.data.get("lat")
        lng = request.data.get("lng")

        if not message:
            return Response({"error": "Message requis"}, status=400)

        payload = chat_immobilier(message, history, lat, lng)
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
                "map_points": response_data.get("map_points", []),
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
        document_data = request.data.get("document_data")

        result = verify_document(document_type, document_url, document_data)

        return Response(result, status=status.HTTP_200_OK)


class RecommendationIAViewSet(viewsets.ModelViewSet):
    queryset = RecommendationIA.objects.all().order_by("-created_at")
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        if self.action == "create":
            return RecommendationIACreateSerializer
        return RecommendationIASerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_authenticated:
            return queryset.filter(user=self.request.user)
        return queryset.none()

    def perform_create(self, serializer):
        # Obligatoire car le modèle n'est pas nullable
        serializer.save(user=self.request.user)

    @action(detail=False, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def generer_recommandations(self, request):
        """Génère une recommandation IA à partir des critères fournis et l'enregistre pour l'utilisateur connecté."""
        serializer = RecommendationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        criteria = serializer.validated_data
        response = search_biens_intelligente(criteria)

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

        return Response(response, status=status.HTTP_201_CREATED)
