from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.files.base import ContentFile
from django.utils import timezone
from datetime import timedelta
import base64
import secrets
import uuid
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
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
from .token_generator import EmailVerificationTokenGenerator
from .emails import send_password_reset_email

User = get_user_model()


class LoginSerializer(TokenObtainPairSerializer):
    """
    Accepte indifféremment email ou username pour le login.
    Vérifie aussi que l'email a bien été validé avant de délivrer le JWT.
    """
    username = serializers.CharField(required=False, allow_blank=True)
    email = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        identifier = attrs.get('email') or attrs.get('username') or attrs.get(self.username_field)
        if not identifier:
            raise serializers.ValidationError({
                'detail': "Email ou nom d'utilisateur requis."
            })

        candidates = list(User.objects.filter(email__iexact=identifier))
        if not candidates:
            candidates = list(User.objects.filter(username=identifier))
        if not candidates:
            raise serializers.ValidationError({
                'detail': 'Identifiants invalides.'
            })

        user = None
        for candidate in sorted(candidates, key=lambda item: item.id, reverse=True):
            if candidate.check_password(attrs.get('password')):
                user = candidate
                break

        if user is None:
            raise serializers.ValidationError({
                'detail': 'Identifiants invalides.'
            })

        if not hasattr(user, 'profile') or not user.profile.is_verified:
            raise serializers.ValidationError({
                'detail': 'Email non vérifié. Veuillez vérifier votre adresse email.'
            })

        attrs[self.username_field] = user.username
        attrs.pop('email', None)
        return super().validate(attrs)


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    user_type = serializers.CharField(write_only=True, required=True)
    role = serializers.CharField(write_only=True, required=False, allow_blank=True)
    nom = serializers.CharField(write_only=True, required=False, allow_blank=True)
    prenom = serializers.CharField(write_only=True, required=False, allow_blank=True)
    phone = serializers.CharField(write_only=True, required=False, allow_blank=True)
    first_name = serializers.CharField(write_only=True, required=False, allow_blank=True)
    last_name = serializers.CharField(write_only=True, required=False, allow_blank=True)
    motdepasse = serializers.CharField(write_only=True, required=False, allow_blank=True)
    confirmation = serializers.CharField(write_only=True, required=False, allow_blank=True)
    type = serializers.CharField(write_only=True, required=False, allow_blank=True)
    adresse = serializers.CharField(write_only=True, required=False, allow_blank=True)
    ville = serializers.CharField(write_only=True, required=False, allow_blank=True)
    nomAgence = serializers.CharField(write_only=True, required=False, allow_blank=True)
    rccm = serializers.CharField(write_only=True, required=False, allow_blank=True)
    ncc = serializers.CharField(write_only=True, required=False, allow_blank=True)
    description = serializers.CharField(write_only=True, required=False, allow_blank=True)
    siteWeb = serializers.CharField(write_only=True, required=False, allow_blank=True)
    logoPreview = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = (
            'id', 'email', 'password', 'password2', 'motdepasse', 'confirmation',
            'nom', 'prenom', 'first_name', 'last_name', 'phone', 'user_type', 'role',
            'type', 'adresse', 'ville', 'nomAgence', 'rccm', 'ncc', 'description',
            'siteWeb', 'logoPreview'
        )

    def validate(self, data):
        # Password and role are required
        if not data.get('password') and not data.get('motdepasse'):
            raise serializers.ValidationError({"password": "Le mot de passe est requis."})
        if not data.get('password2') and not data.get('confirmation'):
            raise serializers.ValidationError({"password2": "La confirmation est requise."})
        if not data.get('user_type') and not data.get('role'):
            raise serializers.ValidationError({"user_type": "Le rôle est requis."})
        if data.get('role') and not data.get('user_type'):
            data['user_type'] = data['role']
        if data.get('motdepasse') and not data.get('password'):
            data['password'] = data['motdepasse']
        if data.get('confirmation') and not data.get('password2'):
            data['password2'] = data['confirmation']
        if data.get('nom') and not data.get('last_name'):
            data['last_name'] = data['nom']
        if data.get('prenom') and not data.get('first_name'):
            data['first_name'] = data['prenom']
        if data['password'] != data['password2']:
            raise serializers.ValidationError({"password": "Les mots de passe ne correspondent pas."})
        # 'admin' est exclu volontairement : ce rôle ne doit jamais être auto-attribuable à l'inscription.
        if data.get('user_type') not in ['locataire', 'proprietaire', 'agent', 'agence']:
            raise serializers.ValidationError({"user_type": "Type d'utilisateur invalide."})
        # Email uniqueness check
        email = data.get('email')
        if email and User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError({'email': 'Cette adresse email est déjà utilisée.'})
        return data

    def create(self, validated_data):
        email = validated_data['email']
        password = validated_data.pop('password')
        validated_data.pop('password2')
        user_type = validated_data.pop('user_type')
        validated_data.pop('role', None)
        phone = validated_data.pop('phone', '')
        first_name = validated_data.pop('first_name', '')
        last_name = validated_data.pop('last_name', '')
        owner_type = validated_data.pop('type', '')
        adresse = validated_data.pop('adresse', '')
        ville = validated_data.pop('ville', '')
        nom_agence = validated_data.pop('nomAgence', '')
        rccm = validated_data.pop('rccm', '')
        ncc = validated_data.pop('ncc', '')
        description = validated_data.pop('description', '')
        site_web = validated_data.pop('siteWeb', '')
        logo_preview = validated_data.pop('logoPreview', '')
        validated_data.pop('nom', None)
        validated_data.pop('prenom', None)
        validated_data.pop('motdepasse', None)
        validated_data.pop('confirmation', None)
        
        # Générer username à partir de l'email
        username = email.split('@')[0]
        # Vérifier unicité du username
        counter = 1
        original_username = username
        while User.objects.filter(username=username).exists():
            username = f"{original_username}{counter}"
            counter += 1
        
        # Créer l'utilisateur avec create_user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )

        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.is_verified = False
        profile.role = user_type
        profile.telephone = phone
        profile.save()

        if user_type == 'proprietaire':
            owner_profile, _ = ProfilProprietaire.objects.get_or_create(
                user=user,
                defaults={
                    'nom': first_name or user.first_name or user.username,
                    'prenom': last_name or user.last_name or '',
                    'type_proprietaire': owner_type or 'particulier',
                    'telephone': phone,
                    'ville': ville or '',
                    'adresse_complete': adresse or '',
                },
            )
            owner_profile.nom = owner_profile.nom or first_name or user.first_name or user.username
            owner_profile.prenom = owner_profile.prenom or last_name or user.last_name or ''
            owner_profile.type_proprietaire = owner_type or owner_profile.type_proprietaire or 'particulier'
            owner_profile.telephone = phone or owner_profile.telephone
            owner_profile.ville = ville or owner_profile.ville
            owner_profile.adresse_complete = adresse or owner_profile.adresse_complete
            owner_profile.save()
        elif user_type in ('agent', 'agence'):
            agency_defaults = {
                'nom_agence': nom_agence or username,
                'logo': None,
                'description': description or '',
                'telephone': phone,
                'email': email,
                'site_web': site_web or '',
                'ville': ville or '',
                'adresse_complete': adresse or '',
                'numero_registre_commerce': rccm or '',
                'numero_contribuable': ncc or '',
            }
            if logo_preview:
                agency_defaults['logo'] = self._decode_base64_file(logo_preview, "logo")
            agency_profile, _ = ProfilAgence.objects.get_or_create(user=user, defaults=agency_defaults)
            agency_profile.nom_agence = nom_agence or agency_profile.nom_agence
            agency_profile.description = description or agency_profile.description
            agency_profile.telephone = phone or agency_profile.telephone
            agency_profile.email = email or agency_profile.email
            agency_profile.site_web = site_web or agency_profile.site_web
            agency_profile.ville = ville or agency_profile.ville
            agency_profile.adresse_complete = adresse or agency_profile.adresse_complete
            agency_profile.numero_registre_commerce = rccm or agency_profile.numero_registre_commerce
            agency_profile.numero_contribuable = ncc or agency_profile.numero_contribuable
            if logo_preview and not agency_profile.logo:
                agency_profile.logo = self._decode_base64_file(logo_preview, "logo")
            agency_profile.save()

        return user

    def _decode_base64_file(self, data, prefix="file"):
        if not data:
            return None
        if ";base64," in data:
            header, encoded = data.split(";base64,", 1)
            mime = header.split(":")[-1] if ":" in header else "application/octet-stream"
        else:
            encoded = data
            mime = "application/octet-stream"
        try:
            decoded = base64.b64decode(encoded)
        except Exception:
            raise serializers.ValidationError("Fichier base64 invalide.")
        ext = "png"
        if "jpeg" in mime or "jpg" in mime:
            ext = "jpg"
        name = f"{prefix}-{uuid.uuid4().hex}.{ext}"
        return ContentFile(decoded, name=name)


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = '__all__'
        read_only_fields = ('user', 'created_at')


class ProfilSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profil
        fields = '__all__'
        read_only_fields = ('utilisateur', 'created_at')


class VisiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Visite
        fields = '__all__'
        read_only_fields = ('utilisateur', 'created_at')


class PaiementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Paiement
        fields = '__all__'
        read_only_fields = ('utilisateur', 'statut', 'reference_transaction', 'payment_url', 'date', 'date_maj')


class InitierPaiementSerializer(serializers.Serializer):
    montant = serializers.IntegerField(min_value=100)
    methode = serializers.ChoiceField(choices=Paiement.METHODE_CHOICES)
    type_transaction = serializers.ChoiceField(choices=Transaction.TYPE_CHOICES)
    description = serializers.CharField(required=False, allow_blank=True, max_length=255)


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = '__all__'
        read_only_fields = ('date',)


class VilleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ville
        fields = '__all__'


class QuartierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quartier
        fields = '__all__'


class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = '__all__'
        read_only_fields = ('utilisateur', 'date')


class HistoriqueRechercheSerializer(serializers.ModelSerializer):
    class Meta:
        model = HistoriqueRecherche
        fields = '__all__'
        read_only_fields = ('utilisateur', 'date')


class SignalementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Signalement
        fields = '__all__'
        read_only_fields = ('utilisateur', 'date')


