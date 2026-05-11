from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    ROLE_CUSTOMER = "customer"
    ROLE_ADMIN = "admin"
    ROLE_SUPER_ADMIN = "super_admin"

    ROLE_CHOICES = [
        (ROLE_CUSTOMER, "Client"),
        (ROLE_ADMIN, "Admin"),
        (ROLE_SUPER_ADMIN, "Super admin"),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    phone = models.CharField(max_length=30, blank=True)
    default_address = models.CharField(max_length=250, blank=True)
    city = models.CharField(max_length=120, blank=True)
    role = models.CharField(
        max_length=20, choices=ROLE_CHOICES, default=ROLE_CUSTOMER
    )

    def __str__(self):
        return self.user.username


class Address(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    label = models.CharField(max_length=100, blank=True)
    address = models.CharField(max_length=250)
    city = models.CharField(max_length=120)
    phone = models.CharField(max_length=30)
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user} - {self.address}"


class Favorite(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    product = models.ForeignKey("catalog.Product", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

# Create your models here.
