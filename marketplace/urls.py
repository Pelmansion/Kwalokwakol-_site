from django.urls import path

from . import views

app_name = "marketplace"

urlpatterns = [
    path("categories/vitrine/", views.showcase_hub, name="showcase_hub"),
    path("categories/<int:category_id>/vitrine/", views.showcase_manage, name="showcase_manage"),
    path("inscription/", views.vendor_register, name="vendor_register"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("produit/ajouter/", views.add_product, name="add_product"),
    path("produit/<int:product_id>/modifier/", views.edit_product, name="edit_product"),
    path("produit/<int:product_id>/supprimer/", views.delete_product, name="delete_product"),
    path("profil/", views.vendor_profile, name="vendor_profile"),
    path("commande/<int:order_id>/statut/", views.update_order_status, name="update_order"),
    path("avis/<int:review_id>/reponse/", views.reply_review, name="reply_review"),
    path("paiements/", views.vendor_payments, name="vendor_payments"),
    path("parametres/", views.vendor_settings, name="vendor_settings"),
    path("demande/<int:request_id>/<str:action>/", views.update_service_request, name="update_service_request"),
    path("prestataire/inscription/", views.service_provider_register, name="service_provider_register"),
    path("prestataire/dashboard/", views.service_provider_dashboard, name="service_provider_dashboard"),
    path("prestataire/profil/", views.service_provider_profile, name="service_provider_profile"),
    path("prestataire/service/ajouter/", views.add_service, name="add_service"),
    path("prestataire/demandes/", views.service_requests_list, name="service_requests_list"),
]
