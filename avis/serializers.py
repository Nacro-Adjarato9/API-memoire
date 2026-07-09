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
        fields = ('id', 'bien', 'note', 'commentaire', 'created_at')
        read_only_fields = ('id', 'created_at')

    def validate_bien(self, bien):
        user = self.context['request'].user
        if Avis.objects.filter(utilisateur=user, bien=bien).exists():
            raise serializers.ValidationError("Vous avez déjà laissé un avis pour ce bien.")
        return bien

    def create(self, validated_data):
        validated_data['utilisateur'] = self.context['request'].user
        return super().create(validated_data)
