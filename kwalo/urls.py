"""
URL configuration for kwalo project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.generic import TemplateView
from django.views.static import serve

urlpatterns = [
    path('admin/', admin.site.urls),
    path("vendeur/", include("marketplace.urls")),
    path("compte/", include("accounts.urls")),
    # URLs de connexion sociale (django-allauth)
    path("social/", include("allauth.urls")),
    path("paiement/", include("payments.urls")),
    path("messagerie/", include("messaging.urls")),
    path("notifications/", include("notifications.urls")),
    path("page/", include("content.urls")),
    path("avis/", include("reviews.urls")),
    path("abonnement/", include("subscriptions.urls")),
    path("culture/", include("culture.urls")),
    # --- PWA : fichiers servis à la racine pour un scope global ---
    path(
        "manifest.webmanifest",
        TemplateView.as_view(
            template_name="pwa/manifest.webmanifest",
            content_type="application/manifest+json",
        ),
        name="pwa-manifest",
    ),
    path(
        "sw.js",
        TemplateView.as_view(
            template_name="pwa/sw.js",
            content_type="application/javascript",
        ),
        name="pwa-service-worker",
    ),
    path(
        "hors-ligne/",
        TemplateView.as_view(template_name="pwa/offline.html"),
        name="pwa-offline",
    ),
    path(
        "browserconfig.xml",
        TemplateView.as_view(
            template_name="pwa/browserconfig.xml",
            content_type="application/xml",
        ),
        name="pwa-browserconfig",
    ),
    path("", include("store.urls")),
]

# Fichiers uploadés en local / disque persistant uniquement (R2/S3 = URLs directes HTTPS)
_uses_cloud_media = (
    settings.STORAGES.get("default", {}).get("BACKEND", "")
    != "django.core.files.storage.FileSystemStorage"
)
if not _uses_cloud_media:
    _media_prefix = settings.MEDIA_URL.strip("/")
    if _media_prefix:
        urlpatterns += [
            re_path(
                rf"^{_media_prefix}/(?P<path>.*)$",
                serve,
                {"document_root": settings.MEDIA_ROOT},
            ),
        ]
