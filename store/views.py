from decimal import Decimal

from django.db.models import Avg, Count, Q
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.http import JsonResponse

from .forms import OrderForm, ServiceRequestForm
from accounts.models import UserProfile
from catalog.models import Category, Product
from content.models import HomepageBackground
from marketplace.models import ServiceProvider, ServiceRequest, Vendor
from notifications.models import Notification
from orders.models import Order, OrderItem
from store.delivery import cart_delivery_fee
from payments.genius import (
    GeniusPaymentError,
    create_checkout_payment,
    is_configured as genius_is_configured,
)
from payments.models import Payment
from reviews.models import Review
from subscriptions.utils import active_product_filter, active_subscription_q


DEFAULT_CATEGORIES = [
    "Alimentation",
    "Métiers du bâtiment",
    "Production",
    "Services artisanaux",
    "Électroménager",
    "Boutiques",
    "Produits vivriers",
    "Outils numériques",
]


def _cart_pricing_context(products_for_fees, subtotal_dec: Decimal) -> dict:
    """Frais et totaux TTC (livraison = somme des tarifs des vendeurs / prestataires concernés)."""
    fee_std = cart_delivery_fee(products_for_fees, delivery_option=Order.DELIVERY_STANDARD)
    fee_exp = cart_delivery_fee(products_for_fees, delivery_option=Order.DELIVERY_EXPRESS)
    return {
        "delivery_fee_standard": fee_std,
        "delivery_fee_express": fee_exp,
        "grand_total_standard": subtotal_dec + fee_std,
        "grand_total_express": subtotal_dec + fee_exp,
    }


def _get_favorites(session):
    """
    Retourne la liste des IDs de produits en favoris stockés en session.
    Toujours une liste d'entiers propre.
    """
    raw = session.get("favorites", [])
    favorites = []
    if isinstance(raw, dict):
        raw = raw.keys()
    for value in raw:
        try:
            favorites.append(int(value))
        except (TypeError, ValueError):
            continue
    session["favorites"] = favorites
    return favorites


def _get_cart(session):
    cart = session.get("cart", {})
    session["cart"] = cart
    return cart


def _get_vendor(user):
    if not user.is_authenticated:
        return None
    return Vendor.objects.filter(owner=user).first()


def _get_service_provider(user):
    if not user.is_authenticated:
        return None
    return ServiceProvider.objects.filter(owner=user).first()


def _is_app_admin(user):
    """True si l'utilisateur est admin ou super admin (ne peut pas passer commande)."""
    if not user or not user.is_authenticated:
        return False
    if getattr(user, "is_superuser", False):
        return True
    try:
        profile = user.userprofile
    except UserProfile.DoesNotExist:
        return False
    return profile.role in (UserProfile.ROLE_ADMIN, UserProfile.ROLE_SUPER_ADMIN)


def home(request):
    # Admin, vendeur et prestataire n'ont pas d'accueil boutique : redirection vers leur espace
    if request.user.is_authenticated:
        vendor = _get_vendor(request.user)
        service_provider = _get_service_provider(request.user)
        if vendor:
            return redirect("marketplace:dashboard")
        if service_provider:
            return redirect("marketplace:service_provider_dashboard")
        if _is_app_admin(request.user):
            return redirect("accounts:admin_dashboard")

    categories = Category.objects.filter(
        is_active=True,
        parent__isnull=True,
        vendor__isnull=True,
        service_provider__isnull=True,
    )
    vendor = _get_vendor(request.user)
    service_provider = _get_service_provider(request.user)
    favorites = _get_favorites(request.session)
    base_products = (
        Product.objects.filter(is_active=True)
        .filter(active_product_filter())
        .prefetch_related("media")
    )
    if vendor:
        base_products = base_products.filter(vendor=vendor)
    elif service_provider:
        base_products = base_products.filter(service_provider=service_provider)

    # Produits mis en avant (utilisés pour la section \"Ventes flash\")
    products = base_products[:12]

    # Quelques produits par catégorie pour la page d'accueil
    category_sections = []
    for category in categories:
        cat_products = (
            base_products.filter(category=category)
            .select_related("category")[:8]
        )
        if cat_products:
            category_sections.append(
                {
                    "category": category,
                    "products": list(cat_products),
                }
            )
    if not categories.exists():
        categories = DEFAULT_CATEGORIES
    react_products = []
    for product in products[:4]:
        media = product.media.first()
        image = media.url if media else (product.image_url or "")
        react_products.append(
            {
                "id": product.id,
                "name": product.name,
                "price": float(product.price),
                "image": image,
                "url": reverse("store:product_detail", args=[product.slug]),
            }
        )
    react_data = {
        "title": "Explorez les meilleures offres locales",
        "subtitle": "Produits et services artisanaux, livraison rapide et paiement sécurisé.",
        "highlights": [
            {"title": "Paiement sécurisé", "subtitle": "Carte & Mobile Money"},
            {"title": "Artisans vérifiés", "subtitle": "Qualité garantie"},
            {"title": "Livraison 24h", "subtitle": "Disponible localement"},
        ],
        "products": react_products,
    }
    return render(
        request,
        "store/home.html",
        {
            "categories": categories,
            "products": products,
            "category_sections": category_sections,
            "react_data": react_data,
            "favorites": favorites,
            "hero_background": HomepageBackground.get_active(),
        },
    )


