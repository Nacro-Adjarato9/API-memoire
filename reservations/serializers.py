from rest_framework import serializers

from .models import Reservation


class ReservationSerializer(serializers.ModelSerializer):
    utilisateur = serializers.ReadOnlyField(source='utilisateur.username')
    bien_titre = serializers.ReadOnlyField(source='bien.titre')
    bien_prix = serializers.ReadOnlyField(source='bien.prix')
    bien_ville = serializers.ReadOnlyField(source='bien.ville')
    client_nom = serializers.SerializerMethodField()
    client_telephone = serializers.SerializerMethodField()

    class Meta:
        model = Reservation
        fields = (
            'id', 'utilisateur', 'bien', 'bien_titre', 'bien_prix', 'bien_ville',
            'client_nom', 'client_telephone', 'date', 'message', 'status', 'created_at',
        )
        read_only_fields = ('id', 'utilisateur', 'status', 'created_at')

    def get_client_nom(self, obj):
        user = obj.utilisateur
        full_name = f"{user.first_name} {user.last_name}".strip()
        return full_name or user.username

    def get_client_telephone(self, obj):
        try:
            return obj.utilisateur.profile.telephone or ""
        except Exception:
            return ""


class ReservationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reservation
        fields = ('id', 'bien', 'date', 'message', 'status', 'created_at')
        read_only_fields = ('id', 'status', 'created_at')

    def create(self, validated_data):
        validated_data['utilisateur'] = self.context['request'].user
        return super().create(validated_data)


class ReservationStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reservation
        fields = ('status',)
