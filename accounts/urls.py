from django.contrib.auth import views as auth_views
from django.urls import path

from . import views
from .forms import LoginFormWithInactiveMessage

app_name = "accounts"

urlpatterns = [
    path("inscription/", views.signup, name="signup"),
    path("inscription/email-envoye/", views.signup_email_sent, name="signup_email_sent"),
    path("verifier-email/", views.verify_email, name="verify_email"),
    path(
        "connexion/",
        auth_views.LoginView.as_view(
            template_name="accounts/login.html",
            form_class=LoginFormWithInactiveMessage,
        ),
        name="login",
    ),
    path(
        "connexion-admin/",
        auth_views.LoginView.as_view(template_name="accounts/admin_login.html"),
        name="admin_login",
    ),
    path("deconnexion/", auth_views.LogoutView.as_view(), name="logout"),
    path("profil/", views.profile, name="profile"),
    path("commandes/", views.order_history, name="order_history"),
    path("reservations/", views.service_reservations, name="service_reservations"),
    path(
        "reservations/<int:pk>/annuler/",
        views.cancel_service_reservation,
        name="cancel_service_reservation",
    ),
    path("admin-panel/", views.admin_dashboard, name="admin_dashboard"),
    path("admin-panel/users/<int:user_id>/role/", views.set_user_role, name="set_user_role"),
    path(
        "admin-panel/vendors/<int:vendor_id>/details/",
        views.view_vendor_details,
        name="view_vendor_details",
    ),
    path(
        "admin-panel/providers/<int:provider_id>/details/",
        views.view_service_provider_details,
        name="view_service_provider_details",
    ),
    path(
        "admin-panel/vendors/<int:vendor_id>/<str:action>/",
        views.moderate_vendor,
        name="moderate_vendor",
    ),
    path(
        "admin-panel/providers/<int:provider_id>/<str:action>/",
        views.moderate_service_provider,
        name="moderate_service_provider",
    ),
]
