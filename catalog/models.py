from django.db import models
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True, related_name="children"
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "categories"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


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
