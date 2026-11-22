"""Modèles Dan Prestige Magazine."""

from __future__ import annotations

import secrets
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify


class TeamMember(models.Model):
    name = models.CharField("nom", max_length=120)
    role = models.CharField("rôle", max_length=160)
    bio = models.TextField(blank=True)
    photo = models.ImageField(upload_to="magazine/team/", blank=True, null=True)
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["display_order", "name"]
        verbose_name = "Membre de l'équipe"
        verbose_name_plural = "Équipe"

    def __str__(self) -> str:
        return f"{self.name} — {self.role}"


class Article(models.Model):
    CATEGORY_INTERVIEW = "interview"
    CATEGORY_REPORTAGE = "reportage"
    CATEGORY_PORTRAIT = "portrait"
    CATEGORY_EMISSION = "emission"
    CATEGORY_ACTU = "actu"
    CATEGORY_CHOICES = [
        (CATEGORY_INTERVIEW, "Interview"),
        (CATEGORY_REPORTAGE, "Reportage"),
        (CATEGORY_PORTRAIT, "Portrait"),
        (CATEGORY_EMISSION, "Émission spéciale"),
        (CATEGORY_ACTU, "Actualité"),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    excerpt = models.TextField("chapeau", blank=True)
    body = models.TextField("contenu")
    cover_image = models.ImageField(upload_to="magazine/articles/", blank=True, null=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default=CATEGORY_ACTU)
    locality = models.CharField("région / localité", max_length=120, blank=True)
    author_name = models.CharField(max_length=120, blank=True)
    is_sponsored = models.BooleanField("publireportage", default=False)
    is_published = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    published_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-published_at"]
        verbose_name = "Article"
        verbose_name_plural = "Articles"

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title) or "article"
            slug = base
            i = 1
            while Article.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                i += 1
                slug = f"{base}-{i}"
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.title

    def get_absolute_url(self) -> str:
        return reverse("magazine:article_detail", args=[self.slug])


class Video(models.Model):
    KIND_INTERVIEW = "interview"
    KIND_REPORTAGE = "reportage"
    KIND_EMISSION = "emission"
    KIND_CHOICES = [
        (KIND_INTERVIEW, "Interview vidéo"),
        (KIND_REPORTAGE, "Reportage"),
        (KIND_EMISSION, "Émission spéciale"),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField(blank=True)
    kind = models.CharField(max_length=20, choices=KIND_CHOICES, default=KIND_INTERVIEW)
    locality = models.CharField("région / localité", max_length=120, blank=True)
    thumbnail = models.ImageField(upload_to="magazine/videos/", blank=True, null=True)
    video_url = models.URLField(
        "URL vidéo (YouTube / Vimeo / fichier)",
        help_text="Lien YouTube/Vimeo embarquable, ou URL directe MP4.",
    )
    is_sponsored = models.BooleanField("publireportage", default=False)
    is_published = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    published_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-published_at"]
        verbose_name = "Vidéo"
        verbose_name_plural = "Vidéos"

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title) or "video"
            slug = base
            i = 1
            while Video.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                i += 1
                slug = f"{base}-{i}"
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.title

    def get_absolute_url(self) -> str:
        return reverse("magazine:video_detail", args=[self.slug])

    @property
    def embed_url(self) -> str:
        url = (self.video_url or "").strip()
        if "youtube.com/watch" in url:
            vid = url.split("v=")[-1].split("&")[0]
            return f"https://www.youtube.com/embed/{vid}"
        if "youtu.be/" in url:
            vid = url.rstrip("/").split("/")[-1].split("?")[0]
            return f"https://www.youtube.com/embed/{vid}"
        if "vimeo.com/" in url and "player.vimeo.com" not in url:
            vid = url.rstrip("/").split("/")[-1]
            return f"https://player.vimeo.com/video/{vid}"
        return url


class Portrait(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    caption = models.TextField("légende", blank=True)
    subject_name = models.CharField("personne photographiée", max_length=160, blank=True)
    locality = models.CharField("région / localité", max_length=120, blank=True)
    image = models.ImageField(upload_to="magazine/portraits/")
    photographer = models.CharField(max_length=120, blank=True)
    is_sponsored = models.BooleanField("publireportage", default=False)
    is_published = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    published_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-published_at"]
        verbose_name = "Portrait photographique"
        verbose_name_plural = "Portraits photographiques"

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title) or "portrait"
            slug = base
            i = 1
            while Portrait.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                i += 1
                slug = f"{base}-{i}"
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.title

    def get_absolute_url(self) -> str:
        return reverse("magazine:portrait_detail", args=[self.slug])


class Personality(models.Model):
    """Fiche du répertoire des personnalités Dan."""

    first_name = models.CharField("prénom", max_length=80)
    last_name = models.CharField("nom", max_length=80)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    profession = models.CharField(max_length=160)
    locality = models.CharField("localité d'origine", max_length=120, blank=True)
    region = models.CharField(max_length=120, blank=True)
    photo = models.ImageField(upload_to="magazine/personalities/", blank=True, null=True)
    bio = models.TextField("parcours", blank=True)
    achievements = models.TextField("réalisations", blank=True)
    consent_validated = models.BooleanField(
        "consentement validé",
        default=False,
        help_text="La fiche n'est visible publiquement que si ce champ est coché.",
    )
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["last_name", "first_name"]
        verbose_name = "Personnalité"
        verbose_name_plural = "Répertoire des personnalités"

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(f"{self.first_name} {self.last_name}") or "personnalite"
            slug = base
            i = 1
            while Personality.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                i += 1
                slug = f"{base}-{i}"
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    def __str__(self) -> str:
        return self.full_name

    def get_absolute_url(self) -> str:
        return reverse("magazine:personality_detail", args=[self.slug])


