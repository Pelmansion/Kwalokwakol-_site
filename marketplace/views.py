from django.contrib.auth import get_user_model
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, DecimalField, F, Sum
from django.shortcuts import get_object_or_404, redirect, render

from catalog.models import Product
from orders.models import OrderItem
from payments.models import Payment
from reviews.models import Review, ReviewReply
from notifications.models import Notification

from .forms import (
    OrderStatusForm,
    ProductForm,
    ServiceProductForm,
    ServiceProviderForm,
    ServiceProviderProfileForm,
    VendorForm,
    VendorProfileForm,
)
from .models import ServiceProvider, ServiceRequest, Vendor
from accounts.forms import SignupForm


# ---------------------------------------------------------------------------
# Helpers abonnement
# ---------------------------------------------------------------------------
def _vendor_gate(vendor):
    """Retourne None si l'accès est OK, sinon un redirect vers la page appropriée."""
    sub = getattr(vendor, "subscription", None)
    if not sub:
        return redirect("subscriptions:choose_plan")
    if not sub.is_active_now():
        return redirect("subscriptions:my_subscription")
    return None


def _provider_gate(provider):
    sub = getattr(provider, "subscription", None)
    if not sub:
        return redirect("subscriptions:choose_plan")
    if not sub.is_active_now():
        return redirect("subscriptions:my_subscription")
    return None


def vendor_register(request):
    """
    Inscription vendeur.
    - Si l'utilisateur est déjà connecté : il ne remplit que le formulaire vendeur.
    - S'il n'est pas connecté : il crée en même temps un compte utilisateur + sa fiche vendeur.
    """
    if request.user.is_authenticated and Vendor.objects.filter(owner=request.user).exists():
        return redirect("marketplace:dashboard")

    signup_form = None

    if request.method == "POST":
        if request.user.is_authenticated:
            form = VendorForm(request.POST, request.FILES)
            if form.is_valid():
                vendor = form.save(commit=False)
                vendor.owner = request.user
                vendor.save()
                messages.success(
                    request,
                    "Profil vendeur créé. Choisissez une formule pour finaliser votre inscription.",
                )
                return redirect("subscriptions:choose_plan")
            messages.error(
                request,
                "L'inscription n'a pas abouti. Veuillez corriger les erreurs indiquées ci-dessous.",
            )
        else:
            signup_form = SignupForm(request.POST, request.FILES)
            form = VendorForm(request.POST, request.FILES)
            if signup_form.is_valid() and form.is_valid():
                user = signup_form.save()
                login(request, user)
                vendor = form.save(commit=False)
                vendor.owner = user
                vendor.save()
                messages.success(
                    request,
                    "Compte et profil vendeur créés. Choisissez une formule pour finaliser votre inscription.",
                )
                return redirect("subscriptions:choose_plan")
            messages.error(
                request,
                "L'inscription n'a pas abouti. Veuillez corriger les erreurs indiquées ci-dessous.",
            )
    else:
        form = VendorForm()
        if not request.user.is_authenticated:
            signup_form = SignupForm()

    context = {
        "form": form,
        "signup_form": signup_form,
    }
    return render(request, "marketplace/vendor_register.html", context)


