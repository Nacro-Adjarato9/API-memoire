from django.db.models import Q
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Image
from .serializers import ImageSerializer, ImageCreateSerializer


class ImageViewSet(viewsets.ModelViewSet):
    queryset = Image.objects.all().order_by('-created_at')
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        if self.action == 'create':
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
        images = self.get_queryset().filter(
            Q(bien__proprietaire=request.user) | Q(bien__agence=request.user)
        )
        serializer = self.get_serializer(images, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def upload_multiple(self, request):
        """Upload multiple image urls for one property."""
        bien_id = request.data.get('bien_id')
        urls = request.data.get('urls', [])

        if not bien_id:
            return Response({'detail': 'bien_id required'}, status=400)
        if not urls:
            return Response({'detail': 'urls required'}, status=400)

        from biens.models import Bien
        try:
            bien = Bien.objects.get(
                Q(id=bien_id) & (Q(proprietaire=request.user) | Q(agence=request.user))
            )
        except Bien.DoesNotExist:
            return Response({'detail': 'Property not found or not authorized'}, status=404)

        images_created = []
        for url in urls:
            image = Image.objects.create(bien=bien, url=url)
            images_created.append(ImageSerializer(image).data)

        return Response({
            'message': f'{len(images_created)} images uploaded',
            'images': images_created
        })
