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
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

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

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
