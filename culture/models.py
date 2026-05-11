from __future__ import annotations

import secrets
import uuid
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify


# ===========================================================================
# Profil artiste — extension activable pour vendeurs / prestataires existants
# ===========================================================================
class ArtistProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="artist_profile",
    )
    stage_name = models.CharField("nom de scène", max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    bio = models.TextField("biographie", blank=True)
    region = models.CharField(max_length=100, blank=True, help_text="Région ou ville d'origine")
    city = models.CharField(max_length=100, blank=True)
    primary_genre = models.ForeignKey(
        "culture.MusicGenre",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="artists",
    )
    cover_photo = models.ImageField(upload_to="culture/artists/covers/", blank=True, null=True)
    portrait = models.ImageField(upload_to="culture/artists/portraits/", blank=True, null=True)
    phone = models.CharField(max_length=30, blank=True)
    whatsapp = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)
    facebook = models.URLField(blank=True)
    instagram = models.URLField(blank=True)
    youtube = models.URLField(blank=True)
    tiktok = models.URLField(blank=True)
    spotify = models.URLField(blank=True)

    is_verified = models.BooleanField(default=False, help_text="Badge artiste vérifié")
    is_featured = models.BooleanField(default=False, help_text="Mis en avant en page d'accueil")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_featured", "-created_at"]
        verbose_name = "Profil artiste"
        verbose_name_plural = "Profils artistes"

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.stage_name) or "artiste"
            slug = base
            i = 1
            while ArtistProfile.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                i += 1
                slug = f"{base}-{i}"
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self) -> str:  # pragma: no cover
        return self.stage_name

    def get_absolute_url(self) -> str:
        return reverse("culture:artist_detail", args=[self.slug])

    @property
    def total_plays(self) -> int:
        return sum(s.play_count for s in self.songs.all())

    @property
    def total_downloads(self) -> int:
        return sum(s.download_count for s in self.songs.all())

    @property
    def published_songs_count(self) -> int:
        return self.songs.filter(is_published=True).count()

    @property
    def upcoming_events_count(self) -> int:
        now = timezone.now()
        return self.events.filter(starts_at__gte=now, is_published=True).count()


class MusicGenre(models.Model):
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    icon = models.CharField(max_length=10, blank=True, help_text="Émoji ou icône")
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["display_order", "name"]
        verbose_name = "Genre musical"
        verbose_name_plural = "Genres musicaux"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self) -> str:  # pragma: no cover
        return self.name


# ===========================================================================
# Chansons & achats
# ===========================================================================
class Song(models.Model):
    PRICING_FREE = "free"
    PRICING_PAID = "paid"
    PRICING_CHOICES = [
        (PRICING_FREE, "Gratuit (téléchargement libre)"),
        (PRICING_PAID, "Payant (téléchargement après achat)"),
    ]

    artist = models.ForeignKey(ArtistProfile, on_delete=models.CASCADE, related_name="songs")
    title = models.CharField(max_length=160)
    slug = models.SlugField(max_length=180, blank=True)
    cover_image = models.ImageField(upload_to="culture/songs/covers/", blank=True, null=True)
    audio_file = models.FileField(
        upload_to="culture/songs/audio/",
        help_text="Fichier MP3 ou WAV (audio file)",
    )
    genre = models.ForeignKey(
        MusicGenre, on_delete=models.SET_NULL, null=True, blank=True, related_name="songs"
    )
    description = models.TextField(blank=True)
    lyrics = models.TextField("paroles", blank=True)
    release_date = models.DateField(null=True, blank=True)
    duration_seconds = models.PositiveIntegerField(default=0, help_text="Durée en secondes")

    pricing = models.CharField(max_length=10, choices=PRICING_CHOICES, default=PRICING_FREE)
    price_fcfa = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0"))
    allow_streaming = models.BooleanField(
        default=True,
        help_text="Si coché, la chanson peut être écoutée gratuitement en streaming",
    )

    play_count = models.PositiveIntegerField(default=0)
    download_count = models.PositiveIntegerField(default=0)

    is_published = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_featured", "-created_at"]

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title) or "chanson"
            slug = f"{base}-{secrets.token_hex(3)}"
            self.slug = slug
        if self.pricing == self.PRICING_FREE:
            self.price_fcfa = Decimal("0")
        super().save(*args, **kwargs)

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.title} — {self.artist.stage_name}"

    def get_absolute_url(self) -> str:
        return reverse("culture:song_detail", args=[self.slug])

    @property
    def is_free(self) -> bool:
        return self.pricing == self.PRICING_FREE

    @property
    def duration_display(self) -> str:
        if not self.duration_seconds:
            return "—"
        m, s = divmod(int(self.duration_seconds), 60)
        return f"{m}:{s:02d}"

    def user_has_access(self, user) -> bool:
        """Le user peut-il télécharger cette chanson ?"""
        if self.is_free:
            return True
        if not user.is_authenticated:
            return False
        if user == self.artist.user:
            return True
        return SongPurchase.objects.filter(song=self, user=user, is_paid=True).exists()


