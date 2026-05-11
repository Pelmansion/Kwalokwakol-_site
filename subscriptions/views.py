from __future__ import annotations

import secrets
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q, Sum
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from marketplace.models import ServiceProvider, Vendor

from .forms import AdminSetAmountForm, ChoosePlanForm, SubscriptionPlanForm
from .models import Subscription, SubscriptionPayment, SubscriptionPlan
from .utils import (
    get_or_create_subscription_for_provider,
    get_or_create_subscription_for_vendor,
    get_user_subscription,
)


# ---------------------------------------------------------------------------
# Helpers accès admin
# ---------------------------------------------------------------------------
def _ensure_admin(user, *, super_only: bool = False):
    from accounts.models import UserProfile

    if not user.is_authenticated:
        raise PermissionDenied
    if user.is_superuser:
        return
    try:
        profile = user.userprofile
    except UserProfile.DoesNotExist as exc:
        raise PermissionDenied from exc
    allowed = (
        {UserProfile.ROLE_SUPER_ADMIN}
        if super_only
        else {UserProfile.ROLE_ADMIN, UserProfile.ROLE_SUPER_ADMIN}
    )
    if profile.role not in allowed:
        raise PermissionDenied


def _target_for_user(user) -> str:
    if Vendor.objects.filter(owner=user).exists():
        return "vendor"
    if ServiceProvider.objects.filter(owner=user).exists():
        return "provider"
    return "both"


# ---------------------------------------------------------------------------
# Vues publiques / vendeur / prestataire
# ---------------------------------------------------------------------------
@login_required
def choose_plan(request):
    """Première étape : choisir une formule d'abonnement."""
    vendor = Vendor.objects.filter(owner=request.user).first()
    provider = ServiceProvider.objects.filter(owner=request.user).first()

    if not vendor and not provider:
        messages.info(
            request,
            "Vous devez d'abord créer votre profil vendeur ou prestataire.",
        )
        return redirect("marketplace:vendor_register")

    target = "vendor" if vendor else "provider"
    existing = get_user_subscription(request.user)

    if existing and existing.monthly_amount and existing.status != Subscription.STATUS_CANCELLED:
        return redirect("subscriptions:my_subscription")

    plans = SubscriptionPlan.objects.filter(is_active=True)
    if target == "vendor":
        plans = plans.filter(target__in=[SubscriptionPlan.TARGET_VENDOR, SubscriptionPlan.TARGET_BOTH])
    else:
        plans = plans.filter(target__in=[SubscriptionPlan.TARGET_PROVIDER, SubscriptionPlan.TARGET_BOTH])

    if request.method == "POST":
        form = ChoosePlanForm(request.POST, target=target)
        if form.is_valid():
            plan = form.cleaned_data["plan"]
            if vendor:
                sub = get_or_create_subscription_for_vendor(
                    vendor, monthly_amount=plan.monthly_amount, plan=plan
                )
            else:
                sub = get_or_create_subscription_for_provider(
                    provider, monthly_amount=plan.monthly_amount, plan=plan
                )
            sub.plan = plan
            sub.monthly_amount = plan.monthly_amount
            if sub.status == Subscription.STATUS_CANCELLED:
                sub.status = Subscription.STATUS_PENDING
            sub.save()
            messages.success(
                request,
                f"Formule {plan.name} sélectionnée. Procédez au paiement pour activer votre compte.",
            )
            return redirect("subscriptions:my_subscription")
    else:
        form = ChoosePlanForm(target=target)

    return render(
        request,
        "subscriptions/choose_plan.html",
        {
            "form": form,
            "plans": plans,
            "target": target,
            "vendor": vendor,
            "provider": provider,
        },
    )


@login_required
def my_subscription(request):
    """Tableau de bord de l'abonnement du vendeur / prestataire."""
    sub = get_user_subscription(request.user)
    vendor = Vendor.objects.filter(owner=request.user).first()
    provider = ServiceProvider.objects.filter(owner=request.user).first()

    if not sub:
        if not vendor and not provider:
            return redirect("marketplace:vendor_register")
        return redirect("subscriptions:choose_plan")

    payments = sub.payments.order_by("-created_at")[:10]

    return render(
        request,
        "subscriptions/my_subscription.html",
        {
            "subscription": sub,
            "payments": payments,
            "vendor": vendor,
            "provider": provider,
        },
    )


