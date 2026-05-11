from django.conf import settings
from django.db import models
from django.utils.text import slugify


class Vendor(models.Model):
    STATUS_PENDING = "pending"
    STATUS_VERIFIED = "verified"
    STATUS_REJECTED = "rejected"

    STATUS_CHOICES = [
        (STATUS_PENDING, "En attente"),
        (STATUS_VERIFIED, "Vérifié"),
        (STATUS_REJECTED, "Rejeté"),
    ]

    OFFER_SERVICE = "service"
    OFFER_PRODUCT = "product"
    OFFER_BOTH = "both"

    OFFER_CHOICES = [
        (OFFER_SERVICE, "Services"),
        (OFFER_PRODUCT, "Produits"),
        (OFFER_BOTH, "Produits & services"),
    ]

    owner = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    name = models.CharField(max_length=150, unique=True)
    slug = models.SlugField(max_length=170, unique=True, blank=True)
    description = models.TextField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(unique=True, help_text="Email unique de la boutique (unique parmi toutes les boutiques et prestataires)")
    location = models.CharField(max_length=200, blank=True)
    id_number = models.CharField(max_length=50, unique=True, help_text="Numéro d'identité unique (unique parmi toutes les boutiques et prestataires)")
    id_document_front = models.ImageField(
        upload_to="kyc/vendor/id_front/", help_text="Pièce d'identité recto"
    )
    id_document_back = models.ImageField(
        upload_to="kyc/vendor/id_back/", help_text="Pièce d'identité verso"
    )
    profile_photo = models.ImageField(
        upload_to="kyc/vendor/photo/", blank=True, null=True
    )
    offer_type = models.CharField(max_length=20, choices=OFFER_CHOICES, default=OFFER_BOTH)
    services_overview = models.TextField(blank=True)
    portfolio_url = models.URLField(blank=True)
    subscription_services = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    verification_status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING
    )
    verified_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class ServiceProvider(models.Model):
    STATUS_PENDING = "pending"
    STATUS_VERIFIED = "verified"
    STATUS_REJECTED = "rejected"

    STATUS_CHOICES = [
        (STATUS_PENDING, "En attente"),
        (STATUS_VERIFIED, "Vérifié"),
        (STATUS_REJECTED, "Rejeté"),
    ]

    owner = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    name = models.CharField(max_length=150, unique=True)
    slug = models.SlugField(max_length=170, unique=True, blank=True)
    description = models.TextField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(
        unique=True, help_text="Email unique du prestataire de services (unique parmi toutes les boutiques et prestataires)"
    )
    location = models.CharField(max_length=200, blank=True)
    id_number = models.CharField(
        max_length=50, unique=True, help_text="Numéro d'identité unique du prestataire (unique parmi toutes les boutiques et prestataires)"
    )
    id_document_front = models.ImageField(
        upload_to="kyc/service_provider/id_front/", help_text="Pièce d'identité recto"
    )
    id_document_back = models.ImageField(
        upload_to="kyc/service_provider/id_back/", help_text="Pièce d'identité verso"
    )
    profile_photo = models.ImageField(
        upload_to="kyc/service_provider/photo/", blank=True, null=True
    )
    services_overview = models.TextField(blank=True)
    portfolio_url = models.URLField(blank=True)
    display_services_as_provider = models.BooleanField(
        default=False,
        verbose_name="Ce sont mes propres services que je propose",
        help_text="Si coché, les services sont affichés en fiche prestataire (photo, badges, localisation). Sinon affichage produit classique.",
    )
    is_active = models.BooleanField(default=True)
    verification_status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING
    )
    verified_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class ServiceRequest(models.Model):
    STATUS_PENDING = "pending"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"

    STATUS_CHOICES = [
        (STATUS_PENDING, "En attente"),
        (STATUS_APPROVED, "Validé"),
        (STATUS_REJECTED, "Refusé"),
    ]

    service = models.ForeignKey("catalog.Product", on_delete=models.CASCADE)
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    vendor = models.ForeignKey("marketplace.Vendor", on_delete=models.CASCADE, null=True, blank=True)
    service_provider = models.ForeignKey(
        "marketplace.ServiceProvider", on_delete=models.CASCADE, null=True, blank=True
    )
    is_interested = models.BooleanField(default=True)
    comment = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("service", "customer")
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.customer} - {self.service}"

# Create your models here.