class SongPurchase(models.Model):
    song = models.ForeignKey(Song, on_delete=models.CASCADE, related_name="purchases")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="song_purchases"
    )
    amount_fcfa = models.DecimalField(max_digits=10, decimal_places=2)
    reference = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    download_token = models.CharField(max_length=64, unique=True, editable=False)
    is_paid = models.BooleanField(default=False)
    paid_at = models.DateTimeField(null=True, blank=True)
    payment_method = models.CharField(max_length=40, blank=True)
    download_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Achat de chanson"
        verbose_name_plural = "Achats de chansons"

    def save(self, *args, **kwargs):
        if not self.download_token:
            self.download_token = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)

    def mark_paid(self, method: str = "sandbox") -> None:
        self.is_paid = True
        self.paid_at = timezone.now()
        self.payment_method = method
        self.save(update_fields=["is_paid", "paid_at", "payment_method"])

    def __str__(self) -> str:  # pragma: no cover
        return f"Achat {self.reference} — {self.song.title}"


class SongPlay(models.Model):
    """Trace minimale des écoutes pour les compteurs."""

    song = models.ForeignKey(Song, on_delete=models.CASCADE, related_name="plays")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    played_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ["-played_at"]
        indexes = [models.Index(fields=["song", "-played_at"])]


# ===========================================================================
# Concerts & billetterie
# ===========================================================================
class Event(models.Model):
    STATUS_DRAFT = "draft"
    STATUS_PUBLISHED = "published"
    STATUS_CANCELLED = "cancelled"
    STATUS_ENDED = "ended"
    STATUS_CHOICES = [
        (STATUS_DRAFT, "Brouillon"),
        (STATUS_PUBLISHED, "Publié"),
        (STATUS_CANCELLED, "Annulé"),
        (STATUS_ENDED, "Terminé"),
    ]

    organizer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="organized_events",
    )
    headlining_artist = models.ForeignKey(
        ArtistProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="events",
        help_text="Artiste principal (tête d'affiche)",
    )
    featured_artists = models.ManyToManyField(
        ArtistProfile, blank=True, related_name="events_featured", verbose_name="Artistes invités"
    )

    title = models.CharField(max_length=180)
    slug = models.SlugField(max_length=200, blank=True, unique=True)
    poster = models.ImageField(upload_to="culture/events/posters/", blank=True, null=True)
    description = models.TextField()
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField(null=True, blank=True)
    venue_name = models.CharField(max_length=180)
    address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    region = models.CharField(max_length=100, blank=True)
    map_url = models.URLField(blank=True, help_text="Lien Google Maps (optionnel)")

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    is_featured = models.BooleanField(default=False)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_featured", "starts_at"]
        verbose_name = "Concert / Événement"
        verbose_name_plural = "Concerts / Événements"

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title) or "concert"
            slug = base
            i = 1
            while Event.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                i += 1
                slug = f"{base}-{i}"
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self) -> str:  # pragma: no cover
        return self.title

    def get_absolute_url(self) -> str:
        return reverse("culture:event_detail", args=[self.slug])

    @property
    def is_past(self) -> bool:
        ref = self.ends_at or self.starts_at
        return ref < timezone.now()

    @property
    def is_upcoming(self) -> bool:
        return self.starts_at > timezone.now()

    @property
    def is_open_for_sale(self) -> bool:
        return (
            self.is_published
            and self.status == self.STATUS_PUBLISHED
            and not self.is_past
        )

    @property
    def total_capacity(self) -> int:
        return sum(c.quantity_total for c in self.ticket_categories.all())

    @property
    def total_sold(self) -> int:
        return sum(c.quantity_sold for c in self.ticket_categories.all())

    @property
    def cheapest_price(self) -> Decimal | None:
        prices = [c.price_fcfa for c in self.ticket_categories.filter(is_active=True)]
        return min(prices) if prices else None