def product_list(request):
    query = request.GET.get("q", "").strip()
    category_slug = request.GET.get("categorie", "").strip()
    subcategory_slug = request.GET.get("sous_categorie", "").strip()
    product_type = request.GET.get("type", "").strip()
    min_price = request.GET.get("min_price")
    max_price = request.GET.get("max_price")
    location = request.GET.get("localisation", "").strip()
    availability = request.GET.get("disponible", "").strip()
    sort = request.GET.get("tri", "").strip()

    favorites = _get_favorites(request.session)
    vendor = _get_vendor(request.user)
    service_provider = _get_service_provider(request.user)
    products = (
        Product.objects.filter(is_active=True)
        .filter(active_product_filter())
        .select_related("category", "vendor", "service_provider")
    )
    if vendor:
        products = products.filter(vendor=vendor)
    elif service_provider:
        products = products.filter(service_provider=service_provider)
    if query:
        products = products.filter(Q(name__icontains=query) | Q(description__icontains=query))
    if category_slug:
        products = products.filter(category__slug=category_slug)
    if subcategory_slug:
        products = products.filter(category__slug=subcategory_slug)
    if product_type:
        products = products.filter(kind=product_type)
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)
    if location:
        products = products.filter(
            Q(location__icontains=location) | Q(vendor__location__icontains=location)
        )
    if availability == "1":
        products = products.filter(stock__gt=0)

    products = products.annotate(
        avg_rating=Avg("reviews__rating"),
        sales_count=Count("order_items"),
    )

    if sort == "price_asc":
        products = products.order_by("price")
    elif sort == "price_desc":
        products = products.order_by("-price")
    elif sort == "rating":
        products = products.order_by("-avg_rating")
    elif sort == "popular":
        products = products.order_by("-sales_count")
    subcategories = Category.objects.filter(
        parent__isnull=False,
        is_active=True,
        vendor__isnull=True,
        service_provider__isnull=True,
    )
    return render(
        request,
        "store/products.html",
        {
            "products": products,
            "subcategories": subcategories,
            "favorites": favorites,
        },
    )


def product_detail(request, slug):
    favorites = _get_favorites(request.session)
    vendor = _get_vendor(request.user)
    service_provider = _get_service_provider(request.user)
    if vendor:
        product = get_object_or_404(Product, slug=slug, is_active=True, vendor=vendor)
    elif service_provider:
        product = get_object_or_404(
            Product, slug=slug, is_active=True, service_provider=service_provider
        )
    else:
        product = get_object_or_404(Product, slug=slug, is_active=True)
    service_request = None
    if request.user.is_authenticated and product.kind == Product.SERVICE:
        service_request = ServiceRequest.objects.filter(
            service=product, customer=request.user
        ).first()
    reviews = Review.objects.filter(product=product, is_approved=True).select_related("user")
    return render(
        request,
        "store/product_detail.html",
        {
            "product": product,
            "reviews": reviews,
            "service_request": service_request,
            "favorites": favorites,
        },
    )


def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug, is_active=True)
    favorites = _get_favorites(request.session)
    vendor = _get_vendor(request.user)
    service_provider = _get_service_provider(request.user)
    if vendor:
        products = Product.objects.filter(category=category, is_active=True, vendor=vendor)
    elif service_provider:
        products = Product.objects.filter(
            category=category, is_active=True, service_provider=service_provider
        )
    else:
        products = Product.objects.filter(category=category, is_active=True).filter(
            active_product_filter()
        )
    return render(
        request,
        "store/category.html",
        {"category": category, "products": products, "favorites": favorites},
    )


