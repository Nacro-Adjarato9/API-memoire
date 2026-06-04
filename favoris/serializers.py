from rest_framework import serializers

from .models import Favori


class FavoriSerializer(serializers.ModelSerializer):
    utilisateur = serializers.ReadOnlyField(source='utilisateur.username')
    bien_titre = serializers.ReadOnlyField(source='bien.titre')
    bien_prix = serializers.ReadOnlyField(source='bien.prix')
    bien_ville = serializers.ReadOnlyField(source='bien.ville')
    bien_image = serializers.SerializerMethodField()

    class Meta:
        model = Favori
        fields = ('id', 'utilisateur', 'bien', 'bien_titre', 'bien_prix', 'bien_ville', 'bien_image', 'created_at')
        read_only_fields = ('id', 'utilisateur', 'created_at')

    def get_bien_image(self, obj):
        images = obj.bien.images.all()
        if images.exists():
            return images.first().url
        return None


class FavoriCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favori
        fields = ('bien',)

    def create(self, validated_data):
        validated_data['utilisateur'] = self.context['request'].user
        return super().create(validated_data)
