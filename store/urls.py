from django.urls import path

from . import views

app_name = "store"

urlpatterns = [
    path("", views.home, name="home"),
    path("produits/", views.product_list, name="product_list"),
    path("produit/<slug:slug>/", views.product_detail, name="product_detail"),
    path("favoris/", views.favorites_list, name="favorites"),
    path("favoris/toggle/<int:product_id>/", views.toggle_favorite, name="toggle_favorite"),
    path("service/demande/<int:product_id>/", views.request_service, name="request_service"),
    path("categorie/<slug:slug>/", views.category_detail, name="category_detail"),
    path("vendeurs/", views.vendor_list, name="vendor_list"),
    path("vendeur/<slug:slug>/", views.vendor_detail, name="vendor_detail"),
    path("prestataires/", views.service_provider_list, name="service_provider_list"),
    path("prestataire/<slug:slug>/", views.service_provider_detail, name="service_provider_detail"),
    path("panier/", views.cart_detail, name="cart_detail"),
    path("panier/ajouter/<int:product_id>/", views.add_to_cart, name="add_to_cart"),
    path("panier/maj/<int:product_id>/", views.update_cart, name="update_cart"),
    path("panier/supprimer/<int:product_id>/", views.remove_from_cart, name="remove_from_cart"),
    path("commande/", views.checkout, name="checkout"),
    path("commande/succes/<int:order_id>/", views.order_success, name="order_success"),
]
