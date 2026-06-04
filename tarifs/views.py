from rest_framework import permissions, viewsets, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta

from .models import Tarif, Abonnement
from .serializers import TarifSerializer, AbonnementSerializer, AbonnementCreateSerializer


class TarifViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tarif.objects.filter(actif=True).order_by('prix')
    serializer_class = TarifSerializer
    permission_classes = [permissions.AllowAny]


class AbonnementViewSet(viewsets.ModelViewSet):
    serializer_class = AbonnementSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Abonnement.objects.filter(utilisateur=self.request.user).order_by('-created_at')

    def get_serializer_class(self):
        if self.action == 'create':
            return AbonnementCreateSerializer
        return AbonnementSerializer

    def perform_create(self, serializer):
        # Calculer date_fin basée sur le tarif
        tarif = serializer.validated_data['tarif']
        try:
            duree_mois = int(self.request.data.get('duree_mois', 1))
        except (TypeError, ValueError):
            duree_mois = 1
        
        date_debut = timezone.now()
        if tarif.duree == 'mensuel':
            date_fin = date_debut + timedelta(days=30 * duree_mois)
        elif tarif.duree == 'trimestriel':
            date_fin = date_debut + timedelta(days=90 * duree_mois)
        elif tarif.duree == 'semestriel':
            date_fin = date_debut + timedelta(days=180 * duree_mois)
        elif tarif.duree == 'annuel':
            date_fin = date_debut + timedelta(days=365 * duree_mois)
        else:
            date_fin = date_debut + timedelta(days=30 * duree_mois)

        serializer.save(utilisateur=self.request.user, date_fin=date_fin)

    @action(detail=False, methods=['post'])
    def souscrire(self, request):
        """Souscrire à un plan tarifaire"""
        serializer = AbonnementCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            abonnement = serializer.save()
            return Response({
                'message': 'Abonnement créé avec succès',
                'abonnement': AbonnementSerializer(abonnement).data
            })
        return Response(serializer.errors, status=400)