@login_required
@require_POST
def start_payment(request):
    """Crée un SubscriptionPayment en attente et redirige vers le sandbox."""
    sub = get_user_subscription(request.user)
    if not sub:
        return redirect("subscriptions:choose_plan")

    if not sub.monthly_amount or sub.monthly_amount <= 0:
        messages.error(
            request,
            "Aucun montant d'abonnement n'est encore défini. Contactez l'administrateur.",
        )
        return redirect("subscriptions:my_subscription")

    if sub.is_active_now():
        messages.info(request, "Votre abonnement est déjà actif.")
        return redirect("subscriptions:my_subscription")

    payment = SubscriptionPayment.objects.create(
        subscription=sub,
        amount=sub.monthly_amount,
        provider=SubscriptionPayment.PROVIDER_CARD,
        reference=f"SUB-{secrets.token_hex(4).upper()}",
    )
    return redirect("subscriptions:payment_sandbox", payment_id=payment.id)


@login_required
def payment_sandbox(request, payment_id: int):
    """Sandbox simulée pour régler un abonnement."""
    payment = get_object_or_404(SubscriptionPayment, id=payment_id)
    sub = payment.subscription

    # Sécurité : seul le propriétaire peut régler
    owner = sub.owner_profile
    if not owner or owner.owner_id != request.user.id:
        raise Http404

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "success":
            payment.mark_success()
            messages.success(request, "Paiement validé ! Votre abonnement est actif.")
            return redirect("subscriptions:payment_success", payment_id=payment.id)
        if action == "fail":
            payment.mark_failed("Paiement refusé (simulation)")
            messages.error(request, "Le paiement a échoué. Vous pouvez réessayer.")
            return redirect("subscriptions:my_subscription")

    return render(
        request,
        "subscriptions/payment_sandbox.html",
        {"payment": payment, "subscription": sub},
    )


@login_required
def payment_success(request, payment_id: int):
    payment = get_object_or_404(SubscriptionPayment, id=payment_id)
    sub = payment.subscription
    owner = sub.owner_profile
    if not owner or owner.owner_id != request.user.id:
        raise Http404
    return render(
        request,
        "subscriptions/payment_success.html",
        {"payment": payment, "subscription": sub},
    )


# ---------------------------------------------------------------------------
# Administration
# ---------------------------------------------------------------------------
@login_required
def admin_list(request):
    _ensure_admin(request.user)
    status = request.GET.get("status") or ""
    q = request.GET.get("q", "").strip()

    qs = Subscription.objects.select_related(
        "plan", "vendor", "service_provider", "vendor__owner", "service_provider__owner"
    )
    if status and status in dict(Subscription.STATUS_CHOICES):
        qs = qs.filter(status=status)
    if q:
        qs = qs.filter(
            Q(vendor__name__icontains=q)
            | Q(service_provider__name__icontains=q)
            | Q(vendor__owner__username__icontains=q)
            | Q(service_provider__owner__username__icontains=q)
        )

    stats = Subscription.objects.aggregate(
        total=Count("id"),
        active=Count("id", filter=Q(status=Subscription.STATUS_ACTIVE)),
        pending=Count("id", filter=Q(status=Subscription.STATUS_PENDING)),
        past_due=Count("id", filter=Q(status=Subscription.STATUS_PAST_DUE)),
        monthly_revenue=Sum(
            "monthly_amount", filter=Q(status=Subscription.STATUS_ACTIVE)
        ),
    )

    return render(
        request,
        "subscriptions/admin/list.html",
        {
            "subscriptions": qs.order_by("-updated_at"),
            "stats": stats,
            "status": status,
            "q": q,
            "status_choices": Subscription.STATUS_CHOICES,
        },
    )