@login_required
def request_service(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_active=True)
    if product.kind != Product.SERVICE:
        messages.error(request, "Ce produit n'est pas un service.")
        return redirect("store:product_detail", slug=product.slug)
    if _get_vendor(request.user) or _get_service_provider(request.user):
        messages.error(request, "Vous ne pouvez pas demander un service avec un profil pro.")
        return redirect("store:product_detail", slug=product.slug)
    provider = product.service_provider
    vendor = product.vendor
    if not provider and not vendor:
        messages.error(request, "Aucun prestataire associé à ce service.")
        return redirect("store:product_detail", slug=product.slug)

    if request.method != "POST":
        form = ServiceRequestForm()
        return render(
            request,
            "store/request_service.html",
            {"product": product, "form": form},
        )

    form = ServiceRequestForm(request.POST)
    if not form.is_valid():
        return render(
            request,
            "store/request_service.html",
            {"product": product, "form": form},
        )

    service_request, created = ServiceRequest.objects.get_or_create(
        service=product,
        customer=request.user,
        defaults={
            "comment": form.cleaned_data["comment"],
            "is_interested": form.cleaned_data["is_interested"],
            "vendor": vendor,
            "service_provider": provider,
        },
    )
    if not created:
        service_request.comment = form.cleaned_data["comment"]
        service_request.is_interested = form.cleaned_data["is_interested"]
        service_request.status = ServiceRequest.STATUS_PENDING
        service_request.vendor = vendor
        service_request.service_provider = provider
        service_request.save()

    target_user = None
    if provider and provider.owner:
        target_user = provider.owner
    elif vendor and vendor.owner:
        target_user = vendor.owner
    if target_user:
        Notification.objects.create(
            user=target_user,
            title="Nouvelle demande de service",
            body=f"{request.user.username} est intéressé par {product.name}.",
            kind=Notification.INFO,
        )

    messages.success(request, "Votre demande a été envoyée.")
    return redirect("store:product_detail", slug=product.slug)


def cart_detail(request):
    # Panier réservé aux clients : admin, vendeur et prestataire sont redirigés vers leur espace
    if request.user.is_authenticated:
        if _get_vendor(request.user):
            return redirect("marketplace:dashboard")
        if _get_service_provider(request.user):
            return redirect("marketplace:service_provider_dashboard")
        if _is_app_admin(request.user):
            return redirect("accounts:admin_dashboard")

    cart = _get_cart(request.session)
    product_ids = list(cart.keys())
    products = Product.objects.filter(id__in=product_ids).select_related("vendor", "service_provider")
    service_ids = list(products.filter(kind=Product.SERVICE).values_list("id", flat=True))
    if service_ids:
        for service_id in service_ids:
            cart.pop(str(service_id), None)
        request.session.modified = True
        messages.warning(request, "Les services ne peuvent pas être dans le panier. Utilisez 'Demander un service' pour réserver.")
        product_ids = list(cart.keys())
        products = Product.objects.filter(id__in=product_ids).select_related("vendor", "service_provider")
    product_list = list(products)
    items = []
    total = 0
    for product in product_list:
        quantity = cart.get(str(product.id), 0)
        line_total = quantity * float(product.price)
        total += line_total
        items.append(
            {
                "product": product,
                "quantity": quantity,
                "line_total": line_total,
            }
        )
    form = OrderForm()
    suggestions = (
        Product.objects.filter(is_active=True, kind=Product.PRODUCT)
        .filter(active_product_filter())
        .exclude(id__in=product_ids)
        .order_by("-created_at")[:6]
    )
    subtotal_dec = Decimal(str(total))
    pricing_ctx = _cart_pricing_context(product_list, subtotal_dec)
    return render(
        request,
        "store/cart.html",
        {
            "items": items,
            "total": total,
            "form": form,
            "suggestions": suggestions,
            "genius_payment": genius_is_configured(),
            **pricing_ctx,
        },
    )