class MagazineIssue(models.Model):
    """Numéro du magazine — vente via Product optionnel (panier Kolê)."""

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    number = models.PositiveIntegerField("numéro", unique=True)
    cover_image = models.ImageField(upload_to="magazine/issues/", blank=True, null=True)
    summary = models.TextField("sommaire / résumé", blank=True)
    published_at = models.DateField(default=timezone.localdate)
    price_fcfa = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("2500"))
    is_special = models.BooleanField("édition spéciale", default=False)
    is_latest = models.BooleanField("dernier numéro", default=False)
    is_published = models.BooleanField(default=True)
    product = models.ForeignKey(
        "catalog.Product",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="magazine_issues",
        help_text="Produit catalogue lié pour l'achat via panier.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-published_at", "-number"]
        verbose_name = "Numéro / édition"
        verbose_name_plural = "Numéros / éditions"

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title) or f"numero-{self.number}"
            slug = base
            i = 1
            while MagazineIssue.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                i += 1
                slug = f"{base}-{i}"
            self.slug = slug
        if self.is_latest:
            MagazineIssue.objects.filter(is_latest=True).exclude(pk=self.pk).update(is_latest=False)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"N°{self.number} — {self.title}"

    def get_absolute_url(self) -> str:
        return reverse("magazine:boutique")


class MagazineSubscriptionPlan(models.Model):
    PERIOD_MONTHLY = "monthly"
    PERIOD_YEARLY = "yearly"
    PERIOD_CHOICES = [
        (PERIOD_MONTHLY, "Mensuel"),
        (PERIOD_YEARLY, "Annuel"),
    ]

    name = models.CharField(max_length=80)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    period = models.CharField(max_length=10, choices=PERIOD_CHOICES, default=PERIOD_MONTHLY)
    price_fcfa = models.DecimalField(max_digits=12, decimal_places=2)
    tagline = models.CharField(max_length=160, blank=True)
    features = models.TextField(
        blank=True,
        help_text="Une avantage par ligne.",
    )
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["display_order", "price_fcfa"]
        verbose_name = "Formule d'abonnement lecteur"
        verbose_name_plural = "Formules d'abonnement lecteur"

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name) or "formule"
            slug = base
            i = 1
            while MagazineSubscriptionPlan.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                i += 1
                slug = f"{base}-{i}"
            self.slug = slug
        super().save(*args, **kwargs)

    def features_list(self) -> list[str]:
        return [line.strip() for line in (self.features or "").splitlines() if line.strip()]

    def __str__(self) -> str:
        return f"{self.name} — {self.price_fcfa} FCFA"


class MagazineSubscription(models.Model):
    STATUS_PENDING = "pending"
    STATUS_ACTIVE = "active"
    STATUS_EXPIRED = "expired"
    STATUS_CANCELLED = "cancelled"
    STATUS_CHOICES = [
        (STATUS_PENDING, "En attente de paiement"),
        (STATUS_ACTIVE, "Actif"),
        (STATUS_EXPIRED, "Expiré"),
        (STATUS_CANCELLED, "Annulé"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="magazine_subscriptions",
        null=True,
        blank=True,
    )
    plan = models.ForeignKey(
        MagazineSubscriptionPlan,
        on_delete=models.PROTECT,
        related_name="subscriptions",
    )
    email = models.EmailField()
    full_name = models.CharField(max_length=160)
    phone = models.CharField(max_length=30, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    reference = models.CharField(max_length=40, unique=True, blank=True)
    amount_fcfa = models.DecimalField(max_digits=12, decimal_places=2)
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Abonnement lecteur"
        verbose_name_plural = "Abonnements lecteurs"

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = f"MAG-{secrets.token_hex(6).upper()}"
        if self.amount_fcfa is None:
            self.amount_fcfa = self.plan.price_fcfa
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.full_name} — {self.plan.name} ({self.get_status_display()})"


class Partner(models.Model):
    name = models.CharField(max_length=160)
    logo = models.ImageField(upload_to="magazine/partners/", blank=True, null=True)
    website = models.URLField(blank=True)
    description = models.TextField(blank=True)
    is_sponsor = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["display_order", "name"]
        verbose_name = "Partenaire"
        verbose_name_plural = "Partenaires"

    def __str__(self) -> str:
        return self.name


class PartnershipInquiry(models.Model):
    OFFER_AD = "publicite"
    OFFER_SPONSORED = "publireportage"
    OFFER_SPECIAL = "edition_speciale"
    OFFER_EVENT = "evenement"
    OFFER_INSTITUTIONAL = "institutionnel"
    OFFER_CHOICES = [
        (OFFER_AD, "Espaces publicitaires"),
        (OFFER_SPONSORED, "Publireportages"),
        (OFFER_SPECIAL, "Sponsoring d'édition spéciale"),
        (OFFER_EVENT, "Couverture d'événement"),
        (OFFER_INSTITUTIONAL, "Partenariat institutionnel / association"),
    ]

    name = models.CharField("nom", max_length=120)
    organization = models.CharField("organisation", max_length=160)
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True)
    offer_type = models.CharField(max_length=30, choices=OFFER_CHOICES)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_handled = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Demande de partenariat"
        verbose_name_plural = "Demandes de partenariat"

    def __str__(self) -> str:
        return f"{self.organization} — {self.get_offer_type_display()}"
