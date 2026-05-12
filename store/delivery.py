"""Calcul des frais de livraison en fonction des vendeurs / prestataires du panier."""

from __future__ import annotations

from collections.abc import Iterable
from decimal import Decimal

from catalog.models import Product
from marketplace.models import ServiceProvider, Vendor
from orders.models import Order


def cart_delivery_fee(products: Iterable[Product], *, delivery_option: str) -> Decimal:
    """
    Somme des frais par boutique (Vendor) distincte et par prestataire (ServiceProvider)
    pour les produits sans boutique, plus une fois le tarif plateforme si le panier
    contient des articles sans vendeur ni prestataire.
    """
    vendor_ids: set[int] = set()
    provider_ids: set[int] = set()
    has_platform_product = False

    for p in products:
        if p.vendor_id:
            vendor_ids.add(p.vendor_id)
        elif p.service_provider_id:
            provider_ids.add(p.service_provider_id)
        else:
            has_platform_product = True

    total = Decimal("0")
    fallback = Order.delivery_fee_amount(delivery_option)

    vendors = {v.pk: v for v in Vendor.objects.filter(pk__in=vendor_ids)}
    for vid in vendor_ids:
        v = vendors.get(vid)
        total += v.delivery_fee_for(delivery_option) if v else fallback

    providers = {sp.pk: sp for sp in ServiceProvider.objects.filter(pk__in=provider_ids)}
    for pid in provider_ids:
        sp = providers.get(pid)
        total += sp.delivery_fee_for(delivery_option) if sp else fallback

    if has_platform_product:
        total += fallback

    return total
