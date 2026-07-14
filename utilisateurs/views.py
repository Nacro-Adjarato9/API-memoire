import threading

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone
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
    InitierPaiementSerializer,
)
from .services_paiement import (
    initier_paiement,
    verifier_paiement,
    generer_reference_transaction,
    CinetPayError,
)
from .token_generator import EmailVerificationTokenGenerator
from .emails import send_verification_email
from avis.serializers import AvisCreateSerializer
from ia.services import verify_document
from notifications.services import notify

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
        self._created_user = user

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        # Le front (upload de profil/documents juste après l'inscription) a besoin
        # d'un token immédiatement : l'email non vérifié ne doit bloquer que la
        # future reconnexion via /auth/login/, pas cette étape d'onboarding.
        refresh = RefreshToken.for_user(self._created_user)
        response.data['access'] = str(refresh.access_token)
        response.data['refresh'] = str(refresh)
        return response


class UtilisateurViewSet(viewsets.ReadOnlyModelViewSet):
    """Affiche l'utilisateur connecté et son profil."""
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.AllowAny]

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
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Profil.objects.none()
        if self.request.user.is_staff:
            return Profil.objects.all()
        return Profil.objects.filter(utilisateur=self.request.user)

    def perform_create(self, serializer):
        serializer.save(utilisateur=self.request.user)


class VisiteViewSet(viewsets.ModelViewSet):
    queryset = Visite.objects.all()
    serializer_class = VisiteSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Visite.objects.none()
        return Visite.objects.filter(utilisateur=self.request.user)

    def perform_create(self, serializer):
        serializer.save(utilisateur=self.request.user)


class PaiementViewSet(viewsets.ModelViewSet):
    queryset = Paiement.objects.all()
    serializer_class = PaiementSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Paiement.objects.none()
        return Paiement.objects.filter(utilisateur=self.request.user)

    def perform_create(self, serializer):
        serializer.save(utilisateur=self.request.user)


class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Transaction.objects.none()
        return Transaction.objects.filter(paiement__utilisateur=self.request.user)


