from rest_framework import serializers

from .models import RecommendationIA


class RecommendationIASerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = RecommendationIA
        fields = '__all__'
        read_only_fields = ('user', 'created_at', 'updated_at')


class RecommendationIACreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecommendationIA
        fields = ('budget_min', 'budget_max', 'ville', 'type_bien', 'nombre_chambres_min', 'localisation')

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class RecommendationRequestSerializer(serializers.Serializer):
    texte = serializers.CharField(required=False, allow_blank=True)
    ville = serializers.CharField(required=False, allow_blank=True)
    quartier = serializers.CharField(required=False, allow_blank=True)
    commune = serializers.CharField(required=False, allow_blank=True)
    type_bien = serializers.CharField(required=False, allow_blank=True)
    budget_min = serializers.IntegerField(required=False, min_value=0)
    budget_max = serializers.IntegerField(required=False, min_value=0)
    nombre_chambres = serializers.IntegerField(required=False, min_value=0)
    nombre_salles_bain = serializers.IntegerField(required=False, min_value=0)
    superficie_min = serializers.DecimalField(required=False, max_digits=10, decimal_places=2)
    superficie_max = serializers.DecimalField(required=False, max_digits=10, decimal_places=2)
    meuble = serializers.BooleanField(required=False)
    parking = serializers.BooleanField(required=False)
    piscine = serializers.BooleanField(required=False)
    securite = serializers.BooleanField(required=False)
    proximite = serializers.CharField(required=False, allow_blank=True)
    statut = serializers.CharField(required=False, allow_blank=True)


class IARechercheSerializer(serializers.Serializer):
    texte = serializers.CharField(required=False, allow_blank=True)
    ville = serializers.CharField(required=False, allow_blank=True)
    quartier = serializers.CharField(required=False, allow_blank=True)
    commune = serializers.CharField(required=False, allow_blank=True)
    type_bien = serializers.CharField(required=False, allow_blank=True)
    budget_min = serializers.IntegerField(required=False)
    budget_max = serializers.IntegerField(required=False)
    nombre_chambres = serializers.IntegerField(required=False)
    nombre_salles_bain = serializers.IntegerField(required=False)
    superficie_min = serializers.DecimalField(required=False, max_digits=10, decimal_places=2)
    superficie_max = serializers.DecimalField(required=False, max_digits=10, decimal_places=2)
    meuble = serializers.BooleanField(required=False)
    parking = serializers.BooleanField(required=False)
    piscine = serializers.BooleanField(required=False)
    securite = serializers.BooleanField(required=False)
    proximite = serializers.CharField(required=False, allow_blank=True)
    statut = serializers.CharField(required=False, allow_blank=True)


class IAChatSerializer(serializers.Serializer):
    message = serializers.CharField()


class IAVerifyDocumentSerializer(serializers.Serializer):
    document_url = serializers.URLField(required=True)
    document_type = serializers.CharField(required=False, default='cni')
    utilisateur = serializers.CharField(required=False, allow_blank=True)
