from catalog.models import Category
from kwalo.contact_info import (
    KOLE_CONTACT_EMAIL,
    KOLE_CONTACT_PHONE,
    KOLE_CONTACT_PHONE_INTL,
    KOLE_WHATSAPP_WA_ME,
)


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
        "kole_contact_email": KOLE_CONTACT_EMAIL,
        "kole_contact_phone": KOLE_CONTACT_PHONE,
        "kole_contact_phone_intl": KOLE_CONTACT_PHONE_INTL,
        "kole_whatsapp_wa_me": KOLE_WHATSAPP_WA_ME,
    }
