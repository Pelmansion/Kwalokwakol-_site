from django.urls import path

from . import views

app_name = "messaging"

urlpatterns = [
    path("vendor/<int:vendor_id>/", views.contact_vendor, name="contact_vendor"),
    path("vendeur/", views.vendor_inbox, name="vendor_inbox"),
    path("vendeur/thread/<int:thread_id>/", views.vendor_thread, name="vendor_thread"),
]