@login_required
def dashboard(request):
    vendor = Vendor.objects.filter(owner=request.user).first()
    if not vendor:
        return redirect("marketplace:vendor_register")

    gate = _vendor_gate(vendor)
    if gate is not None:
        return gate

    products = Product.objects.filter(vendor=vendor, kind=Product.PRODUCT)
    order_items = (
        OrderItem.objects.filter(product__vendor=vendor)
        .select_related("order", "product")
        .order_by("-order__created_at")
    )
    service_requests = ServiceRequest.objects.filter(vendor=vendor).select_related(
        "service", "customer"
    )
    revenue = order_items.aggregate(
        total=Sum(F("unit_price") * F("quantity"), output_field=DecimalField())
    )["total"] or 0
    total_orders = order_items.values("order_id").distinct().count()
    total_products = products.count()
    recent_reviews = (
        Review.objects.filter(product__vendor=vendor, is_approved=True)
        .select_related("product", "user")
        .order_by("-created_at")[:6]
    )

    top_clients_data = (
        OrderItem.objects.filter(product__vendor=vendor)
        .exclude(order__user__isnull=True)
        .values("order__user")
        .annotate(
            total=Sum(F("unit_price") * F("quantity")),
            order_count=Count("order", distinct=True),
        )
        .order_by("-total")[:10]
    )
    user_ids = [d["order__user"] for d in top_clients_data if d["order__user"]]
    User = get_user_model()
    users_map = {u.id: u for u in User.objects.filter(id__in=user_ids)} if user_ids else {}
    top_clients = [
        {"user": users_map.get(d["order__user"]), "total": d["total"], "order_count": d["order_count"]}
        for d in top_clients_data
    ]
    max_client_total = max((c["total"] or 0 for c in top_clients), default=1)

    return render(
        request,
        "marketplace/dashboard.html",
        {
            "vendor": vendor,
            "subscription": vendor.subscription,
            "products": products,
            "order_items": order_items,
            "revenue": revenue,
            "total_orders": total_orders,
            "total_products": total_products,
            "recent_reviews": recent_reviews,
            "service_requests": service_requests,
            "top_clients": top_clients,
            "max_client_total": max_client_total,
        },
    )


@login_required
def add_product(request):
    vendor = Vendor.objects.filter(owner=request.user).first()
    if not vendor:
        return redirect("marketplace:vendor_register")
    gate = _vendor_gate(vendor)
    if gate is not None:
        return gate
    if request.method == "POST":
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save(commit=False)
            product.vendor = vendor
            product.save()
            return redirect("marketplace:dashboard")
    else:
        form = ProductForm()
    return render(request, "marketplace/product_form.html", {"form": form})


@login_required
def edit_product(request, product_id):
    vendor = Vendor.objects.filter(owner=request.user).first()
    if not vendor:
        return redirect("marketplace:vendor_register")
    gate = _vendor_gate(vendor)
    if gate is not None:
        return gate
    product = get_object_or_404(Product, id=product_id, vendor=vendor)
    if request.method == "POST":
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            return redirect("marketplace:dashboard")
    else:
        form = ProductForm(instance=product)
    return render(
        request, "marketplace/product_form.html", {"form": form, "product": product}
    )


@login_required
def delete_product(request, product_id):
    vendor = Vendor.objects.filter(owner=request.user).first()
    if not vendor:
        return redirect("marketplace:vendor_register")
    gate = _vendor_gate(vendor)
    if gate is not None:
        return gate
    product = get_object_or_404(Product, id=product_id, vendor=vendor)
    if request.method == "POST":
        product.delete()
        return redirect("marketplace:dashboard")
    return render(
        request,
        "marketplace/product_delete.html",
        {"product": product, "vendor": vendor},
    )


@login_required
def vendor_profile(request):
    vendor = Vendor.objects.filter(owner=request.user).first()
    if not vendor:
        return redirect("marketplace:vendor_register")
    gate = _vendor_gate(vendor)
    if gate is not None:
        return gate
    if request.method == "POST":
        form = VendorProfileForm(request.POST, instance=vendor)
        if form.is_valid():
            form.save()
            return redirect("marketplace:dashboard")
    else:
        form = VendorProfileForm(instance=vendor)
    return render(request, "marketplace/vendor_profile.html", {"form": form})


@login_required
def update_order_status(request, order_id):
    vendor = Vendor.objects.filter(owner=request.user).first()
    if not vendor:
        return redirect("marketplace:vendor_register")
    gate = _vendor_gate(vendor)
    if gate is not None:
        return gate
    order_item = (
        OrderItem.objects.filter(order_id=order_id, product__vendor=vendor)
        .select_related("order")
        .first()
    )
    if not order_item:
        return redirect("marketplace:dashboard")
    if request.method == "POST":
        form = OrderStatusForm(request.POST, instance=order_item.order)
        if form.is_valid():
            form.save()
    return redirect("marketplace:dashboard")


