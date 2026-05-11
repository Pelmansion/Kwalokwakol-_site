from django.conf import settings
from django.db import models


class Notification(models.Model):
    INFO = "info"
    PROMO = "promo"
    ORDER = "order"
    MESSAGE = "message"

    KIND_CHOICES = [
        (INFO, "Info"),
        (PROMO, "Promo"),
        (ORDER, "Commande"),
        (MESSAGE, "Message"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=120)
    body = models.TextField(blank=True)
    kind = models.CharField(max_length=20, choices=KIND_CHOICES, default=INFO)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

# Create your models here.
