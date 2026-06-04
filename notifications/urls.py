from django.urls import path

from .views import NotificationMarkAsReadView

urlpatterns = [
    path('notifications/<int:pk>/read/', NotificationMarkAsReadView.as_view(), name='notification_mark_read'),
]
