from django.db import models
from django.db.models import Q
from django.utils.text import slugify


class Category(models.Model):
    """Catégorie globale (plateforme) ou personnalisée (une boutique / un prestataire)."""

    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True, related_name="children"
    )
    is_active = models.BooleanField(default=True)
    vendor = models.ForeignKey(
        "marketplace.Vendor",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="custom_categories",
        help_text="Si renseigné : catégorie propre à cette boutique.",
    )
    service_provider = models.ForeignKey(
        "marketplace.ServiceProvider",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="custom_categories",
        help_text="Si renseigné : catégorie propre à ce prestataire.",
    )

    class Meta:
        verbose_name_plural = "categories"
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(vendor__isnull=False, service_provider__isnull=True)
                    | Q(vendor__isnull=True, service_provider__isnull=False)
                    | Q(vendor__isnull=True, service_provider__isnull=True)
                ),
                name="category_at_most_one_owner",
            ),
            models.UniqueConstraint(
                fields=["vendor", "name"],
                condition=Q(vendor__isnull=False),
                name="category_unique_vendor_name",
            ),
            models.UniqueConstraint(
                fields=["service_provider", "name"],
                condition=Q(service_provider__isnull=False),
                name="category_unique_provider_name",
            ),
        ]

    def _ensure_unique_slug(self) -> None:
        prefix = ""
        if self.vendor_id:
            prefix = f"v{self.vendor_id}-"
        elif self.service_provider_id:
            prefix = f"p{self.service_provider_id}-"
        base = slugify(self.name) or "categorie"
        if len(base) > 90:
            base = base[:90].rstrip("-")
        original = f"{prefix}{base}"[:140].rstrip("-")
        slug = original
        counter = 0
        qs = Category.objects.exclude(pk=self.pk) if self.pk else Category.objects.all()
        while qs.filter(slug=slug).exists():
            counter += 1
            suffix = f"-{counter}"
            slug = (original[: 140 - len(suffix)] + suffix).rstrip("-")
        self.slug = slug

    def save(self, *args, **kwargs):
        if not self.slug:
            self._ensure_unique_slug()
        super().save(*args, **kwargs)

    def __str__(self):
        if self.vendor_id:
            return f"{self.name} (boutique)"
        if self.service_provider_id:
            return f"{self.name} (prestataire)"
        return self.name


class CategoryShowcaseImage(models.Model):
    """Photos vitrine pour une catégorie (ex. plats phares en restauration).

    Chaque ligne appartient à une boutique ou un prestataire (obligatoire).
    Pour une catégorie **personnalisée** (rattachée à un vendeur), toutes les
    images portent le même `vendor` / `service_provider` que la catégorie.
    Pour une catégorie **globale**, chaque pro gère jusqu'à SHOWCASE_MAX images
    distinctes pour mettre en avant son offre dans cette catégorie.
    """

    SPACE_GENERAL = "general"
    SPACE_CHAMBRE = "chambre"
    SPACE_SALLE_EAU = "salle_eau"
    SPACE_LIT = "lit"
    SPACE_ACCUEIL = "accueil"
    SPACE_RESTAURATION = "restauration"
    SPACE_EXTERIEUR = "exterieur"
    SPACE_AUTRE = "autre"
    SPACE_KIND_CHOICES = [
        (SPACE_GENERAL, "Général"),
        (SPACE_CHAMBRE, "Chambre"),
        (SPACE_SALLE_EAU, "Salle d'eau / toilettes"),
        (SPACE_LIT, "Literie"),
        (SPACE_ACCUEIL, "Accueil / hall"),
        (SPACE_RESTAURATION, "Restauration / petit-déjeuner"),
        (SPACE_EXTERIEUR, "Extérieur / piscine / jardin"),
        (SPACE_AUTRE, "Autre"),
    ]

    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="showcase_images",
    )
    vendor = models.ForeignKey(
        "marketplace.Vendor",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="category_showcase_images",
    )
    service_provider = models.ForeignKey(
        "marketplace.ServiceProvider",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="category_showcase_images",
    )
    image = models.ImageField(upload_to="catalog/category_showcase/%Y/%m/")
    caption = models.CharField("légende", max_length=200, blank=True)
    showcase_kind = models.CharField(
        "type d'espace",
        max_length=20,
        choices=SPACE_KIND_CHOICES,
        default=SPACE_GENERAL,
        help_text="Utile pour hôtels / résidences : chambre, salle d'eau, accueil, etc.",
    )
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["position", "id"]
        indexes = [
            models.Index(fields=["category", "vendor", "position"]),
            models.Index(fields=["category", "service_provider", "position"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(vendor__isnull=False, service_provider__isnull=True)
                    | models.Q(vendor__isnull=True, service_provider__isnull=False)
                ),
                name="category_showcase_one_owner",
            ),
        ]

    def __str__(self) -> str:  # pragma: no cover
        who = self.vendor or self.service_provider
        return f"{self.category.name} — {who}"


class Product(models.Model):
    PRODUCT = "product"
    SERVICE = "service"

    KIND_CHOICES = [
        (PRODUCT, "Produit"),
        (SERVICE, "Service"),
    ]

    vendor = models.ForeignKey(
        "marketplace.Vendor", on_delete=models.SET_NULL, null=True, blank=True
    )
    service_provider = models.ForeignKey(
        "marketplace.ServiceProvider", on_delete=models.SET_NULL, null=True, blank=True
    )
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    old_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    stock = models.PositiveIntegerField(default=0)
    image = models.ImageField(
        upload_to="catalog/products/%Y/%m/",
        blank=True,
        null=True,
        verbose_name="photo du produit",
    )
    image_url = models.URLField(blank=True)
    kind = models.CharField(max_length=20, choices=KIND_CHOICES, default=PRODUCT)
    location = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    @property
    def promo_discount_percent(self) -> int | None:
        """Pourcentage de réduction si ancien prix > prix actuel."""
        if self.old_price is None:
            return None
        if self.old_price <= self.price or self.old_price <= 0:
            return None
        from decimal import Decimal

        diff = self.old_price - self.price
        pct = (diff / self.old_price) * Decimal(100)
        return int(pct.quantize(Decimal("1")))


class ProductMedia(models.Model):
    IMAGE = "image"
    VIDEO = "video"

    TYPE_CHOICES = [
        (IMAGE, "Image"),
        (VIDEO, "Vidéo"),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="media")
    media_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default=IMAGE)
    url = models.URLField()
    is_primary = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.product} - {self.media_type}"


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    name = models.CharField(max_length=100)
    value = models.CharField(max_length=100)
    price_delta = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    stock = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.product} - {self.name}: {self.value}"

# Create your models here.