def add_to_cart(request, product_id):
    is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"
    product = get_object_or_404(Product, id=product_id, is_active=True)

    def _error(message, redirect_target):
        if is_ajax:
            return JsonResponse({"ok": False, "message": message}, status=400)
        messages.error(request, message)
        return redirect(redirect_target)

    if product.kind == Product.SERVICE:
        return _error(
            "Les services ne peuvent pas être commandés. Utilisez 'Demander un service' pour réserver.",
            ("store:product_detail", {"slug": product.slug}),
        ) if not is_ajax else JsonResponse(
            {"ok": False, "message": "Les services ne peuvent pas être ajoutés au panier."},
            status=400,
        )
    if request.user.is_authenticated:
        if _get_vendor(request.user):
            msg = "Les vendeurs ne peuvent pas acheter de produits."
            if is_ajax:
                return JsonResponse({"ok": False, "message": msg}, status=403)
            messages.error(request, msg)
            return redirect("store:product_list")
        if _get_service_provider(request.user):
            msg = "Les prestataires ne peuvent pas acheter de produits."
            if is_ajax:
                return JsonResponse({"ok": False, "message": msg}, status=403)
            messages.error(request, msg)
            return redirect("store:product_list")
        if _is_app_admin(request.user):
            msg = "Les comptes administration ne peuvent pas acheter de produits."
            if is_ajax:
                return JsonResponse({"ok": False, "message": msg}, status=403)
            messages.error(request, msg)
            return redirect("store:product_list")

    cart = _get_cart(request.session)
    cart[str(product.id)] = cart.get(str(product.id), 0) + 1
    request.session.modified = True

    if is_ajax:
        cart_count = sum(int(q) for q in cart.values())
        return JsonResponse(
            {
                "ok": True,
                "message": f"{product.name} ajouté au panier",
                "product_name": product.name,
                "cart_count": cart_count,
            }
        )
    return redirect("store:cart_detail")


def remove_from_cart(request, product_id):
    cart = _get_cart(request.session)
    cart.pop(str(product_id), None)
    request.session.modified = True
    return redirect("store:cart_detail")


def update_cart(request, product_id):
    if request.method != "POST":
        return redirect("store:cart_detail")
    cart = _get_cart(request.session)
    product = get_object_or_404(Product, id=product_id)
    if product.kind == Product.SERVICE:
        cart.pop(str(product_id), None)
        request.session.modified = True
        messages.error(request, "Les services ne peuvent pas être ajoutés au panier. Utilisez 'Demander un service' pour réserver.")
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            product_ids = list(cart.keys())
            products = Product.objects.filter(id__in=product_ids)
            total = 0
            for item in products:
                qty = cart.get(str(item.id), 0)
                total += qty * float(item.price)
            return JsonResponse(
                {"line_total": 0, "total": round(total, 2), "quantity": 0}
            )
        return redirect("store:cart_detail")
    quantity = int(request.POST.get("quantity", 1))
    if quantity <= 0:
        cart.pop(str(product_id), None)
    else:
        cart[str(product_id)] = quantity
    request.session.modified = True
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        product_ids = list(cart.keys())
        products = Product.objects.filter(id__in=product_ids)
        total = 0
        line_total = 0
        for product in products:
            qty = cart.get(str(product.id), 0)
            item_total = qty * float(product.price)
            total += item_total
            if product.id == product_id:
                line_total = item_total
        return JsonResponse(
            {
                "line_total": round(line_total, 2),
                "total": round(total, 2),
                "quantity": cart.get(str(product_id), 0),
            }
        )
    return redirect("store:cart_detail")


def vendor_list(request):
    vendors = Vendor.objects.filter(is_active=True).filter(active_subscription_q())
    return render(request, "store/vendors.html", {"vendors": vendors})


def service_provider_list(request):
    """Liste des prestataires de services avec affichage professionnel."""
    query = request.GET.get("q", "").strip()
    category_slug = request.GET.get("categorie", "").strip()
    location = request.GET.get("localisation", "").strip()
    
    service_providers = (
        ServiceProvider.objects.filter(is_active=True)
        .filter(active_subscription_q())
        .select_related("owner")
        .prefetch_related("servicerequest_set")
    )
    
    if query:
        service_providers = service_providers.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query) | 
            Q(services_overview__icontains=query)
        )
    
    if category_slug:
        service_providers = service_providers.filter(
            product__category__slug=category_slug,
            product__kind=Product.SERVICE,
            product__is_active=True
        ).distinct()
    
    if location:
        service_providers = service_providers.filter(
            Q(location__icontains=location)
        )
    
    service_providers = service_providers.annotate(
        services_count=Count("product", filter=Q(product__kind=Product.SERVICE, product__is_active=True)),
        approved_requests_count=Count(
            "servicerequest", 
            filter=Q(servicerequest__status=ServiceRequest.STATUS_APPROVED)
        )
    ).order_by("-approved_requests_count", "-services_count", "-verified_at")
    
    categories = Category.objects.filter(
        is_active=True,
        vendor__isnull=True,
        service_provider__isnull=True,
    )
    
    return render(
        request,
        "store/service_providers.html",
        {
            "service_providers": service_providers,
            "categories": categories,
            "query": query,
            "location": location,
        },
    )


