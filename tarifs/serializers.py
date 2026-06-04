from rest_framework import serializers
from .models import Tarif, Abonnement


class TarifSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tarif
        fields = '__all__'


class AbonnementSerializer(serializers.ModelSerializer):
    utilisateur = serializers.ReadOnlyField(source='utilisateur.username')
    tarif_nom = serializers.ReadOnlyField(source='tarif.nom')
    tarif_prix = serializers.ReadOnlyField(source='tarif.prix')

    class Meta:
        model = Abonnement
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

    def create(self, validated_data):
        validated_data['utilisateur'] = self.context['request'].user
        return super().create(validated_data)


class AbonnementCreateSerializer(serializers.ModelSerializer):
    duree_mois = serializers.IntegerField(write_only=True, required=False, default=1)

    class Meta:
        model = Abonnement
        fields = ['tarif', 'duree_mois', 'auto_renew']
        read_only_fields = ('created_at', 'updated_at')

    def create(self, validated_data):
        duree_mois = validated_data.pop('duree_mois', 1)
        validated_data['utilisateur'] = self.context['request'].user
        
        # Calculer date_fin basée sur le tarif
        from datetime import timedelta
        from django.utils import timezone
        
        tarif = validated_data['tarif']
        date_debut = timezone.now()
        
        if tarif.duree == 'mensuel':
            date_fin = date_debut + timedelta(days=30 * duree_mois)
        elif tarif.duree == 'trimestriel':
            date_fin = date_debut + timedelta(days=90 * duree_mois)
        elif tarif.duree == 'semestriel':
            date_fin = date_debut + timedelta(days=180 * duree_mois)
        elif tarif.duree == 'annuel':
            date_fin = date_debut + timedelta(days=365 * duree_mois)
        else:
            date_fin = date_debut + timedelta(days=30 * duree_mois)
        
        validated_data['date_fin'] = date_fin
        return super().create(validated_data)