class ProfilProprietaireSerializer(serializers.ModelSerializer):
    type = serializers.CharField(source='type_proprietaire', required=False)
    adresse = serializers.CharField(source='adresse_complete', required=False, allow_blank=True)

    class Meta:
        model = ProfilProprietaire
        fields = '__all__'
        # kyc_* : uniquement modifiable par le flux Didit (kyc/views.py), jamais via un
        # PATCH classique du profil, sinon un utilisateur pourrait s'auto-approuver.
        read_only_fields = ('user', 'created_at', 'kyc_status', 'kyc_session_id', 'kyc_verified_at')

    def validate(self, attrs):
        if self.instance is None:
            user = self.context['request'].user
            attrs.setdefault('nom', user.first_name or user.username)
            attrs.setdefault('prenom', user.last_name or '')
        return attrs


class ProfilAgenceSerializer(serializers.ModelSerializer):
    nomAgence = serializers.CharField(source='nom_agence', required=False)
    rccm = serializers.CharField(source='numero_registre_commerce', required=False, allow_blank=True)
    ncc = serializers.CharField(source='numero_contribuable', required=False, allow_blank=True)
    adresse = serializers.CharField(source='adresse_complete', required=False, allow_blank=True)
    siteWeb = serializers.CharField(source='site_web', required=False, allow_blank=True)
    logoPreview = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = ProfilAgence
        fields = '__all__'
        # kyc_* : uniquement modifiable par le flux Didit (kyc/views.py), jamais via un
        # PATCH classique du profil, sinon un utilisateur pourrait s'auto-approuver.
        read_only_fields = ('user', 'created_at', 'kyc_status', 'kyc_session_id', 'kyc_verified_at')

    def _decode_base64_file(self, data, prefix="file"):
        if not data:
            return None
        if ";base64," in data:
            header, encoded = data.split(";base64,", 1)
            mime = header.split(":")[-1] if ":" in header else "application/octet-stream"
        else:
            encoded = data
            mime = "application/octet-stream"
        try:
            decoded = base64.b64decode(encoded)
        except Exception:
            raise serializers.ValidationError("Fichier base64 invalide.")
        ext = "png"
        if "jpeg" in mime or "jpg" in mime:
            ext = "jpg"
        name = f"{prefix}-{uuid.uuid4().hex}.{ext}"
        return ContentFile(decoded, name=name)

    def create(self, validated_data):
        logo_preview = validated_data.pop('logoPreview', None)
        if logo_preview and not validated_data.get('logo'):
            validated_data['logo'] = self._decode_base64_file(logo_preview, "logo")
        return super().create(validated_data)

    def update(self, instance, validated_data):
        logo_preview = validated_data.pop('logoPreview', None)
        if logo_preview and not validated_data.get('logo'):
            validated_data['logo'] = self._decode_base64_file(logo_preview, "logo")
        return super().update(instance, validated_data)


class ProfilProprietaireVerificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfilProprietaire
        fields = (
            'type_piece',
            'numero_piece',
            'photo_piece_recto',
            'photo_piece_verso',
            'selfie_verification',
        )
        extra_kwargs = {f: {'required': False} for f in fields}

    def validate(self, data):
        if not data:
            raise serializers.ValidationError("Au moins un document est requis.")
        return data


class ProfilAgenceVerificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfilAgence
        fields = (
            'numero_registre_commerce',
            'numero_contribuable',
            'document_legal',
        )
        extra_kwargs = {f: {'required': False} for f in fields}

    def validate(self, data):
        if not data:
            raise serializers.ValidationError("Au moins un document est requis.")
        return data


class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField(write_only=True)

    def validate_email(self, value):
        try:
            self.user = User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("Utilisateur non trouvé.")
        return value

    def create(self, validated_data):
        token = secrets.token_urlsafe(32)
        expiration = timezone.now() + timedelta(hours=24)
        reset = PasswordReset.objects.create(
            user=self.user,
            token=token,
            date_expiration=expiration,
        )
        send_password_reset_email(self.user, token)
        return reset


class PasswordResetConfirmSerializer(serializers.Serializer):
    email = serializers.EmailField(write_only=True)
    token = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs.get('password') != attrs.get('password2'):
            raise serializers.ValidationError({'password2': 'Les mots de passe ne correspondent pas.'})

        try:
            user = User.objects.get(email=attrs['email'])
        except User.DoesNotExist:
            raise serializers.ValidationError({'email': 'Utilisateur non trouvé.'})

        reset = (
            PasswordReset.objects
            .filter(user=user, token=attrs['token'])
            .order_by('-created_at')
            .first()
        )
        if not reset:
            raise serializers.ValidationError({'token': 'Token invalide.'})
        if reset.is_expired():
            raise serializers.ValidationError({'token': 'Token expiré.'})

        attrs['user'] = user
        attrs['reset'] = reset
        return attrs

    def save(self, **kwargs):
        user = self.validated_data['user']
        reset = self.validated_data['reset']
        user.set_password(self.validated_data['password'])
        user.save(update_fields=['password'])
        reset.delete()
        return user


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    new_password2 = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({'new_password2': 'Les mots de passe ne correspondent pas.'})
        return attrs


class SignalementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Signalement
        fields = '__all__'
        read_only_fields = ('utilisateur', 'date')


class VerifyEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()
    token = serializers.CharField(max_length=255)

    def validate(self, data):
        try:
            user = User.objects.get(email=data['email'])
        except User.DoesNotExist:
            raise serializers.ValidationError("Utilisateur non trouvé.")
        
        if not EmailVerificationTokenGenerator.verify_token(user, data['token']):
            raise serializers.ValidationError("Token invalide ou expiré.")
        
        data['user'] = user
        return data


class ResendVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()


class UserSerializer(serializers.ModelSerializer):
    is_verified = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'is_verified')

    def get_is_verified(self, obj):
        try:
            return obj.profile.is_verified
        except UserProfile.DoesNotExist:
            return False


class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')


class AgentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = UserProfile
        fields = '__all__'
