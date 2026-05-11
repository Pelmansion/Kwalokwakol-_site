from __future__ import annotations

import secrets
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.text import slugify


class SubscriptionPlan(models.Model):
    """Formule type prédéfinie par l'admin (Starter, Pro, Premium...)."""

    TARGET_VENDOR = "vendor"
    TARGET_PROVIDER = "provider"
    TARGET_BOTH = "both"
    TARGET_CHOICES = [
        (TARGET_VENDOR, "Vendeurs"),
        (TARGET_PROVIDER, "Prestataires"),
        (TARGET_BOTH, "Vendeurs & Prestataires"),
    ]

    name = models.CharField(max_length=60)
    slug = models.SlugField(max_length=80, unique=True, blank=True)
    monthly_amount = models.DecimalField(max_digits=10, decimal_places=2)
    target = models.CharField(max_length=10, choices=TARGET_CHOICES, default=TARGET_BOTH)
    tagline = models.CharField(max_length=140, blank=True)
    description = models.TextField(blank=True)
    features = models.TextField(
        blank=True,
        help_text="Une fonctionnalité par ligne (affichée sous forme de puces).",
    )
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False, help_text="Mettre en avant ce plan.")
    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["display_order", "monthly_amount"]

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name) or "plan"
            slug = base
            i = 1
            while SubscriptionPlan.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                i += 1
                slug = f"{base}-{i}"
            self.slug = slug
        super().save(*args, **kwargs)

    def features_list(self) -> list[str]:
        return [line.strip() for line in (self.features or "").splitlines() if line.strip()]

    def accepts_vendors(self) -> bool:
        return self.target in (self.TARGET_VENDOR, self.TARGET_BOTH)

    def accepts_providers(self) -> bool:
        return self.target in (self.TARGET_PROVIDER, self.TARGET_BOTH)

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.name} — {self.monthly_amount} FCFA/mois"


class Subscription(models.Model):
    """Abonnement mensuel d'un vendeur ou d'un prestataire."""

    STATUS_PENDING = "pending"       # créé, pas encore payé
    STATUS_ACTIVE = "active"         # à jour de paiement
    STATUS_PAST_DUE = "past_due"     # expiré, doit renouveler
    STATUS_CANCELLED = "cancelled"   # annulé par admin / vendeur
    STATUS_CHOICES = [
        (STATUS_PENDING, "En attente de paiement"),
        (STATUS_ACTIVE, "Actif"),
        (STATUS_PAST_DUE, "Expiré"),
        (STATUS_CANCELLED, "Annulé"),
    ]

    vendor = models.OneToOneField(
        "marketplace.Vendor",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="subscription",
    )
    service_provider = models.OneToOneField(
        "marketplace.ServiceProvider",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="subscription",
    )

    plan = models.ForeignKey(
        SubscriptionPlan,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="subscriptions",
    )
    monthly_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Montant mensuel en FCFA. Peut différer du plan pour personnaliser.",
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)

    started_at = models.DateTimeField(null=True, blank=True)
    current_period_end = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    admin_note = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(vendor__isnull=False, service_provider__isnull=True)
                    | models.Q(vendor__isnull=True, service_provider__isnull=False)
                ),
                name="subscription_exactly_one_owner",
            ),
        ]

    def __str__(self) -> str:  # pragma: no cover
        target = self.vendor or self.service_provider
        return f"Abonnement {target} — {self.get_status_display()}"

    @property
    def owner_profile(self):
        return self.vendor or self.service_provider

    @property
    def owner_type(self) -> str:
        return "vendor" if self.vendor_id else "provider"

    @property
    def owner_name(self) -> str:
        prof = self.owner_profile
        return getattr(prof, "name", "—")

    def is_active_now(self) -> bool:
        if self.status != self.STATUS_ACTIVE:
            return False
        if not self.current_period_end:
            return False
        return self.current_period_end > timezone.now()

    def needs_payment(self) -> bool:
        return self.status in (self.STATUS_PENDING, self.STATUS_PAST_DUE)

    def days_remaining(self) -> int | None:
        if not self.current_period_end:
            return None
        delta = self.current_period_end - timezone.now()
        return max(0, delta.days)

    def activate_period(self, *, days: int = 30) -> "SubscriptionPayment":
        """Crée un paiement réussi et étend la période d'un mois."""
        now = timezone.now()
        period_start = (
            self.current_period_end
            if self.current_period_end and self.current_period_end > now
            else now
        )
        period_end = period_start + timedelta(days=days)

        payment = SubscriptionPayment.objects.create(
            subscription=self,
            amount=self.monthly_amount,
            status=SubscriptionPayment.STATUS_SUCCESS,
            period_start=period_start,
            period_end=period_end,
            paid_at=now,
            reference=f"SUB-{secrets.token_hex(4).upper()}",
        )

        if not self.started_at:
            self.started_at = now
        self.current_period_end = period_end
        self.status = self.STATUS_ACTIVE
        self.save(update_fields=["started_at", "current_period_end", "status", "updated_at"])
        return payment


class SubscriptionPayment(models.Model):
    """Historique des paiements d'abonnement."""

    STATUS_PENDING = "pending"
    STATUS_SUCCESS = "success"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = [
        (STATUS_PENDING, "En attente"),
        (STATUS_SUCCESS, "Payé"),
        (STATUS_FAILED, "Échoué"),
    ]

    PROVIDER_CARD = "card"
    PROVIDER_MOBILE = "mobile_money"
    PROVIDER_MANUAL = "manual"
    PROVIDER_CHOICES = [
        (PROVIDER_CARD, "Carte bancaire"),
        (PROVIDER_MOBILE, "Mobile Money"),
        (PROVIDER_MANUAL, "Paiement manuel"),
    ]

    subscription = models.ForeignKey(
        Subscription, on_delete=models.CASCADE, related_name="payments"
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    provider = models.CharField(max_length=30, choices=PROVIDER_CHOICES, default=PROVIDER_CARD)
    reference = models.CharField(max_length=80, blank=True)

    period_start = models.DateTimeField(null=True, blank=True)
    period_end = models.DateTimeField(null=True, blank=True)

    paid_at = models.DateTimeField(null=True, blank=True)
    failed_reason = models.CharField(max_length=200, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:  # pragma: no cover
        return f"Paiement {self.amount} FCFA — {self.get_status_display()}"

    def mark_success(self) -> None:
        """Marque un paiement comme réussi et active l'abonnement."""
        now = timezone.now()
        self.status = self.STATUS_SUCCESS
        self.paid_at = now
        if not self.reference:
            self.reference = f"SUB-{secrets.token_hex(4).upper()}"

        sub = self.subscription
        period_start = (
            sub.current_period_end
            if sub.current_period_end and sub.current_period_end > now
            else now
        )
        period_end = period_start + timedelta(days=30)
        self.period_start = period_start
        self.period_end = period_end
        self.save()

        if not sub.started_at:
            sub.started_at = now
        sub.current_period_end = period_end
        sub.status = Subscription.STATUS_ACTIVE
        sub.save(update_fields=["started_at", "current_period_end", "status", "updated_at"])

    def mark_failed(self, reason: str = "") -> None:
        self.status = self.STATUS_FAILED
        if reason:
            self.failed_reason = reason[:200]
        self.save(update_fields=["status", "failed_reason", "updated_at"])
