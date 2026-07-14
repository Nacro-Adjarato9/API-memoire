import base64
import uuid

from django.core.files.base import ContentFile
from rest_framework import serializers

from .models import Bien, Document


class BienSerializer(serializers.ModelSerializer):
    proprietaire = serializers.ReadOnlyField(source='proprietaire.username')
    agence = serializers.ReadOnlyField(source='agence.username')
    contact_id = serializers.SerializerMethodField()
    contact_nom = serializers.SerializerMethodField()
    contact_telephone = serializers.SerializerMethodField()
    contact_email = serializers.SerializerMethodField()
    # 'agence' au sens rôle métier (agence OU agent), pas seulement le champ agence du bien :
    # utilisé par le front pour afficher le bon badge ("Propriétaire" / "Agence immobilière").
    contact_role = serializers.SerializerMethodField()
    # 'images' est une relation inverse (Image.bien -> related_name='images') : ModelSerializer
    # avec fields='__all__' ne l'inclut jamais automatiquement, il faut la déclarer explicitement,
    # sinon le front n'a aucun moyen de savoir quelles photos sont liées à ce bien.
    # Le frontend utilise directement p.images[0] comme src d'une balise <img> : on renvoie
    # donc une liste de simples URLs (string), pas des objets Image.
    images = serializers.SerializerMethodField()

    class Meta:
        model = Bien
        fields = '__all__'

    def get_images(self, obj):
        request = self.context.get('request')
        urls = []
        for img in obj.images.all():
            if img.fichier:
                urls.append(request.build_absolute_uri(img.fichier.url) if request else img.fichier.url)
            elif img.url:
                urls.append(img.url)
        return urls

    def _contact_user(self, obj):
        return obj.agence or obj.proprietaire

    def get_contact_id(self, obj):
        user = self._contact_user(obj)
        return user.id if user else None

    def get_contact_nom(self, obj):
        user = self._contact_user(obj)
        if not user:
            return ""
        full_name = f"{user.first_name} {user.last_name}".strip()
        return full_name or user.username

    def get_contact_telephone(self, obj):
        user = self._contact_user(obj)
        if not user:
            return ""
        try:
            return user.profile.telephone or ""
        except Exception:
            return ""

    def get_contact_email(self, obj):
        user = self._contact_user(obj)
        return user.email if user else ""

    def get_contact_role(self, obj):
        if obj.agence:
            return "agence"
        if obj.proprietaire:
            return "proprietaire"
        return ""


class BienCreateSerializer(serializers.ModelSerializer):
    # FloatField plutôt que le DecimalField auto-généré : les coordonnées GPS envoyées
    # par le navigateur/la carte arrivent avec une précision flottante brute (ex:
    # 5.358600000123456), ce qui casse la validation "max_digits" de DRF avant même
    # l'arrondi. On accepte le float et on l'arrondit nous-mêmes dans validate().
    latitude = serializers.FloatField(required=False, allow_null=True)
    longitude = serializers.FloatField(required=False, allow_null=True)

    class Meta:
        model = Bien
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

    # Champs à choix où le front envoie parfois le libellé affiché ("Titre
    # Foncier (TF)") plutôt que le slug attendu par le modèle ("titre_foncier").
    # On construit un mapping libellé -> slug (insensible à la casse) pour
    # chacun, à partir des choices du modèle lui-même.
    _CHOICE_FIELDS = ('commune', 'type', 'titre_propriete')

    def to_internal_value(self, data):
        if isinstance(data, dict):
            data = dict(data)
            model_fields = {f.name: f for f in Bien._meta.get_fields()}
            for field_name in self._CHOICE_FIELDS:
                value = data.get(field_name)
                if not isinstance(value, str) or not value:
                    continue
                field = model_fields.get(field_name)
                choices = getattr(field, 'choices', None) or []
                valid_slugs = {slug for slug, _ in choices}
                if value in valid_slugs:
                    continue
                label_to_slug = {label.strip().lower(): slug for slug, label in choices}
                normalized = label_to_slug.get(value.strip().lower())
                if normalized is None and value.strip().lower() in valid_slugs:
                    normalized = value.strip().lower()
                if normalized is not None:
                    data[field_name] = normalized
        return super().to_internal_value(data)

    def validate(self, data):
        if data.get('latitude') is not None:
            data['latitude'] = round(data['latitude'], 6)
        if data.get('longitude') is not None:
            data['longitude'] = round(data['longitude'], 6)
        return data

    def create(self, validated_data):
        from ia.services import evaluate_bien_fraud

        user = self.context['request'].user
        role = getattr(getattr(user, 'profile', None), 'role', None)
        if role in ('agent', 'agence'):
            validated_data['agence'] = user
        else:
            validated_data['proprietaire'] = user
        bien = super().create(validated_data)

        resultat = evaluate_bien_fraud(bien)
        bien.score_suspicion = resultat['score_suspicion']
        bien.est_suspect = resultat['est_suspect']
        bien.raisons_suspicion = resultat['raisons']
        bien.save(update_fields=['score_suspicion', 'est_suspect', 'raisons_suspicion'])
        return bien