def service_provider_detail(request, slug):
    """Détails d'un prestataire de services."""
    service_provider = get_object_or_404(
        ServiceProvider.objects.filter(active_subscription_q()),
        slug=slug,
        is_active=True,
    )
    
    # Services proposés par ce prestataire
    services = Product.objects.filter(
        service_provider=service_provider, is_active=True, kind=Product.SERVICE
    ).select_related("category")
    
    # Statistiques
    total_requests = ServiceRequest.objects.filter(service_provider=service_provider).count()
    approved_requests = ServiceRequest.objects.filter(
        service_provider=service_provider, status=ServiceRequest.STATUS_APPROVED
    ).count()
    
    # Avis moyens sur les services
    avg_rating = (
        Review.objects.filter(
            product__service_provider=service_provider, is_approved=True
        )
        .aggregate(avg=Avg("rating"))
        .get("avg")
    )
    
    return render(
        request,
        "store/service_provider_detail.html",
        {
            "service_provider": service_provider,
            "services": services,
            "total_requests": total_requests,
            "approved_requests": approved_requests,
            "avg_rating": avg_rating,
        },
    )


def vendor_detail(request, slug):
    vendor = get_object_or_404(
        Vendor.objects.filter(active_subscription_q()), slug=slug, is_active=True
    )
    favorites = _get_favorites(request.session)
    products = Product.objects.filter(vendor=vendor, is_active=True)
    reviews = (
        Review.objects.filter(product__vendor=vendor, is_approved=True)
        .select_related("product", "user")
        .order_by("-created_at")[:10]
    )
    avg_rating = (
        Review.objects.filter(product__vendor=vendor, is_approved=True)
        .aggregate(avg=Avg("rating"))
        .get("avg")
    )
    return render(
        request,
        "store/vendor_detail.html",
        {
            "vendor": vendor,
            "products": products,
            "reviews": reviews,
            "avg_rating": avg_rating,
            "favorites": favorites,
        },
    )


def favorites_list(request):
    """
    Liste des produits ajoutés en favoris (session). Réservé aux clients.
    """
    if request.user.is_authenticated:
        if _get_vendor(request.user):
            return redirect("marketplace:dashboard")
        if _get_service_provider(request.user):
            return redirect("marketplace:service_provider_dashboard")
        if _is_app_admin(request.user):
            return redirect("accounts:admin_dashboard")

    favorites = _get_favorites(request.session)
    products = (
        Product.objects.filter(id__in=favorites, is_active=True)
        .filter(active_product_filter())
        .select_related("category", "vendor", "service_provider")
        .prefetch_related("media")
    )
    # Conserver l'ordre d'ajout si possible
    products = sorted(products, key=lambda p: favorites.index(p.id) if p.id in favorites else 0)
    return render(
        request,
        "store/favorites.html",
        {"products": products, "favorites": favorites},
    )


@login_required
def toggle_favorite(request, product_id):
    """
    Ajoute ou retire un produit des favoris (session). Réservé aux clients.
    """
    if _get_vendor(request.user) or _get_service_provider(request.user) or _is_app_admin(request.user):
        messages.info(request, "Les favoris sont réservés aux comptes clients.")
        next_url = request.META.get("HTTP_REFERER") or reverse("store:product_list")
        return redirect(next_url)
    product = get_object_or_404(Product, id=product_id, is_active=True)
    favorites = _get_favorites(request.session)
    if product_id in favorites:
        favorites = [pid for pid in favorites if pid != product_id]
        messages.info(request, "Produit retiré de vos favoris.")
    else:
        favorites.append(product_id)
        messages.success(request, "Produit ajouté à vos favoris.")
    request.session["favorites"] = favorites
    request.session.modified = True

    next_url = request.META.get("HTTP_REFERER") or reverse("store:product_detail", args=[product.slug])
    return redirect(next_url)


