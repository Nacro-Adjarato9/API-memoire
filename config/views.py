from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import permissions
from django.db.models import Q, Count, Avg, Sum

from avis.models import Avis
from biens.models import Bien
from reservations.models import Reservation
from utilisateurs.models import UserProfile, Paiement

ACTOR_ROLES = ("proprietaire", "agent", "agence", "admin")


class APIRootView(APIView):
    """API root - list available endpoints."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response({
            "message": "Bienvenue sur l'API Plaforme Immobiliere",
            "version": "1.0.0",
            "endpoints": {
                "authentication": {
                    "register": "/api/auth/register/",
                    "login": "/api/auth/login/",
                    "logout": "/api/auth/logout/",
                    "verify_email": "/api/auth/verify-email/",
                    "resend_verification": "/api/auth/resend-verification/",
                    "refresh": "/api/auth/refresh/",
                },
                "users": {
                    "list_current": "/api/utilisateurs/",
                    "profile": "/api/utilisateurs/me/",
                    "update": "/api/utilisateurs/me/update/",
                    "delete": "/api/utilisateurs/delete/",
                },
                "properties": {
                    "list_create": "/api/biens/",
                    "detail": "/api/biens/{id}/",
                },
                "images": {
                    "add": "/api/biens/{id}/images/",
                    "delete": "/api/images/{id}/",
                },
                "reservations": {
                    "list_create": "/api/reservations/",
                    "detail": "/api/reservations/{id}/",
                    "update_status": "/api/reservations/{id}/status/",
                },
                "messages": {
                    "list_create": "/api/messages/",
                    "conversation": "/api/messages/{conversation_id}/",
                },
                "reviews": {
                    "list_create": "/api/avis/",
                    "delete": "/api/avis/{id}/",
                },
                "favorites": {
                    "list_create": "/api/favoris/",
                    "delete": "/api/favoris/{id}/",
                },
                "agencies": {
                    "list_create": "/api/agences/",
                    "detail": "/api/agences/{id}/",
                },
                "notifications": {
                    "list": "/api/notifications/",
                    "mark_read": "/api/notifications/{id}/read/",
                },
                "ai": {
                    "search": "/api/ia/recherche/",
                    "verify_document": "/api/ia/verifier-document/",
                    "price_estimation": "/api/ia/prix-estimation/",
                    "market_analysis": "/api/ia/analyse-marche/",
                },
                "dashboard": {
                    "client": "/api/dashboard/client/",
                    "agence": "/api/dashboard/agence/",
                    "admin": "/api/dashboard/admin/",
                },
                "advanced_search": {
                    "endpoint": "/api/recherche/",
                    "params": ["q", "ville", "quartier", "type", "prix_min", "prix_max", "nombre_chambres"],
                },
                "admin": {
                    "admin_panel": "/admin/",
                },
            },
            "docs": {
                "full_documentation": "Voir API_DOCUMENTATION.md",
                "security": "Voir SECURITY_NOTES.md",
                "setup": "Voir CONFIG_GUIDE.md",
            }
        })


class SearchView(APIView):
    """Recherche globale et recherche avancée."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        query = request.query_params.get("q", "")
        ville = request.query_params.get("ville")
        quartier = request.query_params.get("quartier")
        type_filter = request.query_params.get("type")
        prix_min = request.query_params.get("prix_min")
        prix_max = request.query_params.get("prix_max")
        nombre_chambres = request.query_params.get("nombre_chambres")

        biens = Bien.objects.filter(statut="disponible")
        if query:
            biens = biens.filter(
                Q(titre__icontains=query)
                | Q(description__icontains=query)
                | Q(ville__icontains=query)
                | Q(localisation__icontains=query)
            )
        if ville:
            biens = biens.filter(ville__iexact=ville)
        if quartier:
            biens = biens.filter(localisation__icontains=quartier)
        if type_filter:
            biens = biens.filter(type__iexact=type_filter)
        if prix_min:
            biens = biens.filter(prix__gte=prix_min)
        if prix_max:
            biens = biens.filter(prix__lte=prix_max)
        if nombre_chambres:
            biens = biens.filter(nombre_chambres__gte=nombre_chambres)

        biens = biens[:10]

        results = {
            "biens": [
                {
                    "id": b.id,
                    "titre": b.titre,
                    "ville": b.ville,
                    "localisation": b.localisation,
                    "prix": b.prix,
                    "type": b.type,
                    "nombre_chambres": getattr(b, 'nombre_chambres', None),
                }
                for b in biens
            ],
            "locataires": [],
            "acteurs": [],
            "utilisateurs": [],
            "agences": [],
        }

        if query:
            users = (
                UserProfile.objects.filter(
                    Q(user__first_name__icontains=query)
                    | Q(user__last_name__icontains=query)
                    | Q(telephone__icontains=query)
                )
                .select_related("user")[:5]
            )

            utilisateurs = []
            for profile in users:
                payload = {
                    "id": profile.user.id,
                    "nom": f"{profile.user.first_name} {profile.user.last_name}".strip(),
                    "role": profile.role,
                    "ville": getattr(profile, "ville", ""),
                }
                utilisateurs.append(payload)

                if profile.role == "locataire":
                    results["locataires"].append(payload)
                elif profile.role in ACTOR_ROLES:
                    results["acteurs"].append(payload)

            results["utilisateurs"] = utilisateurs

        return Response(results)


