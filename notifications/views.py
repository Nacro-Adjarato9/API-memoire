from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Notification
from .serializers import NotificationSerializer, NotificationCreateSerializer


class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all().order_by('-created_at')
    permission_classes = [permissions.AllowAny]

    def get_serializer_class(self):
        if self.action == 'create':
            return NotificationCreateSerializer
        return NotificationSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if not user.is_authenticated:
            return queryset.none()
        is_read = self.request.query_params.get('is_read')

        if is_read is not None:
            if is_read.lower() == 'true':
                queryset = queryset.filter(is_read=True)
            elif is_read.lower() == 'false':
                queryset = queryset.filter(is_read=False)

        return queryset.filter(user=user)

    @action(detail=False, methods=['post'])
    def mark_all_as_read(self, request):
        """Mark every notification as read."""
        if not request.user.is_authenticated:
            return Response({'detail': '0 notifications marked as read'})
        notifications = self.get_queryset().filter(is_read=False)
        count = notifications.count()
        notifications.update(is_read=True)
        return Response({'detail': f'{count} notifications marked as read'})

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get unread notifications count."""
        if not request.user.is_authenticated:
            return Response({'unread_count': 0})
        count = self.get_queryset().filter(is_read=False).count()
        return Response({'unread_count': count})


class NotificationMarkAsReadView(APIView):
    permission_classes = [permissions.AllowAny]

    def put(self, request, pk):
        if not request.user.is_authenticated:
            return Response({'detail': 'Notification introuvable'}, status=status.HTTP_404_NOT_FOUND)
        try:
            notification = Notification.objects.get(pk=pk, user=request.user)
        except Notification.DoesNotExist:
            return Response({'detail': 'Notification introuvable'}, status=status.HTTP_404_NOT_FOUND)

        notification.is_read = True
        notification.save(update_fields=['is_read'])
        return Response(NotificationSerializer(notification).data)
