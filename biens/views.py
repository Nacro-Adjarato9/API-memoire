from django.db.models import Q
from rest_framework import permissions, viewsets, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import Bien, Document
from .serializers import BienSerializer, BienCreateSerializer, DocumentSerializer, DocumentCreateSerializer
from reservations.models import Reservation


class BienViewSet(viewsets.ModelViewSet):
    queryset = Bien.objects.all().order_by('-created_at')

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return BienCreateSerializer
        return BienSerializer

    def perform_create(self, serializer):
        profile = getattr(self.request.user, 'profile', None)
        if profile and profile.role in ('agent', 'agence'):
            serializer.save(agence=self.request.user)
        else:
            serializer.save(proprietaire=self.request.user)

    def get_object(self):
        obj = super().get_object()
        # Vérifier que l'utilisateur est propriétaire pour modification/suppression
        if self.action in ['update', 'partial_update', 'destroy']:
            if obj.proprietaire != self.request.user and obj.agence != self.request.user:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("Vous n'êtes pas autorisé à modifier ce bien.")
        return obj

    def get_queryset(self):
        queryset = super().get_queryset()
        prix_min = self.request.query_params.get('prix_min')
        prix_max = self.request.query_params.get('prix_max')
        ville = self.request.query_params.get('ville')
        type_ = self.request.query_params.get('type')
        statut = self.request.query_params.get('statut')
        nombre_chambres = self.request.query_params.get('nombre_chambres')

        if prix_min is not None and prix_min != '':
            queryset = queryset.filter(prix__gte=prix_min)
        if prix_max is not None and prix_max != '':
            queryset = queryset.filter(prix__lte=prix_max)
        if ville:
            queryset = queryset.filter(ville__iexact=ville)
        if type_:
            queryset = queryset.filter(type__iexact=type_)
        if statut:
            queryset = queryset.filter(statut__iexact=statut)
        if nombre_chambres:
            queryset = queryset.filter(nombre_chambres__gte=nombre_chambres)

        return queryset

    def list(self, request, *args, **kwargs):
        """Liste les biens ; si la recherche stricte donne peu/pas de résultats,
        élargit automatiquement (budget, zone, villes voisines) au lieu de renvoyer une liste vide."""
        queryset = self.filter_queryset(self.get_queryset())
        fallback_info = {"fallback": False, "relaxed": []}

        criteres_recherche = {
            "ville": self.request.query_params.get("ville"),
            "type_bien": self.request.query_params.get("type"),
            "budget_min": self.request.query_params.get("prix_min"),
            "budget_max": self.request.query_params.get("prix_max"),
            "nombre_chambres": self.request.query_params.get("nombre_chambres"),
        }
        a_des_criteres = any(v not in (None, "") for v in criteres_recherche.values())

        if a_des_criteres and queryset.count() < 3:
            from ia.services import search_with_fallback

            biens_elargis, fallback_info = search_with_fallback(criteres_recherche)
            ids = [bien.id for bien in biens_elargis]
            queryset = Bien.objects.filter(id__in=ids).order_by("prix")

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            response.data["fallback"] = fallback_info
            return response

        serializer = self.get_serializer(queryset, many=True)
        return Response({"results": serializer.data, "fallback": fallback_info})

    @swagger_auto_schema(
        operation_description="Récupérer les biens de l'utilisateur connecté ou tous les biens disponibles",
        responses={200: BienSerializer(many=True)}
    )
    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny])
    def mes_biens(self, request):
        """Récupérer les biens de l'utilisateur connecté ou tous les biens disponibles"""
        if request.user.is_authenticated:
            biens = self.get_queryset().filter(Q(proprietaire=request.user) | Q(agence=request.user))
        else:
            biens = self.get_queryset().filter(statut='disponible')

        serializer = self.get_serializer(biens, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def disponibilites(self, request, pk=None):
        """Récupérer les disponibilités d'un bien"""
        bien = self.get_object()
        # Pour l'instant, retourner un calendrier simple
        # En production, ceci serait lié à un modèle Disponibilite
        from datetime import datetime, timedelta
        today = datetime.now().date()
        disponibilites = []
        
        # Générer 30 jours de disponibilité (simplifié)
        for i in range(30):
            date = today + timedelta(days=i)
            # Vérifier s'il y a une réservation confirmée pour cette date
            reservation_exists = Reservation.objects.filter(
                bien=bien,
                date=date,
                status='confirmed'
            ).exists()
            
            disponibilites.append({
                'date': date,
                'disponible': not reservation_exists
            })
        
        return Response(disponibilites)


class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all().order_by('-created_at')
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return DocumentCreateSerializer
        return DocumentSerializer

    def perform_create(self, serializer):
        profile = getattr(self.request.user, 'profile', None)
        if profile and profile.role in ('agent', 'agence'):
            serializer.save(agence=self.request.user)
        else:
            serializer.save(proprietaire=self.request.user)

    def get_queryset(self):
        queryset = super().get_queryset()
        type_document = self.request.query_params.get('type_document')
        statut = self.request.query_params.get('statut')
        user = self.request.user

        if not user.is_authenticated:
            return queryset.none()

        if type_document:
            queryset = queryset.filter(type_document__iexact=type_document)
        if statut:
            queryset = queryset.filter(statut_verification__iexact=statut)

        return queryset.filter(Q(proprietaire=user) | Q(agence=user))

    @action(detail=False, methods=['get'])
    def mes_documents(self, request):
        """Récupérer les documents de l'utilisateur connecté"""
        if not request.user.is_authenticated:
            return Response([])
        documents = self.get_queryset().filter(Q(proprietaire=request.user) | Q(agence=request.user))
        serializer = self.get_serializer(documents, many=True)
        return Response(serializer.data)
