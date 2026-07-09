from rest_framework import permissions, viewsets

from .models import Agence
from .serializers import AgenceSerializer


class AgenceViewSet(viewsets.ModelViewSet):
    queryset = Agence.objects.all().order_by('-created_at')
    serializer_class = AgenceSerializer
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        serializer.save(proprietaire=self.request.user)
