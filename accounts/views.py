import json
from django.contrib.auth import login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.core.exceptions import PermissionDenied
from django.db.models import Count, DecimalField, ExpressionWrapper, F, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from marketplace.models import ServiceProvider, Vendor
from orders.models import Order
from .email_utils import get_user_from_token, send_verification_email
from .forms import ProfileForm, SignupForm
from .models import UserProfile


def signup(request):
    if request.method == "POST":
        form = SignupForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            user.is_active = False
            user.save()
            try:
                send_verification_email(request, user)
            except Exception as e:
                import traceback
                traceback.print_exc()
                messages.error(
                    request,
                    "L'email de vérification n'a pas pu être envoyé. Vérifiez le fichier .env (EMAIL_HOST_USER, EMAIL_HOST_PASSWORD) et la console du serveur pour les détails.",
                )
                return redirect("accounts:signup_email_sent")
            return redirect("accounts:signup_email_sent")
        messages.error(
            request,
            "L'inscription n'a pas abouti. Veuillez corriger les erreurs indiquées ci-dessous.",
        )
    else:
        form = SignupForm()
    return render(request, "accounts/signup.html", {"form": form})


def signup_email_sent(request):
    """Page affichée après inscription : indique de vérifier sa boîte mail."""
    return render(request, "accounts/signup_email_sent.html")


def verify_email(request):
    """Active le compte après clic sur le lien reçu par email."""
    token = request.GET.get("token")
    if not token:
        messages.error(request, "Lien de vérification invalide.")
        return redirect("accounts:login")
    user, err = get_user_from_token(token)
    if err:
        messages.error(request, err)
        return redirect("accounts:login")
    if user.is_active:
        messages.success(
            request,
            "Ce compte est déjà activé. Vous pouvez vous connecter.",
        )
        return redirect("accounts:login")
    user.is_active = True
    user.save()
    messages.success(
        request,
        "Votre adresse email a été confirmée. Vous pouvez maintenant vous connecter.",
    )
    return redirect("accounts:login")


@login_required
def profile(request):
    profile_obj, _ = UserProfile.objects.get_or_create(user=request.user)
    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=profile_obj)
        if form.is_valid():
            form.save()
            return redirect("accounts:profile")
    else:
        form = ProfileForm(instance=profile_obj)
    return render(request, "accounts/profile.html", {"form": form})


def _is_client(user):
    """True si l'utilisateur est un client (ni admin, ni vendeur, ni prestataire)."""
    if not user or not user.is_authenticated:
        return False
    if Vendor.objects.filter(owner=user).exists():
        return False
    if ServiceProvider.objects.filter(owner=user).exists():
        return False
    profile, _ = UserProfile.objects.get_or_create(user=user)
    if profile.role in (UserProfile.ROLE_ADMIN, UserProfile.ROLE_SUPER_ADMIN):
        return False
    if getattr(user, "is_superuser", False):
        return False
    return True


@login_required
def order_history(request):
    if not _is_client(request.user):
        return redirect("accounts:profile")
    orders = Order.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "accounts/orders.html", {"orders": orders})


def _ensure_admin(request, super_only=False):
    """
    Vérifie que l'utilisateur est admin ou super admin de l'application.
    super_only=True : uniquement super admin.
    """
    if not request.user.is_authenticated:
        raise PermissionDenied
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    role = getattr(profile, "role", UserProfile.ROLE_CUSTOMER)
    if request.user.is_superuser:
        return profile
    if super_only:
        if role == UserProfile.ROLE_SUPER_ADMIN:
            return profile
        raise PermissionDenied
    if role in (UserProfile.ROLE_ADMIN, UserProfile.ROLE_SUPER_ADMIN):
        return profile
    raise PermissionDenied


PAGE_SIZE = 10


