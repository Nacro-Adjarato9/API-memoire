from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from rest_framework import generics, permissions, status, serializers, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import (
    UserProfile,
    ProfilProprietaire,
    ProfilAgence,
    PasswordReset,
    Signalement,
    Profil,
    Visite,
    Paiement,
    Transaction,
    Ville,
    Quartier,
    Ticket,
    HistoriqueRecherche,
)
from .serializers import (
    UserProfileSerializer,
    ProfilSerializer,
    VisiteSerializer,
    PaiementSerializer,
    TransactionSerializer,
    VilleSerializer,
    QuartierSerializer,
    TicketSerializer,
    HistoriqueRechercheSerializer,
    ProfilProprietaireSerializer,
    ProfilAgenceSerializer,
    ProfilProprietaireVerificationSerializer,
    ProfilAgenceVerificationSerializer,
    PasswordResetSerializer,
    PasswordResetConfirmSerializer,
    ChangePasswordSerializer,
    SignalementSerializer,
    RegisterSerializer,
    ResendVerificationSerializer,
    VerifyEmailSerializer,
    UserSerializer,
    ProfileUpdateSerializer,
    AgentSerializer,
)
from .token_generator import EmailVerificationTokenGenerator
from .emails import send_verification_email
from avis.serializers import AvisCreateSerializer

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer

    def perform_create(self, serializer):
        user = serializer.save()
        # Generate and send verification email
        token = EmailVerificationTokenGenerator.generate_token(user)
        try:
            send_verification_email(user, token)
        except Exception as e:
            print(f"Error sending email: {e}")


class UtilisateurViewSet(viewsets.ReadOnlyModelViewSet):
    """Affiche l'utilisateur connecté et son profil."""
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if not self.request.user or not self.request.user.is_authenticated:
            return UserProfile.objects.none()
        profile, _ = UserProfile.objects.get_or_create(user=self.request.user)
        return UserProfile.objects.filter(pk=profile.pk)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class ProfilViewSet(viewsets.ModelViewSet):
    queryset = Profil.objects.all()
    serializer_class = ProfilSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Profil.objects.all()
        return Profil.objects.filter(utilisateur=self.request.user)

    def perform_create(self, serializer):
        serializer.save(utilisateur=self.request.user)


class VisiteViewSet(viewsets.ModelViewSet):
    queryset = Visite.objects.all()
    serializer_class = VisiteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Visite.objects.filter(utilisateur=self.request.user)

    def perform_create(self, serializer):
        serializer.save(utilisateur=self.request.user)


class PaiementViewSet(viewsets.ModelViewSet):
    queryset = Paiement.objects.all()
    serializer_class = PaiementSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Paiement.objects.filter(utilisateur=self.request.user)

    def perform_create(self, serializer):
        serializer.save(utilisateur=self.request.user)


class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Transaction.objects.filter(paiement__utilisateur=self.request.user)


class VilleViewSet(viewsets.ModelViewSet):
    queryset = Ville.objects.all()
    serializer_class = VilleSerializer
    permission_classes = [permissions.AllowAny]


class QuartierViewSet(viewsets.ModelViewSet):
    queryset = Quartier.objects.all()
    serializer_class = QuartierSerializer
    permission_classes = [permissions.AllowAny]


class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Ticket.objects.filter(utilisateur=self.request.user)

    def perform_create(self, serializer):
        serializer.save(utilisateur=self.request.user)


class SignalementViewSet(viewsets.ModelViewSet):
    queryset = Signalement.objects.all()
    serializer_class = SignalementSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Signalement.objects.filter(utilisateur=self.request.user)

    def perform_create(self, serializer):
        serializer.save(utilisateur=self.request.user)


class HistoriqueRechercheViewSet(viewsets.ModelViewSet):
    queryset = HistoriqueRecherche.objects.all()
    serializer_class = HistoriqueRechercheSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return HistoriqueRecherche.objects.filter(utilisateur=self.request.user)

    def perform_create(self, serializer):
        serializer.save(utilisateur=self.request.user)


