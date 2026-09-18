"""Données partagées entre les pages d'administration."""

from __future__ import annotations

from django.core.paginator import Paginator
from django.db.models import Count, DecimalField, ExpressionWrapper, F, Q, Sum, Value
from django.db.models.functions import Coalesce

from marketplace.models import ServiceProvider, Vendor
from orders.models import Order
from subscriptions.models import Subscription

PAGE_SIZE = 10

_ORDER_STATUSES = [
    Order.STATUS_PENDING,
    Order.STATUS_PAID,
    Order.STATUS_SHIPPED,
    Order.STATUS_DONE,
]


def pending_count() -> int:
    v = Vendor.objects.filter(verification_status=Vendor.STATUS_PENDING).count()
    p = ServiceProvider.objects.filter(verification_status=ServiceProvider.STATUS_PENDING).count()
    return v + p


def overview_stats() -> dict:
    return {
        "total_vendors": Vendor.objects.filter(verification_status=Vendor.STATUS_VERIFIED).count(),
        "total_providers": ServiceProvider.objects.filter(
            verification_status=ServiceProvider.STATUS_VERIFIED
        ).count(),
        "total_orders": Order.objects.exclude(status=Order.STATUS_CANCELLED).count(),
        "global_revenue": Order.objects.exclude(status=Order.STATUS_CANCELLED).aggregate(
            total=Sum("total_amount")
        )["total"]
        or 0,
        "pending_count": pending_count(),
    }


def subscription_stats() -> dict:
    return Subscription.objects.aggregate(
        total=Count("id"),
        active=Count("id", filter=Q(status=Subscription.STATUS_ACTIVE)),
        pending=Count("id", filter=Q(status=Subscription.STATUS_PENDING)),
        past_due=Count("id", filter=Q(status=Subscription.STATUS_PAST_DUE)),
        monthly_revenue=Sum("monthly_amount", filter=Q(status=Subscription.STATUS_ACTIVE)),
    )


def pending_pages(request):
    vendors_qs = (
        Vendor.objects.filter(verification_status=Vendor.STATUS_PENDING)
        .select_related("owner")
        .order_by("-id")
    )
    providers_qs = (
        ServiceProvider.objects.filter(verification_status=ServiceProvider.STATUS_PENDING)
        .select_related("owner")
        .order_by("-id")
    )
    return {
        "vendors_pending_page": Paginator(vendors_qs, PAGE_SIZE).get_page(
            request.GET.get("vendors_page", 1)
        ),
        "providers_pending_page": Paginator(providers_qs, PAGE_SIZE).get_page(
            request.GET.get("providers_page", 1)
        ),
    }


def ranking_pages(request):
    top_vendors_qs = (
        Vendor.objects.filter(verification_status=Vendor.STATUS_VERIFIED)
        .annotate(
            revenue=Coalesce(
                Sum(
                    ExpressionWrapper(
                        F("product__order_items__unit_price") * F("product__order_items__quantity"),
                        output_field=DecimalField(),
                    ),
                    filter=Q(product__order_items__order__status__in=_ORDER_STATUSES),
                ),
                Value(0, output_field=DecimalField()),
            ),
            order_count=Count(
                "product__order_items__order",
                distinct=True,
                filter=Q(product__order_items__order__status__in=_ORDER_STATUSES),
            ),
        )
        .order_by("-revenue")
    )
    top_providers_qs = (
        ServiceProvider.objects.filter(verification_status=ServiceProvider.STATUS_VERIFIED)
        .annotate(
            request_count=Count("servicerequest"),
            approved_count=Count("servicerequest", filter=Q(servicerequest__status="approved")),
        )
        .order_by("-approved_count", "-request_count")
    )
    return {
        "top_vendors_page": Paginator(top_vendors_qs, PAGE_SIZE).get_page(
            request.GET.get("top_vendors_page", 1)
        ),
        "top_providers_page": Paginator(top_providers_qs, PAGE_SIZE).get_page(
            request.GET.get("top_providers_page", 1)
        ),
    }


def users_page(request):
    from django.contrib.auth.models import User

    qs = User.objects.all().select_related("userprofile").order_by("-id")
    return Paginator(qs, PAGE_SIZE).get_page(request.GET.get("users_page", 1))
