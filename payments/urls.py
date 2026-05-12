from django.urls import path

from . import views

app_name = "payments"

urlpatterns = [
    path("sandbox/<int:payment_id>/", views.payment_sandbox, name="payment_sandbox"),
    path("genius/retour/<int:payment_id>/", views.genius_return, name="genius_return"),
    path("genius/echec/<int:payment_id>/", views.genius_error, name="genius_error"),
    path("genius/webhook/", views.genius_webhook, name="genius_webhook"),
]
