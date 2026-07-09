from django.contrib.auth import get_user_model
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, DecimalField, F, Max, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render

from catalog.models import Category, CategoryShowcaseImage, Product
from catalog.category_utils import resolve_product_category
from orders.models import Order, OrderItem
from payments.models import Payment
from reviews.models import Review, ReviewReply
from notifications.models import Notification

from .forms import (
    CategoryShowcaseImageForm,
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


def _assign_vendor_product_category(product, form, vendor):
    new_name = (form.cleaned_data.get("new_category") or "").strip()
    if new_name:
        product.category = resolve_product_category(new_name, vendor=vendor)
    else:
        product.category = form.cleaned_data["category"]


def _assign_provider_product_category(product, form, service_provider):
    new_name = (form.cleaned_data.get("new_category") or "").strip()
    if new_name:
        product.category = resolve_product_category(
            new_name, service_provider=service_provider
        )
    else:
        product.category = form.cleaned_data["category"]


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
    order_items_qs = (
        OrderItem.objects.filter(product__vendor=vendor)
        .select_related("order", "product")
        .order_by("-order__created_at")
    )

    order_status_filter = request.GET.get("order_status", "").strip()
    payment_status_filter = request.GET.get("payment_status", "").strip()
    orders_q = request.GET.get("orders_q", "").strip()

    valid_statuses = {c[0] for c in Order.STATUS_CHOICES}
    valid_payments = {c[0] for c in Order.PAYMENT_CHOICES}
    if order_status_filter in valid_statuses:
        order_items_qs = order_items_qs.filter(order__status=order_status_filter)
    else:
        order_status_filter = ""
    if payment_status_filter in valid_payments:
        order_items_qs = order_items_qs.filter(order__payment_status=payment_status_filter)
    else:
        payment_status_filter = ""

    if orders_q:
        if orders_q.isdigit():
            order_items_qs = order_items_qs.filter(order_id=int(orders_q))
        else:
            order_items_qs = order_items_qs.filter(
                Q(product__name__icontains=orders_q)
                | Q(order__full_name__icontains=orders_q)
                | Q(order__city__icontains=orders_q)
                | Q(order__tracking_code__icontains=orders_q)
            )

    orders_query_params = request.GET.copy()
    orders_query_params.pop("orders_page", None)
    orders_query_base = orders_query_params.urlencode()

    order_items_page = Paginator(order_items_qs, 10).get_page(
        request.GET.get("orders_page", 1)
    )
    service_requests = ServiceRequest.objects.filter(vendor=vendor).select_related(
        "service", "customer"
    )
    revenue = order_items_qs.aggregate(
        total=Sum(F("unit_price") * F("quantity"), output_field=DecimalField())
    )["total"] or 0
    total_orders = order_items_qs.values("order_id").distinct().count()
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
            "order_items_page": order_items_page,
            "order_status_filter": order_status_filter,
            "payment_status_filter": payment_status_filter,
            "orders_q": orders_q,
            "orders_query_base": orders_query_base,
            "order_status_choices": Order.STATUS_CHOICES,
            "payment_status_choices": Order.PAYMENT_CHOICES,
            "orders_filters_active": bool(
                order_status_filter or payment_status_filter or orders_q
            ),
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
        form = ProductForm(request.POST, request.FILES, vendor=vendor)
        if form.is_valid():
            product = form.save(commit=False)
            product.vendor = vendor
            _assign_vendor_product_category(product, form, vendor)
            product.save()
            return redirect("marketplace:dashboard")
    else:
        form = ProductForm(vendor=vendor)
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
        form = ProductForm(request.POST, request.FILES, instance=product, vendor=vendor)
        if form.is_valid():
            product = form.save(commit=False)
            _assign_vendor_product_category(product, form, vendor)
            product.save()
            return redirect("marketplace:dashboard")
    else:
        form = ProductForm(instance=product, vendor=vendor)
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
        form = VendorProfileForm(request.POST, request.FILES, instance=vendor)
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
        form = ServiceProviderProfileForm(
            request.POST, request.FILES, instance=service_provider
        )
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
        form = ServiceProductForm(
            request.POST, request.FILES, service_provider=service_provider
        )
        if form.is_valid():
            product = form.save(commit=False)
            product.service_provider = service_provider
            product.kind = Product.SERVICE
            product.stock = 0
            _assign_provider_product_category(product, form, service_provider)
            product.save()
            return redirect("marketplace:service_provider_dashboard")
    else:
        form = ServiceProductForm(service_provider=service_provider)
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


SHOWCASE_MAX_IMAGES = 8


def _showcase_owner_for_category(
    category: Category,
    vendor: Vendor | None,
    provider: ServiceProvider | None,
) -> tuple[Vendor | None, ServiceProvider | None]:
    if category.vendor_id:
        return category.vendor, None
    if category.service_provider_id:
        return None, category.service_provider
    if vendor:
        return vendor, None
    if provider:
        return None, provider
    return None, None


def _vendor_or_provider_can_manage_showcase(
    category: Category,
    *,
    vendor: Vendor | None = None,
    provider: ServiceProvider | None = None,
) -> bool:
    if category.vendor_id and vendor and category.vendor_id == vendor.id:
        return True
    if (
        category.service_provider_id
        and provider
        and category.service_provider_id == provider.id
    ):
        return True
    if not category.vendor_id and not category.service_provider_id:
        if vendor and Product.objects.filter(vendor=vendor, category=category).exists():
            return True
        if provider and Product.objects.filter(service_provider=provider, category=category).exists():
            return True
    return False


def _showcase_qs_for_editor(
    category: Category,
    vendor: Vendor | None,
    provider: ServiceProvider | None,
):
    own_v, own_p = _showcase_owner_for_category(category, vendor, provider)
    if own_v:
        return CategoryShowcaseImage.objects.filter(category=category, vendor=own_v)
    if own_p:
        return CategoryShowcaseImage.objects.filter(category=category, service_provider=own_p)
    return CategoryShowcaseImage.objects.none()


@login_required
def showcase_hub(request):
    vendor = Vendor.objects.filter(owner=request.user).first()
    provider = ServiceProvider.objects.filter(owner=request.user).first()
    if vendor and provider:
        messages.error(
            request,
            "Utilisez un compte dédié (boutique ou prestataire) pour gérer les photos vitrine.",
        )
        return redirect("store:home")
    if vendor:
        gate = _vendor_gate(vendor)
        if gate is not None:
            return gate
        cat_ids = set(
            Product.objects.filter(vendor=vendor)
            .exclude(category_id=None)
            .values_list("category_id", flat=True)
        ) | set(Category.objects.filter(vendor=vendor).values_list("id", flat=True))
        categories = Category.objects.filter(id__in=cat_ids, is_active=True).order_by("name")
        rows = []
        for cat in categories:
            if not _vendor_or_provider_can_manage_showcase(cat, vendor=vendor):
                continue
            rows.append({"category": cat, "count": _showcase_qs_for_editor(cat, vendor, None).count()})
        return render(
            request,
            "marketplace/showcase_hub.html",
            {"rows": rows, "role_vendor": True, "showcase_max": SHOWCASE_MAX_IMAGES},
        )
    if provider:
        gate = _provider_gate(provider)
        if gate is not None:
            return gate
        cat_ids = set(
            Product.objects.filter(service_provider=provider)
            .exclude(category_id=None)
            .values_list("category_id", flat=True)
        ) | set(Category.objects.filter(service_provider=provider).values_list("id", flat=True))
        categories = Category.objects.filter(id__in=cat_ids, is_active=True).order_by("name")
        rows = []
        for cat in categories:
            if not _vendor_or_provider_can_manage_showcase(cat, provider=provider):
                continue
            rows.append({"category": cat, "count": _showcase_qs_for_editor(cat, None, provider).count()})
        return render(
            request,
            "marketplace/showcase_hub.html",
            {"rows": rows, "role_vendor": False, "showcase_max": SHOWCASE_MAX_IMAGES},
        )
    return redirect("store:home")


@login_required
def showcase_manage(request, category_id: int):
    vendor = Vendor.objects.filter(owner=request.user).first()
    provider = ServiceProvider.objects.filter(owner=request.user).first()
    if not vendor and not provider:
        return redirect("store:home")

    category = get_object_or_404(Category, id=category_id, is_active=True)

    if vendor:
        gate = _vendor_gate(vendor)
        if gate is not None:
            return gate
        if not _vendor_or_provider_can_manage_showcase(category, vendor=vendor):
            messages.error(request, "Vous ne pouvez pas gérer la vitrine pour cette catégorie.")
            return redirect("marketplace:showcase_hub")
        owner_v, owner_p = _showcase_owner_for_category(category, vendor, None)
        qs = _showcase_qs_for_editor(category, vendor, None)
    else:
        gate = _provider_gate(provider)
        if gate is not None:
            return gate
        if not _vendor_or_provider_can_manage_showcase(category, provider=provider):
            messages.error(request, "Vous ne pouvez pas gérer la vitrine pour cette catégorie.")
            return redirect("marketplace:showcase_hub")
        owner_v, owner_p = _showcase_owner_for_category(category, None, provider)
        qs = _showcase_qs_for_editor(category, None, provider)

    form = CategoryShowcaseImageForm()
    if request.method == "POST":
        del_id = request.POST.get("delete_id")
        if del_id:
            img = get_object_or_404(qs, pk=int(del_id))
            img.delete()
            messages.success(request, "Image supprimée.")
            return redirect("marketplace:showcase_manage", category_id=category.id)
        form = CategoryShowcaseImageForm(request.POST, request.FILES)
        if qs.count() >= SHOWCASE_MAX_IMAGES:
            messages.error(
                request,
                f"Limite de {SHOWCASE_MAX_IMAGES} photos atteinte pour cette catégorie.",
            )
            form = CategoryShowcaseImageForm()
        elif form.is_valid():
            next_pos = qs.aggregate(m=Max("position"))["m"]
            pos = (next_pos if next_pos is not None else -1) + 1
            inst = form.save(commit=False)
            inst.category = category
            inst.vendor = owner_v
            inst.service_provider = owner_p
            inst.position = pos
            inst.save()
            messages.success(request, "Photo ajoutée à la vitrine.")
            return redirect("marketplace:showcase_manage", category_id=category.id)

    return render(
        request,
        "marketplace/showcase_manage.html",
        {
            "category": category,
            "images": qs.order_by("position", "id"),
            "form": form,
            "max_showcase": SHOWCASE_MAX_IMAGES,
            "can_add": qs.count() < SHOWCASE_MAX_IMAGES,
        },
    )
