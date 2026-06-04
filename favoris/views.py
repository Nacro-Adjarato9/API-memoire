from rest_framework import generics, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Favori
from .serializers import FavoriSerializer, FavoriCreateSerializer


class FavoriViewSet(viewsets.ModelViewSet):
    queryset = Favori.objects.all().order_by('-created_at')
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return FavoriCreateSerializer
        return FavoriSerializer

    def perform_create(self, serializer):
        serializer.save(utilisateur=self.request.user)

    def get_queryset(self):
        queryset = super().get_queryset()
        ville = self.request.query_params.get('ville')
        type_bien = self.request.query_params.get('type_bien')
        prix_min = self.request.query_params.get('prix_min')
        prix_max = self.request.query_params.get('prix_max')

        if ville:
            queryset = queryset.filter(bien__ville__iexact=ville)
        if type_bien:
            queryset = queryset.filter(bien__type__iexact=type_bien)
        if prix_min:
            queryset = queryset.filter(bien__prix__gte=prix_min)
        if prix_max:
            queryset = queryset.filter(bien__prix__lte=prix_max)

        return queryset.filter(utilisateur=self.request.user)

    @action(detail=False, methods=['get'])
    def count(self, request):
        """Obtenir le nombre de favoris de l'utilisateur"""
        count = self.get_queryset().count()
        return Response({'count': count})

    @action(detail=False, methods=['post'])
    def toggle(self, request, pk=None):
        """Ajouter ou supprimer un favori"""
        bien_id = request.data.get('bien_id') or request.query_params.get('bien_id')
        if not bien_id:
            return Response({'detail': 'bien_id requis'}, status=400)

        favori, created = Favori.objects.get_or_create(
            utilisateur=request.user,
            bien_id=bien_id
        )
        
        if not created:
            favori.delete()
            return Response({'action': 'removed', 'message': 'Favori supprimé'})
        
        serializer = self.get_serializer(favori)
        return Response({'action': 'added', 'favori': serializer.data})