@login_required
def admin_set_amount(request, kind: str, target_id: int):
    """Admin fixe le montant mensuel pour un vendeur ou prestataire."""
    _ensure_admin(request.user)

    if kind == "vendor":
        target = get_object_or_404(Vendor, id=target_id)
        form_target = "vendor"
        sub = getattr(target, "subscription", None)
    elif kind == "provider":
        target = get_object_or_404(ServiceProvider, id=target_id)
        form_target = "provider"
        sub = getattr(target, "subscription", None)
    else:
        raise Http404

    initial = {}
    if sub:
        initial["plan"] = sub.plan
        initial["monthly_amount"] = sub.monthly_amount
        initial["admin_note"] = sub.admin_note

    if request.method == "POST":
        form = AdminSetAmountForm(request.POST, target=form_target)
        if form.is_valid():
            plan = form.cleaned_data["plan"]
            amount = form.cleaned_data["monthly_amount"]
            note = form.cleaned_data["admin_note"]

            if kind == "vendor":
                sub = get_or_create_subscription_for_vendor(
                    target, monthly_amount=amount, plan=plan
                )
            else:
                sub = get_or_create_subscription_for_provider(
                    target, monthly_amount=amount, plan=plan
                )
            sub.plan = plan
            sub.monthly_amount = amount
            sub.admin_note = note
            # Si l'abonnement était annulé, on repasse en pending
            if sub.status == Subscription.STATUS_CANCELLED:
                sub.status = Subscription.STATUS_PENDING
            sub.save()
            messages.success(
                request,
                f"Montant mensuel mis à jour : {amount} FCFA"
                + (f" ({plan.name})" if plan else " (personnalisé)"),
            )
            return redirect("subscriptions:admin_list")
    else:
        form = AdminSetAmountForm(initial=initial, target=form_target)

    return render(
        request,
        "subscriptions/admin/set_amount.html",
        {
            "form": form,
            "target": target,
            "kind": kind,
            "subscription": sub,
        },
    )


@login_required
@require_POST
def admin_mark_paid(request, subscription_id: int):
    """Admin valide manuellement un paiement (ex: virement)."""
    _ensure_admin(request.user)
    sub = get_object_or_404(Subscription, id=subscription_id)

    if not sub.monthly_amount:
        messages.error(request, "Fixez d'abord le montant mensuel.")
        return redirect("subscriptions:admin_list")

    payment = SubscriptionPayment.objects.create(
        subscription=sub,
        amount=sub.monthly_amount,
        provider=SubscriptionPayment.PROVIDER_MANUAL,
    )
    payment.mark_success()
    messages.success(request, f"Abonnement de {sub.owner_name} activé manuellement.")
    return redirect("subscriptions:admin_list")


@login_required
@require_POST
def admin_cancel(request, subscription_id: int):
    _ensure_admin(request.user)
    sub = get_object_or_404(Subscription, id=subscription_id)
    sub.status = Subscription.STATUS_CANCELLED
    sub.cancelled_at = timezone.now()
    sub.save(update_fields=["status", "cancelled_at", "updated_at"])
    messages.warning(request, f"Abonnement de {sub.owner_name} annulé.")
    return redirect("subscriptions:admin_list")


# ---------- Plans CRUD ----------
@login_required
def admin_plans(request):
    _ensure_admin(request.user)
    plans = SubscriptionPlan.objects.all().order_by("display_order", "monthly_amount")
    return render(request, "subscriptions/admin/plans.html", {"plans": plans})


@login_required
def admin_plan_edit(request, plan_id: int | None = None):
    _ensure_admin(request.user)
    plan = get_object_or_404(SubscriptionPlan, id=plan_id) if plan_id else None
    if request.method == "POST":
        form = SubscriptionPlanForm(request.POST, instance=plan)
        if form.is_valid():
            form.save()
            messages.success(request, "Formule enregistrée.")
            return redirect("subscriptions:admin_plans")
    else:
        form = SubscriptionPlanForm(instance=plan)
    return render(
        request,
        "subscriptions/admin/plan_form.html",
        {"form": form, "plan": plan},
    )


@login_required
@require_POST
def admin_plan_delete(request, plan_id: int):
    _ensure_admin(request.user, super_only=True)
    plan = get_object_or_404(SubscriptionPlan, id=plan_id)
    plan.delete()
    messages.success(request, "Formule supprimée.")
    return redirect("subscriptions:admin_plans")
