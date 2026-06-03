from catalog.models import Category


def category_nav(request):
    categories = Category.objects.filter(
        is_active=True,
        parent__isnull=True,
        vendor__isnull=True,
        service_provider__isnull=True,
    )
    cart = request.session.get("cart", {})
    cart_count = 0
    if isinstance(cart, dict):
        cart_count = sum(int(qty) for qty in cart.values())
    raw_favorites = request.session.get("favorites", [])
    favorites = []
    if isinstance(raw_favorites, dict):
        raw_favorites = raw_favorites.keys()
    for value in raw_favorites:
        try:
            favorites.append(int(value))
        except (TypeError, ValueError):
            continue
    favorites_count = len(favorites)
    from payments.genius import is_configured as genius_is_configured

    return {
        "nav_categories": categories,
        "cart_count": cart_count,
        "favorites_count": favorites_count,
        "genius_payment": genius_is_configured(),
    }
