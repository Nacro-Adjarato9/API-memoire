import base64
import uuid

from django.core.files.base import ContentFile
from rest_framework import serializers

from .models import Bien, Document


class BienSerializer(serializers.ModelSerializer):
    proprietaire = serializers.ReadOnlyField(source='proprietaire.username')
    agence = serializers.ReadOnlyField(source='agence.username')

    class Meta:
        model = Bien
        fields = '__all__'


class BienCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bien
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

    def create(self, validated_data):
        user = self.context['request'].user
        role = getattr(getattr(user, 'profile', None), 'role', None)
        if role in ('agent', 'agence'):
            validated_data['agence'] = user
        else:
            validated_data['proprietaire'] = user
        return super().create(validated_data)


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