@login_required
def reply_review(request, review_id):
    vendor = Vendor.objects.filter(owner=request.user).first()
    if not vendor:
        return redirect("marketplace:vendor_register")
    gate = _vendor_gate(vendor)
    if gate is not None:
        return gate
    review = get_object_or_404(Review, id=review_id, product__vendor=vendor)
    if request.method == "POST":
        message = request.POST.get("message", "").strip()
        if message:
            ReviewReply.objects.update_or_create(
                review=review, defaults={"vendor": vendor, "message": message}
            )
    return redirect("marketplace:dashboard")


@login_required
def vendor_payments(request):
    vendor = Vendor.objects.filter(owner=request.user).first()
    if not vendor:
        return redirect("marketplace:vendor_register")
    gate = _vendor_gate(vendor)
    if gate is not None:
        return gate
    order_ids = (
        OrderItem.objects.filter(product__vendor=vendor)
        .values_list("order_id", flat=True)
        .distinct()
    )
    payments = Payment.objects.filter(order_id__in=order_ids).select_related("order")
    total_paid = payments.filter(status=Payment.STATUS_SUCCESS).aggregate(
        total=Sum("amount")
    )["total"] or 0
    return render(
        request,
        "marketplace/payments.html",
        {"payments": payments, "total_paid": total_paid, "vendor": vendor},
    )


@login_required
def vendor_settings(request):
    vendor = Vendor.objects.filter(owner=request.user).first()
    if not vendor:
        return redirect("marketplace:vendor_register")
    gate = _vendor_gate(vendor)
    if gate is not None:
        return gate
    return render(request, "marketplace/settings.html", {"vendor": vendor})


def service_provider_register(request):
    """
    Inscription prestataire de services.
    """
    if request.user.is_authenticated and ServiceProvider.objects.filter(owner=request.user).exists():
        return redirect("marketplace:service_provider_dashboard")

    signup_form = None

    if request.method == "POST":
        if request.user.is_authenticated:
            form = ServiceProviderForm(request.POST, request.FILES)
            if form.is_valid():
                provider = form.save(commit=False)
                provider.owner = request.user
                provider.save()
                messages.success(
                    request,
                    "Profil prestataire créé. Choisissez une formule pour finaliser votre inscription.",
                )
                return redirect("subscriptions:choose_plan")
            messages.error(
                request,
                "L'inscription n'a pas abouti. Veuillez corriger les erreurs indiquées ci-dessous.",
            )
        else:
            signup_form = SignupForm(request.POST, request.FILES)
            form = ServiceProviderForm(request.POST, request.FILES)
            if signup_form.is_valid() and form.is_valid():
                user = signup_form.save()
                login(request, user)
                provider = form.save(commit=False)
                provider.owner = user
                provider.save()
                messages.success(
                    request,
                    "Compte et profil prestataire créés. Choisissez une formule pour finaliser votre inscription.",
                )
                return redirect("subscriptions:choose_plan")
            messages.error(
                request,
                "L'inscription n'a pas abouti. Veuillez corriger les erreurs indiquées ci-dessous.",
            )
    else:
        form = ServiceProviderForm()
        if not request.user.is_authenticated:
            signup_form = SignupForm()

    context = {
        "form": form,
        "signup_form": signup_form,
    }
    return render(request, "marketplace/service_provider_register.html", context)


@login_required
def service_provider_dashboard(request):
    service_provider = ServiceProvider.objects.filter(owner=request.user).first()
    if not service_provider:
        return redirect("marketplace:service_provider_register")
    gate = _provider_gate(service_provider)
    if gate is not None:
        return gate

    services = Product.objects.filter(service_provider=service_provider, is_active=True)
    service_requests = ServiceRequest.objects.filter(
        service_provider=service_provider
    ).select_related("service", "customer").order_by("-created_at")[:5]

    total_requests = ServiceRequest.objects.filter(service_provider=service_provider).count()
    pending_requests = ServiceRequest.objects.filter(
        service_provider=service_provider, status=ServiceRequest.STATUS_PENDING
    ).count()

    return render(
        request,
        "marketplace/service_provider_dashboard.html",
        {
            "service_provider": service_provider,
            "subscription": service_provider.subscription,
            "services": services,
            "service_requests": service_requests,
            "total_requests": total_requests,
            "pending_requests": pending_requests,
        },
    )


