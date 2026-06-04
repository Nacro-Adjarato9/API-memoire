from rest_framework import serializers

from .models import Image


class ImageSerializer(serializers.ModelSerializer):
    bien_titre = serializers.ReadOnlyField(source='bien.titre')

    class Meta:
        model = Image
        fields = ('id', 'bien', 'bien_titre', 'url', 'created_at')
        read_only_fields = ('id', 'created_at')


class ImageCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ('bien', 'url')

    def create(self, validated_data):
        # Vérifier que l'utilisateur gère bien ce bien
        bien = validated_data['bien']
        user = self.context['request'].user
        if bien.proprietaire != user and bien.agence != user:
            raise serializers.ValidationError("Vous n'êtes pas autorisé à ajouter des images à ce bien.")
        return super().create(validated_data)