class StatsView(APIView):
    """Dashboard stats."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        user = request.user
        stats = {}

        if hasattr(user, "profile"):
            profile = user.profile
            if profile.role == "proprietaire":
                biens_count = Bien.objects.filter(proprietaire=user).count()
                reservations_count = Reservation.objects.filter(bien__proprietaire=user).count()
                avis_count = Avis.objects.filter(bien__proprietaire=user).count()
                revenu_total = (
                    Reservation.objects.filter(bien__proprietaire=user, status="confirmed")
                    .aggregate(total=Sum("bien__prix"))["total"]
                    or 0
                )
                stats = {
                    "biens_count": biens_count,
                    "reservations_count": reservations_count,
                    "avis_count": avis_count,
                    "revenu_total": revenu_total,
                }
            elif profile.role == "locataire":
                reservations_count = Reservation.objects.filter(utilisateur=user).count()
                favoris_count = user.favoris.count() if hasattr(user, "favoris") else 0
                avis_count = Avis.objects.filter(utilisateur=user).count()
                stats = {
                    "reservations_count": reservations_count,
                    "favoris_count": favoris_count,
                    "avis_count": avis_count,
                }
            elif profile.role in ("agent", "agence"):
                biens_count = Bien.objects.filter(agence=user).count()
                reservations_count = Reservation.objects.filter(bien__agence=user).count()
                avis_count = Avis.objects.filter(bien__agence=user).count()
                stats = {
                    "biens_count": biens_count,
                    "reservations_count": reservations_count,
                    "avis_count": avis_count,
                }

        stats.update({
            "total_biens": Bien.objects.count(),
            "total_users": UserProfile.objects.count(),
        })
        return Response(stats)


class DashboardView(APIView):
    """Dashboard summary by scope."""
    permission_classes = [permissions.AllowAny]

    def get(self, request, scope):
        user = request.user
        profile = getattr(user, 'profile', None)
        response = {
            "scope": scope,
            "summary": {},
        }

        if scope == 'client':
            response["summary"] = {
                "reservations_count": Reservation.objects.filter(utilisateur=user).count(),
                "visites_count": user.visites.count() if hasattr(user, 'visites') else 0,
                "favoris_count": user.favoris.count() if hasattr(user, 'favoris') else 0,
                "avis_count": Avis.objects.filter(utilisateur=user).count(),
            }
        elif scope == 'agence':
            response["summary"] = {
                "biens_count": Bien.objects.filter(agence=user).count(),
                "reservations_count": Reservation.objects.filter(bien__agence=user).count(),
                "avis_count": Avis.objects.filter(bien__agence=user).count(),
                "prix_moyen_bien": Bien.objects.filter(agence=user).aggregate(Avg('prix'))['prix__avg'] or 0,
                "revenu_total": Paiement.objects.filter(utilisateur=user, statut='succes').aggregate(total=Sum('montant'))['total'] or 0,
            }
        elif scope == 'admin':
            response["summary"] = {
                "total_users": UserProfile.objects.count(),
                "total_biens": Bien.objects.count(),
                "total_reservations": Reservation.objects.count(),
                "total_revenu": Paiement.objects.filter(statut='succes').aggregate(total=Sum('montant'))['total'] or 0,
            }
        else:
            return Response({"detail": "Scope invalide. Utilisez client, agence ou admin."}, status=400)

        return Response(response)


class TypesBienView(APIView):
    """List property types."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        types_bien = [
            {"value": "appartement", "label": "Appartement"},
            {"value": "maison", "label": "Maison"},
            {"value": "terrain", "label": "Terrain"},
            {"value": "bureau", "label": "Bureau"},
            {"value": "commerce", "label": "Commerce"},
        ]
        return Response(types_bien)


class LocatairesView(APIView):
    """List locataires."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        profiles = (
            UserProfile.objects.filter(role="locataire")
            .select_related("user")
            .order_by("user__username")
        )
        data = [
            {
                "id": p.user.id,
                "username": p.user.username,
                "email": p.user.email,
                "telephone": p.telephone,
                "role": p.role,
                "is_verified": p.is_verified,
                "created_at": p.created_at,
            }
            for p in profiles
        ]
        return Response(data)


class ActeursView(APIView):
    """List acteurs (proprietaires, agents, agences, admin)."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        profiles = (
            UserProfile.objects.filter(role__in=ACTOR_ROLES)
            .select_related("user")
            .order_by("user__username")
        )
        data = [
            {
                "id": p.user.id,
                "username": p.user.username,
                "email": p.user.email,
                "telephone": p.telephone,
                "role": p.role,
                "is_verified": p.is_verified,
                "created_at": p.created_at,
            }
            for p in profiles
        ]
        return Response(data)
