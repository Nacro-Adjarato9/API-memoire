from django.db.models import Q
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Image
from .serializers import ImageSerializer, ImageCreateSerializer


class ImageViewSet(viewsets.ModelViewSet):
    queryset = Image.objects.all().order_by('-created_at')

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'upload_multiple']:
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def get_serializer_class(self):
        if self.action in ['create', 'upload_multiple']:
            return ImageCreateSerializer
        return ImageSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        bien_id = self.request.query_params.get('bien_id')

        if bien_id:
            queryset = queryset.filter(bien_id=bien_id)

        return queryset

    @action(detail=False, methods=['get'])
    def mes_images(self, request):
        """Return images for properties managed by the current user."""
        if not request.user.is_authenticated:
            return Response([])
        images = self.get_queryset().filter(
            Q(bien__proprietaire=request.user) | Q(bien__agence=request.user)
        )
        serializer = ImageSerializer(images, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def upload_multiple(self, request):
        """Upload plusieurs images (fichiers, base64, ou urls) pour un même bien."""
        bien_id = request.data.get('bien_id')
        if not bien_id:
            return Response({'detail': 'bien_id required'}, status=400)

        from biens.models import Bien
        try:
            bien = Bien.objects.get(
                Q(id=bien_id) & (Q(proprietaire=request.user) | Q(agence=request.user))
            )
        except Bien.DoesNotExist:
            return Response({'detail': 'Property not found or not authorized'}, status=404)

        # Trois formats acceptés : fichiers multipart (getlist("fichiers")),
        # une liste de chaînes base64 ("images_base64"), ou une liste d'URLs ("urls").
        fichiers = request.FILES.getlist('fichiers')
        images_base64 = request.data.get('images_base64', [])
        urls = request.data.get('urls', [])

        if not fichiers and not images_base64 and not urls:
            return Response({'detail': 'fichiers, images_base64 ou urls requis'}, status=400)

        images_created = []
        for fichier in fichiers:
            image = Image.objects.create(bien=bien, fichier=fichier)
            images_created.append(image)
        for b64 in images_base64:
            serializer = ImageCreateSerializer(
                data={'bien': bien.id, 'fichier_base64': b64},
                context={'request': request},
            )
            serializer.is_valid(raise_exception=True)
            images_created.append(serializer.save())
        for url in urls:
            images_created.append(Image.objects.create(bien=bien, url=url))

        return Response({
            'message': f'{len(images_created)} images uploaded',
            'images': ImageSerializer(images_created, many=True, context={'request': request}).data,
        })
