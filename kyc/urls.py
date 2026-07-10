from django.urls import path

from . import views

urlpatterns = [
    path("start/", views.StartKycView.as_view(), name="kyc-start"),
    path("status/", views.KycStatusView.as_view(), name="kyc-status"),
    path("webhook/", views.didit_webhook, name="kyc-webhook"),
]