class InitierPaiementView(APIView):
    """Démarre un paiement CinetPay (Mobile Money / carte) pour un abonnement ou une réservation."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = InitierPaiementSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        reference = generer_reference_transaction()
        paiement = Paiement.objects.create(
            utilisateur=request.user,
            montant=data["montant"],
            methode=data["methode"],
            statut="en_attente",
            reference_transaction=reference,
            description=data.get("description", ""),
        )
        Transaction.objects.create(paiement=paiement, type=data["type_transaction"], statut="en_attente")

        profile = getattr(request.user, "profile", None)
        try:
            resultat = initier_paiement(
                montant=data["montant"],
                description=data.get("description") or f"Paiement {data['type_transaction']} LogeCiv",
                reference_transaction=reference,
                client_nom=request.user.get_full_name() or request.user.username,
                client_telephone=getattr(profile, "telephone", ""),
                client_email=request.user.email,
            )
        except CinetPayError as exc:
            paiement.statut = "echec"
            paiement.save(update_fields=["statut", "date_maj"])
            paiement.transactions.update(statut="echec")
            return Response({"error": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

        paiement.payment_url = resultat["payment_url"]
        paiement.save(update_fields=["payment_url", "date_maj"])

        return Response(
            {
                "reference_transaction": reference,
                "payment_url": resultat["payment_url"],
                "paiement": PaiementSerializer(paiement).data,
            },
            status=status.HTTP_201_CREATED,
        )


class CinetPayWebhookView(APIView):
    """Endpoint appelé par CinetPay après paiement. Ne fait jamais confiance au body reçu :
    revérifie systématiquement le statut auprès de l'API CinetPay avant de mettre à jour la base."""

    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        reference = request.data.get("cpm_trans_id") or request.data.get("transaction_id")
        if not reference:
            return Response({"error": "transaction_id manquant"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            paiement = Paiement.objects.get(reference_transaction=reference)
        except Paiement.DoesNotExist:
            return Response({"error": "Transaction inconnue"}, status=status.HTTP_404_NOT_FOUND)

        try:
            statut, _raw = verifier_paiement(reference)
        except CinetPayError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

        if statut != paiement.statut:
            paiement.statut = statut
            paiement.save(update_fields=["statut", "date_maj"])
            paiement.transactions.update(statut=statut)

        return Response({"reference_transaction": reference, "statut": statut})


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
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Ticket.objects.none()
        return Ticket.objects.filter(utilisateur=self.request.user)

    def perform_create(self, serializer):
        serializer.save(utilisateur=self.request.user)


class SignalementViewSet(viewsets.ModelViewSet):
    queryset = Signalement.objects.all()
    serializer_class = SignalementSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Signalement.objects.none()
        return Signalement.objects.filter(utilisateur=self.request.user)

    def perform_create(self, serializer):
        serializer.save(utilisateur=self.request.user)


class HistoriqueRechercheViewSet(viewsets.ModelViewSet):
    queryset = HistoriqueRecherche.objects.all()
    serializer_class = HistoriqueRechercheSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return HistoriqueRecherche.objects.none()
        return HistoriqueRecherche.objects.filter(utilisateur=self.request.user)

    def perform_create(self, serializer):
        serializer.save(utilisateur=self.request.user)


class ChangePasswordView(APIView):
    permission_classes = [permissions.AllowAny]

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
    permission_classes = [permissions.AllowAny]

    def get_object(self):
        if not self.request.user.is_authenticated:
            raise NotFound("Profil utilisateur introuvable.")
        try:
            return self.request.user.profile
        except UserProfile.DoesNotExist:
            raise NotFound("Profil utilisateur introuvable.")


class ProfilProprietaireView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfilProprietaireSerializer
    permission_classes = [permissions.AllowAny]

    def _ensure_proprietaire_role(self):
        role = getattr(getattr(self.request.user, 'profile', None), 'role', None)
        if role != 'proprietaire':
            return Response(
                {'detail': 'Cette route est réservée aux propriétaires.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return None

    def get_object(self):
        if not self.request.user.is_authenticated:
            raise NotFound("Profil propriétaire introuvable.")
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
        # partial=True : le front (ex. étape d'inscription) n'envoie que les
        # champs modifiés, pas la fiche complète — un PUT strict forcerait à
        # renvoyer nom/prenom à chaque appel alors qu'ils ont déjà une valeur.
        serializer = self.get_serializer(profile, data=request.data, partial=True)
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
    permission_classes = [permissions.AllowAny]

    def _ensure_agence_role(self):
        role = getattr(getattr(self.request.user, 'profile', None), 'role', None)
        if role not in ('agent', 'agence'):
            return Response(
                {'detail': 'Cette route est réservée aux agents et agences.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return None

    def get_object(self):
        if not self.request.user.is_authenticated:
            raise NotFound("Profil agence introuvable.")
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
        serializer = self.get_serializer(profile, data=request.data, partial=True)
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


# Le front envoie les documents sous des clés "métier" (cni_recto, rccm_doc, ...)
# qui ne correspondent pas aux noms de champs du modèle : on les remappe ici.
_PROPRIETAIRE_DOC_ALIASES = {
    'cni_recto': 'photo_piece_recto',
    'cni_verso': 'photo_piece_verso',
    'selfie_cni': 'selfie_verification',
}
_AGENCE_DOC_ALIASES = {
    # Un seul champ fichier existe côté modèle (document_legal) : on prend le
    # premier document légal fourni, par ordre de priorité.
    'rccm_doc': 'document_legal',
    'ncc_doc': 'document_legal',
    'cni_responsable': 'document_legal',
    'logo_agence': 'logo',
}


def _remap_document_keys(data, aliases):
    remapped = data.copy()
    for source_key, target_key in aliases.items():
        if source_key in data and target_key not in remapped:
            remapped[target_key] = data[source_key]
    return remapped


def _run_ia_document_check(profile, document_type, file_field):
    """Analyse IA : ne doit jamais bloquer la réponse HTTP ni laisser le dossier
    coincé en 'en_attente' indéfiniment. Le résultat est appliqué en base dès
    qu'il est prêt ; l'utilisateur peut continuer (vérif email, connexion)
    sans attendre."""
    if not file_field:
        return
    try:
        result = verify_document(document_type, file_field.url)
    except Exception:
        return

    verdict = (result.get('verdict') or '').lower()
    profile.statut_verification = 'valide' if 'valide' in verdict else 'en_attente'
    profile.date_verification = timezone.now()
    profile.save(update_fields=['statut_verification', 'date_verification'])

    if profile.statut_verification == 'valide':
        notify(profile.user, "Vos documents ont été vérifiés et validés.", type='document')
    else:
        notify(profile.user, "Vos documents sont en cours de vérification manuelle.", type='document')


def _run_ia_document_check_async(profile, document_type, file_field):
    thread = threading.Thread(
        target=_run_ia_document_check,
        args=(profile, document_type, file_field),
        daemon=True,
    )
    thread.start()


class ProfilProprietaireVerificationView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        try:
            profile = request.user.profil_proprietaire
        except ProfilProprietaire.DoesNotExist:
            return Response({'detail': 'Profil propriétaire introuvable.'}, status=404)

        data = _remap_document_keys(request.data, _PROPRIETAIRE_DOC_ALIASES)
        serializer = ProfilProprietaireVerificationSerializer(profile, data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save(statut_verification='en_attente', date_verification=None)

        _run_ia_document_check_async(profile, profile.type_piece or 'cni', profile.photo_piece_recto)

        return Response(
            {'detail': 'Dossier envoyé. Analyse IA en cours en arrière-plan.', 'statut_verification': profile.statut_verification},
            status=200,
        )


class ProfilAgenceVerificationView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        try:
            profile = request.user.profil_agence
        except ProfilAgence.DoesNotExist:
            return Response({'detail': 'Profil agence introuvable.'}, status=404)

        data = _remap_document_keys(request.data, _AGENCE_DOC_ALIASES)
        serializer = ProfilAgenceVerificationSerializer(profile, data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save(statut_verification='en_attente', date_verification=None)

        _run_ia_document_check_async(profile, 'rccm_doc', profile.document_legal)

        return Response(
            {'detail': 'Dossier envoyé. Analyse IA en cours en arrière-plan.', 'statut_verification': profile.statut_verification},
            status=200,
        )


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
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Signalement.objects.none()
        return Signalement.objects.filter(utilisateur=self.request.user)

    def perform_create(self, serializer):
        serializer.save(utilisateur=self.request.user)


class SignalementDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = SignalementSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Signalement.objects.none()
        return Signalement.objects.filter(utilisateur=self.request.user)


class MeView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        if not request.user.is_authenticated:
            return Response({'detail': 'Profil utilisateur introuvable.'}, status=status.HTTP_404_NOT_FOUND)
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
    permission_classes = [permissions.AllowAny]

    def put(self, request):
        return self._update_account(request)

    def patch(self, request):
        return self._update_account(request)

    def _update_account(self, request):
        if not request.user.is_authenticated:
            return Response({'detail': 'Utilisateur non trouvé.'}, status=status.HTTP_404_NOT_FOUND)
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
    permission_classes = [permissions.AllowAny]

    def delete(self, request):
        user = request.user
        if not user.is_authenticated:
            return Response({'detail': 'Utilisateur non trouvé.'}, status=status.HTTP_404_NOT_FOUND)
        if isinstance(user, AnonymousUser):
            return Response({'detail': 'Utilisateur non trouvé.'}, status=status.HTTP_404_NOT_FOUND)
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class UtilisateursView(APIView):
    """Retourne les informations du compte connecté."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        if not request.user.is_authenticated:
            return Response({'detail': 'Profil utilisateur introuvable.'}, status=status.HTTP_404_NOT_FOUND)
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
    permission_classes = [permissions.AllowAny]
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
