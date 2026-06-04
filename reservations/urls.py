from django.urls import path

from .views import ReservationStatusUpdateView

urlpatterns = [
    path('reservations/<int:pk>/status/', ReservationStatusUpdateView.as_view(), name='reservation_status_update'),
]