class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        if not user.check_password(serializer.validated_data['old_password']):
            return Response({'old_password': 'Ancien mot de passe invalide.'}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({'detail': 'Mot de passe mis à jour.'}, status=status.HTTP_200_OK)


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        identifier = data.get('email') or data.get('username')
        password = data.get('password')

        if not identifier:
            return Response({'detail': "Email ou nom d'utilisateur requis."}, status=status.HTTP_400_BAD_REQUEST)
        if not password:
            return Response({'detail': 'Mot de passe requis.'}, status=status.HTTP_400_BAD_REQUEST)

        candidates = list(User.objects.filter(email__iexact=identifier))
        if not candidates:
            candidates = list(User.objects.filter(username=identifier))
        if not candidates:
            return Response({'detail': 'Identifiants invalides.'}, status=status.HTTP_400_BAD_REQUEST)

        user = None
        for candidate in sorted(candidates, key=lambda item: item.id, reverse=True):
            if candidate.check_password(password):
                user = candidate
                break

        if user is None:
            return Response({'detail': 'Identifiants invalides.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            profile = user.profile
        except UserProfile.DoesNotExist:
            profile, _ = UserProfile.objects.get_or_create(
                user=user,
                defaults={
                    'role': 'locataire',
                    'is_verified': True,
                    'telephone': '',
                },
            )

        if not profile.is_verified:
            return Response(
                {'detail': 'Email non vérifié. Veuillez vérifier votre adresse email.'},
                status=status.HTTP_403_FORBIDDEN
            )

        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_200_OK)



class RefreshView(TokenRefreshView):
    permission_classes = [permissions.AllowAny]


class LogoutView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        return Response({'detail': 'Déconnexion réussie.'}, status=status.HTTP_200_OK)


class VerifyEmailView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = VerifyEmailSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            EmailVerificationTokenGenerator.mark_as_verified(user)
            return Response({'detail': 'Email vérifié avec succès.'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResendVerificationView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ResendVerificationSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user = User.objects.get(email=serializer.validated_data['email'])
                token = EmailVerificationTokenGenerator.generate_token(user)
                try:
                    send_verification_email(user, token)
                    return Response({'detail': 'Email de vérification envoyé.'}, status=status.HTTP_200_OK)
                except Exception as e:
                    return Response({'detail': f'Erreur lors de l\'envoi: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            except User.DoesNotExist:
                return Response({'detail': 'Utilisateur non trouvé.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        try:
            return self.request.user.profile
        except UserProfile.DoesNotExist:
            raise NotFound("Profil utilisateur introuvable.")


class ProfilProprietaireView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfilProprietaireSerializer
    permission_classes = [permissions.IsAuthenticated]

    def _ensure_proprietaire_role(self):
        role = getattr(getattr(self.request.user, 'profile', None), 'role', None)
        if role != 'proprietaire':
            return Response(
                {'detail': 'Cette route est réservée aux propriétaires.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return None

    def get_object(self):
        try:
            return self.request.user.profil_proprietaire
        except ProfilProprietaire.DoesNotExist:
            raise NotFound("Profil propriétaire introuvable.")

    def post(self, request):
        forbidden = self._ensure_proprietaire_role()
        if forbidden:
            return forbidden
        profile, _ = ProfilProprietaire.objects.get_or_create(
            user=request.user,
            defaults={
                'nom': request.user.first_name or request.user.username,
                'prenom': request.user.last_name or '',
            },
        )
        serializer = self.get_serializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request):
        forbidden = self._ensure_proprietaire_role()
        if forbidden:
            return forbidden
        profile, _ = ProfilProprietaire.objects.get_or_create(
            user=request.user,
            defaults={
                'nom': request.user.first_name or request.user.username,
                'prenom': request.user.last_name or '',
            },
        )
        serializer = self.get_serializer(profile, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request):
        forbidden = self._ensure_proprietaire_role()
        if forbidden:
            return forbidden
        profile, _ = ProfilProprietaire.objects.get_or_create(
            user=request.user,
            defaults={
                'nom': request.user.first_name or request.user.username,
                'prenom': request.user.last_name or '',
            },
        )
        serializer = self.get_serializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class ProfilAgenceView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfilAgenceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def _ensure_agence_role(self):
        role = getattr(getattr(self.request.user, 'profile', None), 'role', None)
        if role not in ('agent', 'agence'):
            return Response(
                {'detail': 'Cette route est réservée aux agents et agences.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return None

    def get_object(self):
        try:
            return self.request.user.profil_agence
        except ProfilAgence.DoesNotExist:
            raise NotFound("Profil agence introuvable.")

    def post(self, request):
        forbidden = self._ensure_agence_role()
        if forbidden:
            return forbidden
        profile, _ = ProfilAgence.objects.get_or_create(
            user=request.user,
            defaults={
                'nom_agence': request.data.get('nomAgence') or request.data.get('nom_agence') or request.user.username,
                'ville': request.data.get('ville') or '',
            },
        )
        serializer = self.get_serializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request):
        forbidden = self._ensure_agence_role()
        if forbidden:
            return forbidden
        profile, _ = ProfilAgence.objects.get_or_create(
            user=request.user,
            defaults={
                'nom_agence': request.data.get('nomAgence') or request.data.get('nom_agence') or request.user.username,
                'ville': request.data.get('ville') or '',
            },
        )
        serializer = self.get_serializer(profile, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request):
        forbidden = self._ensure_agence_role()
        if forbidden:
            return forbidden
        profile, _ = ProfilAgence.objects.get_or_create(
            user=request.user,
            defaults={
                'nom_agence': request.data.get('nomAgence') or request.data.get('nom_agence') or request.user.username,
                'ville': request.data.get('ville') or '',
            },
        )
        serializer = self.get_serializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class ProfilProprietaireVerificationView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            profile = request.user.profil_proprietaire
        except ProfilProprietaire.DoesNotExist:
            return Response({'detail': 'Profil propriétaire introuvable.'}, status=404)

        serializer = ProfilProprietaireVerificationSerializer(profile, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(statut_verification='en_attente', date_verification=None)
        return Response({'detail': 'Dossier envoyé. Vérification en cours.'}, status=200)


class ProfilAgenceVerificationView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            profile = request.user.profil_agence
        except ProfilAgence.DoesNotExist:
            return Response({'detail': 'Profil agence introuvable.'}, status=404)

        serializer = ProfilAgenceVerificationSerializer(profile, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(statut_verification='en_attente', date_verification=None)
        return Response({'detail': 'Dossier envoyé. Vérification en cours.'}, status=200)


class PasswordResetView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'detail': 'Email de réinitialisation envoyé.'}, status=status.HTTP_200_OK)


class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'detail': 'Mot de passe mis ? jour avec succ?s.'}, status=status.HTTP_200_OK)


class SignalementListCreateView(generics.ListCreateAPIView):
    serializer_class = SignalementSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Signalement.objects.filter(utilisateur=self.request.user)

    def perform_create(self, serializer):
        serializer.save(utilisateur=self.request.user)


class SignalementDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = SignalementSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Signalement.objects.filter(utilisateur=self.request.user)


class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        profile, _ = UserProfile.objects.get_or_create(
            user=request.user,
            defaults={
                'role': 'locataire',
                'is_verified': True,
                'telephone': '',
            },
        )
        serializer = UserProfileSerializer(profile)
        return Response(serializer.data)


class MeUpdateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request):
        return self._update_account(request)

    def patch(self, request):
        return self._update_account(request)

    def _update_account(self, request):
        profile, _ = UserProfile.objects.get_or_create(
            user=request.user,
            defaults={
                'role': 'locataire',
                'is_verified': True,
                'telephone': '',
            },
        )

        user_data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        if 'nom' in user_data and 'last_name' not in user_data:
            user_data['last_name'] = user_data.get('nom')
        if 'prenom' in user_data and 'first_name' not in user_data:
            user_data['first_name'] = user_data.get('prenom')

        user_serializer = ProfileUpdateSerializer(request.user, data=user_data, partial=True)
        user_serializer.is_valid(raise_exception=True)
        user_serializer.save()

        profile_serializer = UserProfileSerializer(profile, data=request.data, partial=True)
        profile_serializer.is_valid(raise_exception=True)
        profile_serializer.save()

        return Response({
            'user': UserSerializer(request.user).data,
            'profile': UserProfileSerializer(profile).data,
        })


class DeleteAccountView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request):
        user = request.user
        if isinstance(user, AnonymousUser):
            return Response({'detail': 'Utilisateur non trouvé.'}, status=status.HTTP_404_NOT_FOUND)
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class UtilisateursView(APIView):
    """Retourne les informations du compte connecté."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            profile = request.user.profile
        except UserProfile.DoesNotExist:
            return Response({'detail': 'Profil utilisateur introuvable.'}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            'user': UserSerializer(request.user).data,
            'profile': UserProfileSerializer(profile).data,
        })


class AgentsListView(generics.ListAPIView):
    """Lister tous les agents (utilisateurs avec rôle 'agence')"""
    permission_classes = [permissions.AllowAny]
    serializer_class = AgentSerializer

    def get_queryset(self):
        return UserProfile.objects.filter(role__in=['agent', 'agence']).select_related('user')


class AgentDetailView(generics.RetrieveAPIView):
    """Détails d'un agent"""
    permission_classes = [permissions.AllowAny]
    serializer_class = AgentSerializer

    def get_queryset(self):
        return UserProfile.objects.filter(role__in=['agent', 'agence']).select_related('user')


class AgentBiensView(generics.ListAPIView):
    """Lister les biens d'un agent"""
    permission_classes = [permissions.AllowAny]
    serializer_class = None  # Will be set dynamically

    def get_queryset(self):
        agent_id = self.kwargs['pk']
        from biens.models import Bien
        from biens.serializers import BienSerializer
        self.serializer_class = BienSerializer
        return Bien.objects.filter(agence_id=agent_id)


class AgentAvisView(generics.ListAPIView):
    """Lister les avis d'un agent"""
    permission_classes = [permissions.AllowAny]
    serializer_class = None  # Will be set dynamically

    def get_queryset(self):
        agent_id = self.kwargs['pk']
        from avis.models import Avis
        from avis.serializers import AvisSerializer
        self.serializer_class = AvisSerializer
        return Avis.objects.filter(bien__agence_id=agent_id).select_related('bien', 'utilisateur')


class LaisserAvisAgentView(generics.CreateAPIView):
    """Laisser un avis sur un agent"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AvisCreateSerializer

    def get_queryset(self):
        agent_id = self.kwargs['pk']
        from avis.models import Avis
        return Avis.objects.filter(bien__agence_id=agent_id)

    def perform_create(self, serializer):
        # Pour l'instant, on lie l'avis à un bien de l'agent
        # En production, il faudrait un modèle AvisAgent séparé
        agent_id = self.kwargs['pk']
        from biens.models import Bien
        # Prendre le premier bien de l'agent comme référence
        bien = Bien.objects.filter(agence_id=agent_id).first()
        if bien:
            serializer.save(utilisateur=self.request.user, bien=bien)
        else:
            raise serializers.ValidationError("Agent n'a pas de biens")

