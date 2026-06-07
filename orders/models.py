from decimal import Decimal

from django.db import models


class Order(models.Model):
    STATUS_PENDING = "pending"
    STATUS_PAID = "paid"
    STATUS_SHIPPED = "shipped"
    STATUS_DONE = "done"
    STATUS_CANCELLED = "cancelled"

    STATUS_CHOICES = [
        (STATUS_PENDING, "En attente"),
        (STATUS_PAID, "Payée"),
        (STATUS_SHIPPED, "Expédiée"),
        (STATUS_DONE, "Terminée"),
        (STATUS_CANCELLED, "Annulée"),
    ]

    PAYMENT_PENDING = "pending"
    PAYMENT_SUCCESS = "success"
    PAYMENT_FAILED = "failed"

    PAYMENT_CHOICES = [
        (PAYMENT_PENDING, "En attente"),
        (PAYMENT_SUCCESS, "Payée"),
        (PAYMENT_FAILED, "Échouée"),
    ]

    METHOD_CARD = "card"
    METHOD_MOBILE = "mobile_money"
    METHOD_PAYPAL = "paypal"
    METHOD_LOCAL = "local"
    METHOD_GENIUS = "genius"

    METHOD_CHOICES = [
        (METHOD_CARD, "Carte bancaire"),
        (METHOD_MOBILE, "Mobile Money"),
        (METHOD_PAYPAL, "PayPal"),
        (METHOD_LOCAL, "Autre"),
        (METHOD_GENIUS, "Paiement en ligne"),
    ]

    DELIVERY_STANDARD = "standard"
    DELIVERY_EXPRESS = "express"

    DELIVERY_CHOICES = [
        (DELIVERY_STANDARD, "Standard"),
        (DELIVERY_EXPRESS, "Express"),
    ]

    # Tarifs plateforme : produits sans vendeur ni prestataire (voir store.delivery)
    DELIVERY_FEE_STANDARD = Decimal("200")
    DELIVERY_FEE_EXPRESS = Decimal("500")

    user = models.ForeignKey(
        "auth.User", on_delete=models.SET_NULL, null=True, blank=True
    )
    full_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=30)
    email = models.EmailField()
    address = models.CharField(max_length=250)
    city = models.CharField(max_length=120)
    delivery_option = models.CharField(
        max_length=20, choices=DELIVERY_CHOICES, default=DELIVERY_STANDARD
    )
    delivery_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    payment_status = models.CharField(
        max_length=20, choices=PAYMENT_CHOICES, default=PAYMENT_PENDING
    )
    payment_method = models.CharField(
        max_length=50, choices=METHOD_CHOICES, default=METHOD_CARD
    )
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tracking_code = models.CharField(max_length=40, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Commande {self.pk} - {self.full_name}"

    @classmethod
    def delivery_fee_amount(cls, delivery_option: str) -> Decimal:
        if delivery_option == cls.DELIVERY_EXPRESS:
            return cls.DELIVERY_FEE_EXPRESS
        return cls.DELIVERY_FEE_STANDARD

    def subtotal_items(self) -> Decimal:
        """Somme des lignes (hors frais de livraison)."""
        from django.db.models import DecimalField, ExpressionWrapper, F, Sum

        result = self.items.aggregate(
            s=Sum(
                ExpressionWrapper(
                    F("quantity") * F("unit_price"),
                    output_field=DecimalField(max_digits=14, decimal_places=2),
                )
            )
        )["s"]
        return result if result is not None else Decimal("0")


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(
        "catalog.Product",
        on_delete=models.SET_NULL,
        null=True,
        related_name="order_items",
    )
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    variant = models.ForeignKey(
        "catalog.ProductVariant", on_delete=models.SET_NULL, null=True, blank=True
    )

    def __str__(self):
        return f"{self.product} x {self.quantity}"


class OrderStatusHistory(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="status_history")
    status = models.CharField(max_length=20, choices=Order.STATUS_CHOICES)
    note = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

# Create your models here.
