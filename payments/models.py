from django.db import models


class Payment(models.Model):
    STATUS_PENDING = "pending"
    STATUS_SUCCESS = "success"
    STATUS_FAILED = "failed"

    STATUS_CHOICES = [
        (STATUS_PENDING, "En attente"),
        (STATUS_SUCCESS, "Réussi"),
        (STATUS_FAILED, "Échoué"),
    ]

    PROVIDER_CARD = "card"
    PROVIDER_MOBILE = "mobile_money"
    PROVIDER_PAYPAL = "paypal"
    PROVIDER_LOCAL = "local"
    PROVIDER_GENIUS = "genius"

    PROVIDER_CHOICES = [
        (PROVIDER_CARD, "Carte bancaire"),
        (PROVIDER_MOBILE, "Mobile Money"),
        (PROVIDER_PAYPAL, "PayPal"),
        (PROVIDER_LOCAL, "Autre"),
        (PROVIDER_GENIUS, "Paiement en ligne"),
    ]

    order = models.ForeignKey("orders.Order", on_delete=models.CASCADE, related_name="payments")
    provider = models.CharField(max_length=30, choices=PROVIDER_CHOICES, default=PROVIDER_CARD)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reference = models.CharField(max_length=80, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

# Create your models here.