class DocumentSerializer(serializers.ModelSerializer):
    proprietaire = serializers.ReadOnlyField(source='proprietaire.username')
    agence = serializers.ReadOnlyField(source='agence.username')
    bien = serializers.ReadOnlyField(source='bien.titre')

    class Meta:
        model = Document
        fields = '__all__'


class DocumentCreateSerializer(serializers.ModelSerializer):
    titre = serializers.CharField(required=False, allow_blank=True)
    fichier = serializers.FileField(required=False, allow_null=True)
    fichier_base64 = serializers.CharField(write_only=True, required=False, allow_blank=True)
    fichier_name = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = Document
        fields = (
            'id', 'titre', 'type_document', 'fichier', 'fichier_base64', 'fichier_name',
            'proprietaire', 'agence', 'bien', 'statut_verification',
            'commentaires_verification', 'created_at'
        )
        read_only_fields = ('created_at',)

    def _decode_base64_file(self, data, filename_prefix="document"):
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
            raise serializers.ValidationError({"fichier_base64": "Fichier base64 invalide."})
        ext = "pdf"
        if "png" in mime:
            ext = "png"
        elif "jpeg" in mime or "jpg" in mime:
            ext = "jpg"
        elif "pdf" in mime:
            ext = "pdf"
        filename = f"{filename_prefix}-{uuid.uuid4().hex}.{ext}"
        return ContentFile(decoded, name=filename)

    def create(self, validated_data):
        fichier_base64 = validated_data.pop('fichier_base64', None)
        fichier_name = validated_data.pop('fichier_name', None)
        if fichier_base64 and not validated_data.get('fichier'):
            validated_data['fichier'] = self._decode_base64_file(fichier_base64, fichier_name or "document")
        if not validated_data.get('titre'):
            type_document = validated_data.get('type_document', 'autre')
            validated_data['titre'] = type_document.replace('_', ' ').title()
        user = self.context['request'].user
        role = getattr(getattr(user, 'profile', None), 'role', None)
        if role in ('agent', 'agence'):
            validated_data['agence'] = user
        else:
            validated_data['proprietaire'] = user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        fichier_base64 = validated_data.pop('fichier_base64', None)
        fichier_name = validated_data.pop('fichier_name', None)
        if fichier_base64 and not validated_data.get('fichier'):
            validated_data['fichier'] = self._decode_base64_file(fichier_base64, fichier_name or "document")
        if not validated_data.get('titre') and not instance.titre:
            type_document = validated_data.get('type_document', instance.type_document)
            validated_data['titre'] = type_document.replace('_', ' ').title()
        return super().update(instance, validated_data)
