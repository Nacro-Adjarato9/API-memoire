from rest_framework import serializers

from .models import Agence


class AgenceSerializer(serializers.ModelSerializer):
    proprietaire = serializers.ReadOnlyField(source='proprietaire.username')

    class Meta:
        model = Agence
        fields = ('id', 'nom', 'adresse', 'proprietaire', 'telephone', 'created_at')
        read_only_fields = ('id', 'proprietaire', 'created_at')
