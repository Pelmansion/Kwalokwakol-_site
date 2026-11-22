"""Coordonnées officielles Kolê Group (affichage site, page contact, emails)."""

KOLE_CONTACT_EMAIL = "kwakolegroup@gmail.com"
KOLE_CONTACT_PHONE = "0799633113"
KOLE_CONTACT_PHONE_INTL = "+2250799633113"
KOLE_WHATSAPP_WA_ME = "2250799633113"

# Réseaux sociaux (laisser vide pour masquer le lien dans le pied de page)
KOLE_SOCIAL_FACEBOOK = ""
KOLE_SOCIAL_INSTAGRAM = ""
KOLE_SOCIAL_TIKTOK = ""
KOLE_SOCIAL_YOUTUBE = ""

# Pied de page éditorial Dan Prestige Magazine (configurable)
MAGAZINE_EDITORIAL = {
    "publisher": "Kolê Group",
    "magazine_name": "Dan Prestige Magazine",
    "director": "Directeur de publication",
    "editor_in_chief": "Rédacteur en chef",
    "email": KOLE_CONTACT_EMAIL,
    "phone": KOLE_CONTACT_PHONE,
    "legal_notice": (
        "Dan Prestige Magazine est un média édité par Kolê Group. "
        "Les publireportages sont clairement identifiés. "
        "Reproduction interdite sans autorisation."
    ),
}


def contact_page_content() -> str:
    return (
        "<p>Besoin d'aide, d'informations ou d'un accompagnement pour votre commande ? "
        "Notre équipe support vous répond avec plaisir.</p>"
        "<h2>Horaires</h2>"
        "<ul>"
        "<li><strong>Lundi – vendredi :</strong> 8 h – 18 h</li>"
        "<li><strong>Samedi :</strong> 9 h – 14 h</li>"
        "<li><strong>Dimanche et jours fériés :</strong> réponse par e-mail sous 24 h</li>"
        "</ul>"
        "<h2>Nous joindre</h2>"
        f"<p><strong>Email :</strong> "
        f'<a href="mailto:{KOLE_CONTACT_EMAIL}">{KOLE_CONTACT_EMAIL}</a></p>'
        f"<p><strong>Téléphone / WhatsApp :</strong> "
        f'<a href="tel:{KOLE_CONTACT_PHONE_INTL}">{KOLE_CONTACT_PHONE}</a></p>'
        f'<p><a href="https://wa.me/{KOLE_WHATSAPP_WA_ME}" target="_blank" rel="noopener">'
        "Écrire sur WhatsApp</a></p>"
        "<h2>Avant de nous écrire</h2>"
        "<ul>"
        "<li>Consultez la <a href=\"/page/faq/\">FAQ</a> : la réponse y est souvent déjà disponible.</li>"
        "<li>Pour une commande en cours, utilisez la messagerie depuis <em>Mes commandes</em> "
        "pour contacter directement le vendeur.</li>"
        "<li>Indiquez toujours votre numéro de commande ou l'e-mail du compte utilisé.</li>"
        "</ul>"
    )
