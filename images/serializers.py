import base64
import uuid

from django.core.files.base import ContentFile
from rest_framework import serializers

from .models import Image


class ImageSerializer(serializers.ModelSerializer):
    bien_titre = serializers.ReadOnlyField(source='bien.titre')
    url = serializers.SerializerMethodField()

    class Meta:
        model = Image
        fields = ('id', 'bien', 'bien_titre', 'url', 'fichier', 'created_at')
        read_only_fields = ('id', 'created_at')

    def get_url(self, obj):
        if obj.fichier:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.fichier.url) if request else obj.fichier.url
        return obj.url


class ImageCreateSerializer(serializers.ModelSerializer):
    url = serializers.CharField(required=False, allow_blank=True)
    fichier = serializers.ImageField(required=False, allow_null=True)
    fichier_base64 = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = Image
        fields = ('bien', 'url', 'fichier', 'fichier_base64')

    def _decode_base64_image(self, data):
        if not data:
            return None
        if ";base64," in data:
            header, encoded = data.split(";base64,", 1)
            mime = header.split(":")[-1] if ":" in header else "image/jpeg"
        else:
            encoded = data
            mime = "image/jpeg"
        try:
            decoded = base64.b64decode(encoded)
        except Exception:
            raise serializers.ValidationError({"fichier_base64": "Image base64 invalide."})
        ext = "png" if "png" in mime else "jpg"
        return ContentFile(decoded, name=f"image-{uuid.uuid4().hex}.{ext}")

    def validate(self, data):
        if not data.get('fichier') and not data.get('fichier_base64') and not data.get('url'):
            raise serializers.ValidationError("Fournissez un fichier, une image en base64, ou une URL.")
        return data

    def create(self, validated_data):
        fichier_base64 = validated_data.pop('fichier_base64', None)
        if fichier_base64 and not validated_data.get('fichier'):
            validated_data['fichier'] = self._decode_base64_image(fichier_base64)

        bien = validated_data['bien']
        user = self.context['request'].user
        if bien.proprietaire != user and bien.agence != user:
            raise serializers.ValidationError("Vous n'êtes pas autorisé à ajouter des images à ce bien.")
        return super().create(validated_data)
