from rest_framework import serializers

from .models import Avis


class AvisSerializer(serializers.ModelSerializer):
    utilisateur = serializers.ReadOnlyField(source='utilisateur.username')
    bien_titre = serializers.ReadOnlyField(source='bien.titre')

    class Meta:
        model = Avis
        fields = ('id', 'utilisateur', 'bien', 'bien_titre', 'note', 'commentaire', 'created_at')
        read_only_fields = ('id', 'utilisateur', 'created_at')


class AvisCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Avis
        fields = ('bien', 'note', 'commentaire')

    def create(self, validated_data):
        validated_data['utilisateur'] = self.context['request'].user
        return super().create(validated_data)