@login_required
def checkout(request):
    cart = _get_cart(request.session)
    vendor = _get_vendor(request.user)
    service_provider = _get_service_provider(request.user)
    if vendor:
        messages.error(request, "Les vendeurs ne peuvent pas passer de commande.")
        return redirect("store:cart_detail")
    if service_provider:
        messages.error(request, "Les prestataires ne peuvent pas passer de commande.")
        return redirect("store:cart_detail")
    if _is_app_admin(request.user):
        messages.error(request, "Les comptes administration ne peuvent pas passer de commande.")
        return redirect("store:cart_detail")
    product_ids = list(cart.keys())
    products = Product.objects.filter(id__in=product_ids).select_related("vendor", "service_provider")
    if products.filter(kind=Product.SERVICE).exists():
        messages.error(request, "Les services ne peuvent pas être commandés. Utilisez 'Demander un service' pour réserver.")
        return redirect("store:cart_detail")
    if request.method != "POST":
        return redirect("store:cart_detail")

    form = OrderForm(request.POST)
    if not form.is_valid():
        product_list = list(products)
        items = []
        total = 0
        for product in product_list:
            quantity = cart.get(str(product.id), 0)
            line_total = quantity * float(product.price)
            total += line_total
            items.append(
                {
                    "product": product,
                    "quantity": quantity,
                    "line_total": line_total,
                }
            )
        subtotal_dec = Decimal(str(total))
        pricing_ctx = _cart_pricing_context(product_list, subtotal_dec)
        suggestions = (
            Product.objects.filter(is_active=True, kind=Product.PRODUCT)
            .filter(active_product_filter())
            .exclude(id__in=product_ids)
            .order_by("-created_at")[:6]
        )
        return render(
            request,
            "store/cart.html",
            {
                "items": items,
                "total": total,
                "form": form,
                "genius_payment": genius_is_configured(),
                "suggestions": suggestions,
                **pricing_ctx,
            },
        )

    if not products.exists():
        return redirect("store:cart_detail")

    order = form.save(commit=False)
    if request.user.is_authenticated:
        order.user = request.user

    product_list = list(products)
    items = []
    subtotal = 0
    for product in product_list:
        quantity = cart.get(str(product.id), 0)
        line_total = quantity * float(product.price)
        subtotal += line_total
        items.append((product, quantity))

    order.delivery_fee = cart_delivery_fee(product_list, delivery_option=order.delivery_option)
    order.total_amount = Decimal(str(subtotal)) + order.delivery_fee
    order.save()
    for product, quantity in items:
        if quantity:
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                unit_price=product.price,
            )

    payment = Payment.objects.create(
        order=order,
        provider=order.payment_method,
        amount=order.total_amount,
    )

    def _notify_order_created():
        if request.user.is_authenticated:
            Notification.objects.create(
                user=request.user,
                title="Commande enregistrée",
                body=f"Votre commande {order.id} est en attente de paiement.",
                kind=Notification.ORDER,
            )

    if order.payment_method == Order.METHOD_GENIUS:
        success_url = request.build_absolute_uri(
            reverse("payments:genius_return", kwargs={"payment_id": payment.id})
        )
        error_url = request.build_absolute_uri(
            reverse("payments:genius_error", kwargs={"payment_id": payment.id})
        )
        try:
            res = create_checkout_payment(
                amount=order.total_amount,
                description=f"Commande #{order.id} — Kolê",
                customer_name=order.full_name,
                customer_email=order.email,
                customer_phone=order.phone,
                metadata={"payment_id": str(payment.id), "order_id": str(order.id)},
                success_url=success_url,
                error_url=error_url,
            )
        except GeniusPaymentError as exc:
            order.delete()
            messages.error(request, str(exc))
            return redirect("store:cart_detail")

        ref = (res.get("reference") or "")[:80]
        if ref:
            payment.reference = ref
            payment.save(update_fields=["reference"])
        request.session["cart"] = {}
        request.session.modified = True
        _notify_order_created()
        return redirect(res["checkout_url"])

    if order.payment_method == Order.METHOD_LOCAL:
        request.session["cart"] = {}
        request.session.modified = True
        _notify_order_created()
        messages.success(
            request,
            "Commande enregistrée. Vous paierez en espèces à la livraison.",
        )
        return redirect("store:order_success", order_id=order.id)

    messages.error(
        request,
        "Le paiement en ligne n'est pas disponible. Choisissez GeniusPay ou le paiement à la livraison.",
    )
    order.delete()
    return redirect("store:cart_detail")


def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, "store/order_success.html", {"order": order})
