from django.urls import path

from . import views

app_name = "payments"

urlpatterns = [
    path("sandbox/<int:payment_id>/", views.payment_sandbox, name="payment_sandbox"),
]