class TicketCategory(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="ticket_categories")
    name = models.CharField(max_length=80, help_text="Ex: Standard, VIP, Carré Or")
    description = models.CharField(max_length=255, blank=True, help_text="Avantages inclus")
    price_fcfa = models.DecimalField(max_digits=10, decimal_places=2)
    quantity_total = models.PositiveIntegerField(default=0)
    quantity_sold = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)
    color = models.CharField(
        max_length=20, default="#C2410C", help_text="Couleur hex pour la badge billet"
    )

    class Meta:
        ordering = ["display_order", "price_fcfa"]
        verbose_name = "Catégorie de billet"
        verbose_name_plural = "Catégories de billets"

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.event.title} — {self.name}"

    @property
    def quantity_remaining(self) -> int:
        return max(0, self.quantity_total - self.quantity_sold)

    @property
    def is_sold_out(self) -> bool:
        return self.quantity_remaining <= 0

    @property
    def percent_sold(self) -> int:
        if self.quantity_total == 0:
            return 0
        return int(round(100 * self.quantity_sold / self.quantity_total))


class Ticket(models.Model):
    STATUS_PENDING = "pending"
    STATUS_VALID = "valid"
    STATUS_USED = "used"
    STATUS_CANCELLED = "cancelled"
    STATUS_CHOICES = [
        (STATUS_PENDING, "En attente de paiement"),
        (STATUS_VALID, "Valide"),
        (STATUS_USED, "Utilisé"),
        (STATUS_CANCELLED, "Annulé"),
    ]

    event = models.ForeignKey(Event, on_delete=models.PROTECT, related_name="tickets")
    category = models.ForeignKey(TicketCategory, on_delete=models.PROTECT, related_name="tickets")
    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tickets",
    )
    buyer_name = models.CharField(max_length=120)
    buyer_email = models.EmailField()
    buyer_phone = models.CharField(max_length=30, blank=True)

    reference = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    secret_code = models.CharField(max_length=64, unique=True, editable=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    amount_fcfa = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=40, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    used_at = models.DateTimeField(null=True, blank=True)
    used_by = models.CharField(max_length=120, blank=True, help_text="Nom du contrôleur qui a validé")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.secret_code:
            self.secret_code = secrets.token_urlsafe(24)
        super().save(*args, **kwargs)

    def mark_paid(self, method: str = "sandbox") -> None:
        self.status = self.STATUS_VALID
        self.payment_method = method
        self.paid_at = timezone.now()
        self.save(update_fields=["status", "payment_method", "paid_at"])
        TicketCategory.objects.filter(pk=self.category_id).update(
            quantity_sold=models.F("quantity_sold") + 1
        )

    def get_absolute_url(self) -> str:
        return reverse("culture:ticket_detail", args=[str(self.reference)])

    def get_check_url(self) -> str:
        return reverse(
            "culture:ticket_check", args=[str(self.reference), self.secret_code]
        )

    @property
    def qr_payload(self) -> str:
        """Donnée encodée dans le QR : URL absolue de vérification."""
        return f"{self.reference}:{self.secret_code}"

    def __str__(self) -> str:  # pragma: no cover
        return f"Billet {self.reference} — {self.event.title}"