@login_required
def service_provider_profile(request):
    service_provider = ServiceProvider.objects.filter(owner=request.user).first()
    if not service_provider:
        return redirect("marketplace:service_provider_register")
    gate = _provider_gate(service_provider)
    if gate is not None:
        return gate
    if request.method == "POST":
        form = ServiceProviderProfileForm(request.POST, instance=service_provider)
        if form.is_valid():
            form.save()
            return redirect("marketplace:service_provider_dashboard")
    else:
        form = ServiceProviderProfileForm(instance=service_provider)
    return render(
        request,
        "marketplace/service_provider_profile.html",
        {"form": form},
    )


@login_required
def add_service(request):
    service_provider = ServiceProvider.objects.filter(owner=request.user).first()
    if not service_provider:
        return redirect("marketplace:service_provider_register")
    gate = _provider_gate(service_provider)
    if gate is not None:
        return gate
    if request.method == "POST":
        form = ServiceProductForm(request.POST)
        if form.is_valid():
            product = form.save(commit=False)
            product.service_provider = service_provider
            product.kind = Product.SERVICE
            product.stock = 0
            product.save()
            return redirect("marketplace:service_provider_dashboard")
    else:
        form = ServiceProductForm()
    return render(
        request, "marketplace/service_product_form.html", {"form": form}
    )


@login_required
def update_service_request(request, request_id, action):
    if request.method != "POST":
        return redirect("store:home")
    service_request = ServiceRequest.objects.filter(id=request_id).select_related(
        "service", "customer", "vendor", "service_provider"
    ).first()
    if not service_request:
        return redirect("marketplace:dashboard")

    vendor = Vendor.objects.filter(owner=request.user).first()
    service_provider = ServiceProvider.objects.filter(owner=request.user).first()
    if vendor:
        gate = _vendor_gate(vendor)
        if gate is not None:
            return gate
    if service_provider:
        gate = _provider_gate(service_provider)
        if gate is not None:
            return gate
    if vendor and service_request.vendor_id != vendor.id:
        return redirect("marketplace:dashboard")
    if service_provider and service_request.service_provider_id != service_provider.id:
        return redirect("marketplace:service_provider_dashboard")
    if not vendor and not service_provider:
        return redirect("store:home")

    if action == "approve":
        service_request.status = ServiceRequest.STATUS_APPROVED
    elif action == "reject":
        service_request.status = ServiceRequest.STATUS_REJECTED
    else:
        return redirect("store:home")
    service_request.save()

    Notification.objects.create(
        user=service_request.customer,
        title="Mise à jour de votre demande",
        body=(
            f"Votre demande pour {service_request.service.name} a été "
            f"{'validée' if action == 'approve' else 'refusée'}."
        ),
        kind=Notification.INFO,
    )

    if vendor:
        return redirect("marketplace:dashboard")
    return redirect("marketplace:service_provider_dashboard")


@login_required
def service_requests_list(request):
    """Vue dédiée pour voir toutes les demandes de services."""
    service_provider = ServiceProvider.objects.filter(owner=request.user).first()
    if not service_provider:
        return redirect("marketplace:service_provider_register")
    gate = _provider_gate(service_provider)
    if gate is not None:
        return gate

    status_filter = request.GET.get("statut", "")
    service_requests = ServiceRequest.objects.filter(
        service_provider=service_provider
    ).select_related("service", "customer").order_by("-created_at")

    if status_filter:
        service_requests = service_requests.filter(status=status_filter)

    total = ServiceRequest.objects.filter(service_provider=service_provider).count()
    pending = ServiceRequest.objects.filter(
        service_provider=service_provider, status=ServiceRequest.STATUS_PENDING
    ).count()
    approved = ServiceRequest.objects.filter(
        service_provider=service_provider, status=ServiceRequest.STATUS_APPROVED
    ).count()
    rejected = ServiceRequest.objects.filter(
        service_provider=service_provider, status=ServiceRequest.STATUS_REJECTED
    ).count()

    return render(
        request,
        "marketplace/service_requests_list.html",
        {
            "service_provider": service_provider,
            "service_requests": service_requests,
            "status_filter": status_filter,
            "stats": {
                "total": total,
                "pending": pending,
                "approved": approved,
                "rejected": rejected,
            },
        },
    )
