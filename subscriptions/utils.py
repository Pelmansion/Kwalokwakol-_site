"""Helpers et décorateurs pour gérer les abonnements vendeur / prestataire."""
from __future__ import annotations

from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import redirect
from django.utils import timezone

from .models import Subscription


def active_subscription_q(prefix: str = "subscription") -> Q:
    """Retourne une condition Q filtrant les souscriptions actives sur la relation donnée."""
    return Q(
        **{
            f"{prefix}__status": Subscription.STATUS_ACTIVE,
            f"{prefix}__current_period_end__gt": timezone.now(),
        }
    )


def active_product_filter() -> Q:
    """Q qui garde les produits/services dont le vendeur OU le prestataire est abonné."""
    now = timezone.now()
    return Q(
        vendor__subscription__status=Subscription.STATUS_ACTIVE,
        vendor__subscription__current_period_end__gt=now,
    ) | Q(
        service_provider__subscription__status=Subscription.STATUS_ACTIVE,
        service_provider__subscription__current_period_end__gt=now,
    )


def get_user_subscription(user):
    """Retourne l'abonnement lié à ce user (vendor OU provider), ou None."""
    if not user or not user.is_authenticated:
        return None
    sub = (
        Subscription.objects.select_related("plan", "vendor", "service_provider")
        .filter(vendor__owner=user)
        .first()
    )
    if sub:
        return sub
    return (
        Subscription.objects.select_related("plan", "vendor", "service_provider")
        .filter(service_provider__owner=user)
        .first()
    )


def get_or_create_subscription_for_vendor(vendor, *, monthly_amount=None, plan=None) -> Subscription:
    sub = getattr(vendor, "subscription", None)
    if sub:
        return sub
    return Subscription.objects.create(
        vendor=vendor,
        plan=plan,
        monthly_amount=monthly_amount if monthly_amount is not None else 0,
    )


def get_or_create_subscription_for_provider(provider, *, monthly_amount=None, plan=None) -> Subscription:
    sub = getattr(provider, "subscription", None)
    if sub:
        return sub
    return Subscription.objects.create(
        service_provider=provider,
        plan=plan,
        monthly_amount=monthly_amount if monthly_amount is not None else 0,
    )


def subscription_active(user) -> bool:
    sub = get_user_subscription(user)
    return bool(sub and sub.is_active_now())


def subscription_required(view_func):
    """Décorateur qui impose un abonnement actif pour accéder à la vue.

    Redirige vers la page d'abonnement sinon.
    """

    @wraps(view_func)
    @login_required
    def _wrapped(request, *args, **kwargs):
        sub = get_user_subscription(request.user)
        if not sub:
            messages.warning(
                request,
                "Vous devez choisir une formule d'abonnement pour accéder à cet espace.",
            )
            return redirect("subscriptions:choose_plan")
        if not sub.is_active_now():
            if sub.status == Subscription.STATUS_PENDING and not sub.monthly_amount:
                messages.info(
                    request,
                    "Votre abonnement est en attente de validation par l'administrateur.",
                )
            else:
                messages.warning(
                    request,
                    "Votre abonnement n'est pas actif. Veuillez régler le paiement pour continuer.",
                )
            return redirect("subscriptions:my_subscription")
        return view_func(request, *args, **kwargs)

    return _wrapped
