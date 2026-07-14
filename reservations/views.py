from django.db.models import Q
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from notifications.services import notify

from .models import Reservation
from .serializers import (
    ReservationCreateSerializer,
    ReservationSerializer,
    ReservationStatusSerializer,
)


class ReservationViewSet(viewsets.ModelViewSet):
    queryset = Reservation.objects.all().order_by("-created_at")
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "create":
            return ReservationCreateSerializer
        return ReservationSerializer

    def perform_create(self, serializer):
        reservation = serializer.save(utilisateur=self.request.user)
        destinataire = reservation.bien.agence or reservation.bien.proprietaire
        notify(
            destinataire,
            f"Nouveau rendez-vous de visite avec {self.request.user.username} pour \"{reservation.bien.titre}\"",
            type='reservation', bien=reservation.bien, reservation=reservation,
        )
        # Auto-confirmé dès la création (pas d'action requise du propriétaire) :
        # le locataire est notifié immédiatement, pas seulement le propriétaire.
        notify(
            reservation.utilisateur,
            f"Votre rendez-vous de visite pour \"{reservation.bien.titre}\" est confirmé",
            type='reservation', bien=reservation.bien, reservation=reservation,
        )

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        role = getattr(getattr(user, "profile", None), "role", None)
        status_filter = self.request.query_params.get("status")
        bien_id = self.request.query_params.get("bien_id")

        if role in ("proprietaire", "agent", "agence", "admin"):
            queryset = queryset.filter(Q(bien__proprietaire=user) | Q(bien__agence=user))
        else:
            queryset = queryset.filter(utilisateur=user)

        if status_filter:
            queryset = queryset.filter(status__iexact=status_filter)
        if bien_id:
            queryset = queryset.filter(bien_id=bien_id)

        return queryset

    @action(detail=False, methods=["get"])
    def mes_reservations(self, request):
        reservations = Reservation.objects.filter(utilisateur=request.user).order_by("-created_at")
        serializer = self.get_serializer(reservations, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def reservations_pour_mes_biens(self, request):
        reservations = Reservation.objects.filter(
            Q(bien__proprietaire=request.user) | Q(bien__agence=request.user)
        ).order_by("-created_at")

        status_filter = self.request.query_params.get("status")
        bien_id = self.request.query_params.get("bien_id")
        if status_filter:
            reservations = reservations.filter(status__iexact=status_filter)
        if bien_id:
            reservations = reservations.filter(bien_id=bien_id)

        serializer = self.get_serializer(reservations, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def calendrier(self, request):
        bien_id = request.query_params.get("bien_id")
        mois = request.query_params.get("mois")
        annee = request.query_params.get("annee")

        if not bien_id:
            return Response({"error": "bien_id requis"}, status=400)

        reservations = Reservation.objects.filter(bien_id=bien_id, status="confirmed")
        if mois and annee:
            reservations = reservations.filter(date__month=mois, date__year=annee)

        dates_reservees = list(reservations.values_list("date", flat=True))
        return Response({
            "bien_id": bien_id,
            "dates_reservees": dates_reservees,
            "mois": mois,
            "annee": annee,
        })


class ReservationStatusUpdateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, pk):
        try:
            reservation = Reservation.objects.get(pk=pk)
        except Reservation.DoesNotExist:
            return Response({"detail": "Reservation introuvable"}, status=status.HTTP_404_NOT_FOUND)

        if request.user != reservation.bien.proprietaire and request.user != reservation.bien.agence:
            return Response({"detail": "Non autorise"}, status=status.HTTP_403_FORBIDDEN)

        serializer = ReservationStatusSerializer(reservation, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        statut_labels = {"confirmed": "confirmée", "cancelled": "annulée", "rejected": "refusée"}
        libelle = statut_labels.get(reservation.status, reservation.status)
        notify(
            reservation.utilisateur,
            f"Votre réservation pour \"{reservation.bien.titre}\" a été {libelle}",
            type='reservation', bien=reservation.bien, reservation=reservation,
        )

        return Response(ReservationSerializer(reservation).data)