@login_required
def admin_dashboard(request):
    profile = _ensure_admin(request, super_only=False)
    vendors_pending_qs = Vendor.objects.filter(
        verification_status=Vendor.STATUS_PENDING
    ).select_related("owner").order_by("-id")
    providers_pending_qs = ServiceProvider.objects.filter(
        verification_status=ServiceProvider.STATUS_PENDING
    ).select_related("owner").order_by("-id")

    paginator_v = Paginator(vendors_pending_qs, PAGE_SIZE)
    paginator_p = Paginator(providers_pending_qs, PAGE_SIZE)
    vendors_pending_page = paginator_v.get_page(request.GET.get("vendors_page", 1))
    providers_pending_page = paginator_p.get_page(request.GET.get("providers_page", 1))
    pending_count = vendors_pending_qs.count() + providers_pending_qs.count()

    total_vendors = Vendor.objects.filter(verification_status=Vendor.STATUS_VERIFIED).count()
    total_providers = ServiceProvider.objects.filter(verification_status=ServiceProvider.STATUS_VERIFIED).count()
    total_orders = Order.objects.exclude(status=Order.STATUS_CANCELLED).count()
    global_revenue = (
        Order.objects.exclude(status=Order.STATUS_CANCELLED).aggregate(total=Sum("total_amount"))["total"] or 0
    )

    top_vendors_qs = (
        Vendor.objects.filter(verification_status=Vendor.STATUS_VERIFIED)
        .annotate(
            revenue=Coalesce(
                Sum(
                    ExpressionWrapper(
                        F("product__order_items__unit_price") * F("product__order_items__quantity"),
                        output_field=DecimalField(),
                    ),
                    filter=Q(
                        product__order_items__order__status__in=[
                            Order.STATUS_PENDING,
                            Order.STATUS_PAID,
                            Order.STATUS_SHIPPED,
                            Order.STATUS_DONE,
                        ]
                    ),
                ),
                Value(0, output_field=DecimalField()),
            ),
            order_count=Count(
                "product__order_items__order",
                distinct=True,
                filter=Q(
                    product__order_items__order__status__in=[
                        Order.STATUS_PENDING,
                        Order.STATUS_PAID,
                        Order.STATUS_SHIPPED,
                        Order.STATUS_DONE,
                    ]
                ),
            ),
        )
        .order_by("-revenue")
    )

    top_providers_qs = (
        ServiceProvider.objects.filter(verification_status=ServiceProvider.STATUS_VERIFIED)
        .annotate(
            request_count=Count("servicerequest"),
            approved_count=Count(
                "servicerequest", filter=Q(servicerequest__status="approved")
            ),
        )
        .order_by("-approved_count", "-request_count")
    )

    paginator_top_v = Paginator(top_vendors_qs, PAGE_SIZE)
    paginator_top_p = Paginator(top_providers_qs, PAGE_SIZE)
    top_vendors_page = paginator_top_v.get_page(request.GET.get("top_vendors_page", 1))
    top_providers_page = paginator_top_p.get_page(request.GET.get("top_providers_page", 1))

    users_page = None
    if request.user.is_superuser or profile.role == UserProfile.ROLE_SUPER_ADMIN:
        users_qs = User.objects.all().select_related("userprofile").order_by("-id")
        paginator_u = Paginator(users_qs, PAGE_SIZE)
        users_page = paginator_u.get_page(request.GET.get("users_page", 1))

    from subscriptions.models import Subscription
    sub_stats = Subscription.objects.aggregate(
        total=Count("id"),
        active=Count("id", filter=Q(status=Subscription.STATUS_ACTIVE)),
        pending=Count("id", filter=Q(status=Subscription.STATUS_PENDING)),
        past_due=Count("id", filter=Q(status=Subscription.STATUS_PAST_DUE)),
        monthly_revenue=Sum("monthly_amount", filter=Q(status=Subscription.STATUS_ACTIVE)),
    )

    return render(
        request,
        "accounts/admin_dashboard.html",
        {
            "vendors_pending_page": vendors_pending_page,
            "providers_pending_page": providers_pending_page,
            "top_vendors_page": top_vendors_page,
            "top_providers_page": top_providers_page,
            "users_page": users_page,
            "pending_count": pending_count,
            "profile": profile,
            "total_vendors": total_vendors,
            "total_providers": total_providers,
            "total_orders": total_orders,
            "global_revenue": global_revenue,
            "role_choices": UserProfile.ROLE_CHOICES,
            "sub_stats": sub_stats,
        },
    )


@login_required
def set_user_role(request, user_id):
    _ensure_admin(request, super_only=True)
    target = get_object_or_404(User, id=user_id)
    if request.method == "POST":
        role = request.POST.get("role")
        profile, _ = UserProfile.objects.get_or_create(user=target)
        valid_roles = {choice[0] for choice in UserProfile.ROLE_CHOICES}
        if role in valid_roles:
            profile.role = role
            profile.save()
    return redirect("accounts:admin_dashboard")


@login_required
def moderate_vendor(request, vendor_id, action):
    _ensure_admin(request, super_only=False)
    vendor = get_object_or_404(Vendor, id=vendor_id)
    if request.method == "POST":
        if action == "approve":
            vendor.verification_status = Vendor.STATUS_VERIFIED
            vendor.verified_at = timezone.now()
        elif action == "reject":
            vendor.verification_status = Vendor.STATUS_REJECTED
            vendor.verified_at = timezone.now()
        vendor.save()
    return redirect("accounts:admin_dashboard")


@login_required
def moderate_service_provider(request, provider_id, action):
    _ensure_admin(request, super_only=False)
    provider = get_object_or_404(ServiceProvider, id=provider_id)
    if request.method == "POST":
        if action == "approve":
            provider.verification_status = ServiceProvider.STATUS_VERIFIED
            provider.verified_at = timezone.now()
        elif action == "reject":
            provider.verification_status = ServiceProvider.STATUS_REJECTED
            provider.verified_at = timezone.now()
        provider.save()
    return redirect("accounts:admin_dashboard")


@login_required
def view_vendor_details(request, vendor_id):
    """Vue détaillée d'un vendeur pour validation admin."""
    _ensure_admin(request, super_only=False)
    vendor = get_object_or_404(Vendor, id=vendor_id)
    return render(
        request,
        "accounts/vendor_details.html",
        {"vendor": vendor},
    )


@login_required
def view_service_provider_details(request, provider_id):
    """Vue détaillée d'un prestataire pour validation admin."""
    _ensure_admin(request, super_only=False)
    provider = get_object_or_404(ServiceProvider, id=provider_id)
    return render(
        request,
        "accounts/service_provider_details.html",
        {"provider": provider},
    )
