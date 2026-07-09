from rest_framework import generics, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from notifications.services import notify

from .models import Avis
from .serializers import AvisSerializer, AvisCreateSerializer


class AvisViewSet(viewsets.ModelViewSet):
    queryset = Avis.objects.all().order_by('-created_at')

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def get_serializer_class(self):
        if self.action == 'create':
            return AvisCreateSerializer
        return AvisSerializer

    def perform_create(self, serializer):
        avis = serializer.save(utilisateur=self.request.user)
        destinataire = avis.bien.agence or avis.bien.proprietaire
        notify(
            destinataire,
            f"Nouvel avis ({avis.note}/5) de {self.request.user.username} sur \"{avis.bien.titre}\"",
        )

    def get_queryset(self):
        queryset = super().get_queryset()
        bien_id = self.request.query_params.get('bien_id')
        note_min = self.request.query_params.get('note_min')

        if bien_id:
            queryset = queryset.filter(bien_id=bien_id)
        if note_min:
            queryset = queryset.filter(note__gte=note_min)

        return queryset

    @action(detail=False, methods=['get'])
    def mes_avis(self, request):
        """Récupérer les avis de l'utilisateur connecté"""
        avis = self.get_queryset().filter(utilisateur=request.user)
        serializer = self.get_serializer(avis, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def statistiques(self, request):
        """Obtenir les statistiques des avis pour un bien"""
        bien_id = request.query_params.get('bien_id')
        if not bien_id:
            return Response({'detail': 'bien_id requis'}, status=400)
        
        avis = Avis.objects.filter(bien_id=bien_id)
        if not avis.exists():
            return Response({
                'bien_id': bien_id,
                'total_avis': 0,
                'note_moyenne': 0,
                'distribution': {}
            })
        
        total = avis.count()
        moyenne = sum(a.note for a in avis) / total
        
        distribution = {}
        for note in range(1, 6):
            distribution[note] = avis.filter(note=note).count()
        
        return Response({
            'bien_id': bien_id,
            'total_avis': total,
            'note_moyenne': round(moyenne, 1),
            'distribution': distribution
        })
