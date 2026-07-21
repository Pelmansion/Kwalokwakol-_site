#!/usr/bin/env python3
"""
Génère le guide utilisateur PDF Kolê Group (connexion, navigation, profils).
Usage : python scripts/generate_guide_pdf.py
Sortie : docs/Guide_Utilisateur_Kole_Group.pdf
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "Guide_Utilisateur_Kole_Group.pdf"
AFFICHES = ROOT / "docs" / "affiches"
ONBOARDING = ROOT / "static" / "images" / "onboarding"

SITE_DISPLAY = "kolêgroup.com"
SITE = f"https://{SITE_DISPLAY}"


def _img(path: Path, max_width_cm: float):
    from reportlab.lib.units import cm
    from reportlab.lib.utils import ImageReader
    from reportlab.platypus import Image

    if not path.is_file():
        return None
    reader = ImageReader(str(path))
    iw, ih = reader.getSize()
    w = max_width_cm * cm
    h = w * (ih / float(iw))
    return Image(str(path), width=w, height=h)


def _first_image(*candidates: Path, max_width_cm: float = 16):
    for path in candidates:
        img = _img(path, max_width_cm)
        if img is not None:
            return img
    return None


def _caption(text: str, style):
    from reportlab.platypus import Paragraph

    return Paragraph(
        f'<i><font size="8" color="#6b5f54">{text}</font></i>',
        style,
    )


def main() -> int:
    try:
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import cm
        from reportlab.platypus import (
            PageBreak,
            Paragraph,
            SimpleDocTemplate,
            Spacer,
            Table,
            TableStyle,
        )
    except ImportError:
        print("Installez reportlab : pip install reportlab", file=sys.stderr)
        return 1

    OUT.parent.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet()

    title = ParagraphStyle(
        "Titre",
        parent=styles["Heading1"],
        fontSize=24,
        spaceAfter=14,
        textColor=colors.HexColor("#9a3412"),
        alignment=TA_CENTER,
    )
    cover_sub = ParagraphStyle(
        "CoverSub",
        parent=styles["Normal"],
        fontSize=12,
        textColor=colors.HexColor("#443a33"),
        alignment=TA_CENTER,
        spaceAfter=6,
    )
    h2 = ParagraphStyle(
        "H2",
        parent=styles["Heading2"],
        fontSize=14,
        spaceBefore=10,
        spaceAfter=8,
        textColor=colors.HexColor("#c2410c"),
    )
    h3 = ParagraphStyle(
        "H3",
        parent=styles["Heading3"],
        fontSize=11,
        spaceBefore=8,
        spaceAfter=5,
        textColor=colors.HexColor("#9a3412"),
    )
    body = ParagraphStyle(
        "Corps",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        alignment=TA_JUSTIFY,
        spaceAfter=6,
    )
    bullet = ParagraphStyle(
        "Puce",
        parent=styles["Normal"],
        fontSize=10,
        leading=13,
        leftIndent=14,
        bulletIndent=4,
        spaceAfter=4,
    )
    step = ParagraphStyle(
        "Etape",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        leftIndent=8,
        spaceAfter=5,
    )
    tip = ParagraphStyle(
        "Astuce",
        parent=body,
        fontSize=9.5,
        backColor=colors.HexColor("#fff7ed"),
        borderPadding=8,
        leftIndent=6,
        rightIndent=6,
        spaceBefore=4,
        spaceAfter=8,
    )
    url_style = ParagraphStyle(
        "URL",
        parent=styles["Normal"],
        fontSize=11,
        textColor=colors.HexColor("#c2410c"),
        alignment=TA_CENTER,
    )
    toc = ParagraphStyle(
        "TOC",
        parent=styles["Normal"],
        fontSize=10,
        leading=16,
        leftIndent=10,
        spaceAfter=2,
    )

    def section(title_text: str):
        story.append(Paragraph(title_text, h2))

    def subsection(title_text: str):
        story.append(Paragraph(title_text, h3))

    def steps(lines: list[str]):
        for line in lines:
            story.append(Paragraph(line, step))

    def bullets(lines: list[str]):
        for line in lines:
            story.append(Paragraph(f"• {line}", bullet))

    def tip_box(text: str):
        story.append(Paragraph(f"<b>💡 Astuce :</b> {text}", tip))

    def add_illustration(*paths: Path, caption: str = "", width: float = 16):
        img = _first_image(*paths, max_width_cm=width)
        if img:
            story.append(Spacer(1, 0.2 * cm))
            story.append(img)
            if caption:
                story.append(_caption(caption, body))
            story.append(Spacer(1, 0.15 * cm))

    story: list = []

    # ── Couverture ──
    story.append(Spacer(1, 2 * cm))
    logo = _img(ROOT / "static" / "images" / "icons" / "icon-192.png", 3.5)
    if logo:
        story.append(logo)
        story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph("Guide utilisateur", title))
    story.append(Paragraph("Kolê Group", ParagraphStyle("Brand", parent=cover_sub, fontSize=16, fontName="Helvetica-Bold")))
    story.append(Paragraph("Marketplace Afro-moderne — Acheter · Réserver · Célébrer", cover_sub))
    story.append(Spacer(1, 0.8 * cm))
    story.append(Paragraph(f"<b>{SITE_DISPLAY}</b>", url_style))
    story.append(Spacer(1, 0.4 * cm))
    story.append(
        Paragraph(
            "Ce document explique, étape par étape et avec des illustrations, "
            "comment utiliser le site Kolê Group : créer un compte, acheter, réserver un service, "
            "ouvrir une boutique, proposer un service ou publier votre musique.",
            ParagraphStyle("IntroCover", parent=body, alignment=TA_CENTER, fontSize=10),
        )
    )
    story.append(Spacer(1, 0.6 * cm))
    story.append(
        Paragraph(
            f"Version {date.today().strftime('%d/%m/%Y')} — "
            "Destiné aux clients, vendeurs, prestataires et artistes.",
            ParagraphStyle("Meta", parent=styles["Normal"], fontSize=8, textColor=colors.grey, alignment=TA_CENTER),
        )
    )
    story.append(PageBreak())

    # ── Sommaire ──
    story.append(Paragraph("Sommaire", h2))
    for item in [
        "1. Bienvenue — Qu'est-ce que Kolê Group ?",
        "2. Les 4 profils utilisateur",
        "3. Créer un compte et se connecter",
        "4. Naviguer sur le site (ordinateur et mobile)",
        "5. Client — Acheter un produit (du panier au paiement)",
        "6. Client — Réserver un service",
        "7. Suivre ses commandes et réservations",
        "8. Devenir vendeur (boutique en ligne)",
        "9. Devenir prestataire de services",
        "10. Kolê Culture — Musique, concerts, artistes",
        "11. Aide, contact et installation sur mobile",
        "12. Récapitulatif des adresses utiles",
    ]:
        story.append(Paragraph(item, toc))
    story.append(PageBreak())

    # ── 1. Introduction ──
    section("1. Bienvenue — Qu'est-ce que Kolê Group ?")
    story.append(
        Paragraph(
            "<b>Kolê Group</b> est une marketplace en ligne qui regroupe tout ce dont vous avez besoin "
            "au quotidien : <b>produits locaux</b> (mode, alimentation, artisanat…), "
            "<b>services</b> (hébergement, location, réparation…), et l'univers "
            "<b>Culture</b> (musique, concerts, artistes ivoiriens).",
            body,
        )
    )
    story.append(
        Paragraph(
            "Le site est accessible depuis un <b>navigateur web</b> (Chrome, Safari, Firefox…) "
            f"à l'adresse <b>{SITE_DISPLAY}</b>. Sur mobile, vous pouvez aussi l'<b>installer</b> "
            "comme une application (voir section 11).",
            body,
        )
    )
    add_illustration(
        AFFICHES / "affiche-pub-kole-group.png",
        ROOT / "docs" / "affiche-pub-kole-group.png",
        caption="Kolê Group — une plateforme, plusieurs usages.",
        width=14,
    )
    story.append(PageBreak())

    # ── 2. Profils ──
    section("2. Les 4 profils utilisateur")
    story.append(
        Paragraph(
            "Sur Kolê Group, tout le monde commence par un <b>compte client</b>. Ensuite, "
            "vous pouvez activer un profil professionnel selon votre activité :",
            body,
        )
    )
    profils = [
        ["Profil", "Pour qui ?", "Ce que vous pouvez faire"],
        [
            "Client",
            "Tout visiteur",
            "Acheter des produits, réserver des services, acheter de la musique et des billets",
        ],
        [
            "Vendeur",
            "Commerçants, artisans",
            "Ouvrir une boutique, publier des produits, gérer les commandes",
        ],
        [
            "Prestataire",
            "Professionnels de services",
            "Proposer des services (hôtel, location, réparation…), gérer les demandes",
        ],
        [
            "Artiste",
            "Musiciens, organisateurs",
            "Publier de la musique, vendre des billets de concert (Kolê Culture)",
        ],
    ]
    t = Table(profils, colWidths=[2.8 * cm, 4.2 * cm, 9.5 * cm])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#fff7ed")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#9a3412")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 9),
                ("FONTSIZE", (0, 1), (-1, -1), 8.5),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e7e5e4")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(t)
    story.append(Spacer(1, 0.3 * cm))
    add_illustration(
        AFFICHES / "affiche-fonctionnement-profils.png",
        ONBOARDING / "guide-profils.jpeg",
        caption="Les quatre profils Kolê Group.",
    )
    tip_box(
        "À votre première visite sur le site, un <b>guide interactif</b> s'affiche automatiquement "
        "et reprend ces mêmes explications. Vous pouvez le parcourir en faisant glisser les écrans."
    )
    story.append(PageBreak())

    # ── 3. Connexion ──
    section("3. Créer un compte et se connecter")
    subsection("3.1 Créer un compte (inscription)")
    steps(
        [
            f"1. Ouvrez votre navigateur et allez sur <b>{SITE_DISPLAY}</b>.",
            "2. En haut à droite, cliquez sur le menu <b>Compte</b>, puis sur <b>Créer un compte</b>.",
            f"   Lien direct : <b>{SITE}/compte/inscription/</b>",
            "3. Remplissez le formulaire : <b>adresse e-mail</b>, <b>nom d'utilisateur</b> "
            "et <b>mot de passe</b> (minimum 8 caractères).",
            "4. Validez le formulaire. Un e-mail de confirmation vous est envoyé.",
            "5. Ouvrez votre boîte mail et cliquez sur le <b>lien de vérification</b> pour activer votre compte.",
            "6. <b>Alternative rapide :</b> vous pouvez aussi vous inscrire avec votre compte "
            "<b>Google</b> ou <b>Facebook</b> (boutons sur la page d'inscription).",
        ]
    )
    tip_box(
        "Sur téléphone, utilisez l'icône <b>Compte</b> dans la barre du bas de l'écran "
        "pour accéder à l'inscription ou à la connexion."
    )

    subsection("3.2 Se connecter (déjà inscrit)")
    steps(
        [
            "1. Cliquez sur <b>Compte → Connexion</b> en haut de la page.",
            f"2. Lien direct : <b>{SITE}/compte/connexion/</b>",
            "3. Saisissez votre <b>identifiant</b> (e-mail ou nom d'utilisateur) et votre <b>mot de passe</b>.",
            "4. Cliquez sur <b>Se connecter</b>. Vous accédez alors à votre espace personnel.",
        ]
    )

    subsection("3.3 Mot de passe oublié")
    story.append(
        Paragraph(
            "Sur la page de connexion, cliquez sur <b>Mot de passe oublié ?</b>. "
            "Saisissez votre e-mail : vous recevrez un lien pour choisir un nouveau mot de passe.",
            body,
        )
    )
    story.append(PageBreak())

    # ── 4. Navigation ──
    section("4. Naviguer sur le site (ordinateur et mobile)")
    story.append(
        Paragraph(
            "Le site est organisé autour de zones claires. Voici où trouver chaque fonction :",
            body,
        )
    )
    nav_data = [
        ["Zone", "Où cliquer (ordinateur)", "Sur mobile", "À quoi ça sert"],
        ["Accueil", "Logo Kolê en haut", "Barre du bas « Accueil »", "Page d'accueil, offres, catégories"],
        ["Explorer", "Menu « Explorer »", "Barre du bas « Explorer »", "Tous les produits et services"],
        ["Recherche", "Barre en haut", "Barre en haut", "Chercher un produit, une boutique, un service"],
        ["Panier", "Icône panier (haut)", "Barre du bas « Panier »", "Voir et valider vos achats"],
        ["Favoris", "Icône cœur", "Menu Compte", "Produits enregistrés pour plus tard"],
        ["Compte", "Menu Compte (haut)", "Barre du bas « Compte »", "Profil, commandes, réservations"],
        ["Culture", "Bouton « Culture »", "Menu ou barre du bas", "Musique, concerts, artistes"],
        ["Aide", "Menu Aide", "Menu Compte → Aide", "FAQ, contact, conditions générales"],
        ["Kwa", "Bulle orange (bas droite)", "Bulle orange", "Assistant : réponses rapides"],
    ]
    t = Table(nav_data, colWidths=[2.2 * cm, 4 * cm, 3.8 * cm, 6.5 * cm])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#fff7ed")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#9a3412")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 8),
                ("FONTSIZE", (0, 1), (-1, -1), 7.8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e7e5e4")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(t)
    add_illustration(
        AFFICHES / "affiche-fonctionnement-vue-ensemble.png",
        ONBOARDING / "guide-vue-ensemble.jpeg",
        caption="Vue d'ensemble : compte → explorer → recevoir ou réserver.",
    )
    story.append(PageBreak())

    # ── 5. Client achat ──
    section("5. Client — Acheter un produit (du panier au paiement)")
    add_illustration(
        AFFICHES / "affiche-fonctionnement-client.png",
        ONBOARDING / "guide-client.jpeg",
        caption="Parcours client : parcourir, ajouter au panier, payer, suivre.",
    )
    subsection("Étape 1 — Trouver un produit")
    steps(
        [
            f"1. Sur l'accueil (<b>{SITE_DISPLAY}</b>) ou via <b>Explorer</b>, parcourez les catégories.",
            f"2. Utilisez la <b>barre de recherche</b> ou la page <b>{SITE}/produits/</b>.",
            "3. Cliquez sur un produit pour voir sa fiche : photos, prix, description, vendeur.",
        ]
    )
    subsection("Étape 2 — Ajouter au panier")
    steps(
        [
            "1. Sur la fiche produit, choisissez la <b>quantité</b> souhaitée.",
            "2. Cliquez sur <b>Ajouter au panier</b>.",
            "3. L'icône panier se met à jour. Vous pouvez continuer vos achats ou aller au panier.",
            f"4. Panier : <b>{SITE}/panier/</b>",
        ]
    )
    subsection("Étape 3 — Valider la commande")
    steps(
        [
            "1. Dans le panier, vérifiez les articles, quantités et le total.",
            "2. Cliquez sur <b>Passer commande</b> (vous devez être connecté).",
            f"3. Page commande : <b>{SITE}/commande/</b> — renseignez adresse de livraison et téléphone.",
            "4. Choisissez le mode de paiement proposé.",
        ]
    )
    subsection("Étape 4 — Payer")
    bullets(
        [
            "<b>Paiement en ligne (GeniusPay)</b> : Wave, Orange Money, MTN MoMo ou carte bancaire "
            "selon disponibilité. Vous êtes redirigé vers une page sécurisée, puis revenez sur le site.",
            "<b>Paiement à la livraison</b> : proposé par certains vendeurs — vous payez à réception.",
        ]
    )
    subsection("Étape 5 — Suivre la livraison")
    steps(
        [
            f"1. Menu <b>Compte → Mes commandes</b> ou <b>{SITE}/compte/commandes/</b>.",
            "2. Consultez le <b>statut</b> : en préparation, expédiée, livrée.",
            "3. Utilisez la <b>messagerie</b> pour contacter le vendeur si besoin.",
        ]
    )
    tip_box("Livraison gratuite dès <b>15 000 FCFA</b> sur les commandes éligibles.")
    story.append(PageBreak())

    # ── 6. Réservation ──
    section("6. Client — Réserver un service")
    story.append(
        Paragraph(
            "Les services (hébergement, location de véhicule, prestations diverses) "
            "ne passent pas par le panier classique : vous faites une <b>demande de réservation</b>.",
            body,
        )
    )
    steps(
        [
            f"1. Trouvez un service via <b>Explorer</b> ou <b>{SITE}/prestataires/</b>.",
            "2. Ouvrez la fiche du service et lisez les conditions (tarif, durée, zone).",
            "3. Cliquez sur <b>Réserver</b> ou <b>Demander une réservation</b>.",
            "4. Remplissez le formulaire : dates, message au prestataire, coordonnées.",
            "5. Envoyez la demande. Le prestataire la <b>valide</b> ou la <b>refuse</b>.",
            f"6. Suivez vos demandes dans <b>Compte → Mes réservations</b> "
            f"(<b>{SITE}/compte/reservations/</b>).",
        ]
    )
    story.append(
        Paragraph(
            "<b>Annulation :</b> une demande en attente peut être annulée avant midi (12 h) : "
            "le jour même si vous avez réservé le matin, sinon jusqu'à midi le lendemain.",
            tip,
        )
    )
    story.append(PageBreak())

    # ── 7. Suivi ──
    section("7. Suivre ses commandes et réservations")
    story.append(
        Paragraph(
            "Toutes vos activités sont regroupées dans votre <b>espace Compte</b>. "
            "Les listes s'affichent sous forme de <b>tableaux</b> clairs (date, statut, actions).",
            body,
        )
    )
    suivi = [
        ["Page", "Adresse", "Contenu"],
        ["Mon profil", f"{SITE}/compte/profil/", "Informations personnelles, changement de mot de passe"],
        ["Mes commandes", f"{SITE}/compte/commandes/", "Historique des achats produits, statuts, messagerie"],
        ["Mes réservations", f"{SITE}/compte/reservations/", "Demandes de services, statut validé/en attente"],
        ["Mes favoris", f"{SITE}/favoris/", "Produits enregistrés avec l'icône cœur"],
        ["Mes billets", f"{SITE}/culture/ (menu Compte)", "Billets de concert avec QR code"],
        ["Mes achats musique", f"{SITE}/culture/ (menu Compte)", "Titres achetés, liens de téléchargement"],
    ]
    t = Table(suivi, colWidths=[3.5 * cm, 5.5 * cm, 7.5 * cm])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#fff7ed")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 9),
                ("FONTSIZE", (0, 1), (-1, -1), 8.5),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e7e5e4")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(t)
    story.append(PageBreak())

    # ── 8. Vendeur ──
    section("8. Devenir vendeur (boutique en ligne)")
    add_illustration(
        AFFICHES / "affiche-fonctionnement-vendeur-prestataire.png",
        ONBOARDING / "guide-vendeur-prestataire.jpeg",
        caption="Devenir vendeur ou prestataire sur Kolê Group.",
    )
    steps(
        [
            "1. Créez un compte client et connectez-vous.",
            f"2. Menu <b>Compte → Devenir vendeur</b> ou <b>{SITE}/vendeur/inscription/</b>.",
            "3. Remplissez le formulaire : nom de boutique, description, identité, documents (KYC).",
            "4. Choisissez une <b>formule d'abonnement</b> (Starter, Pro ou Premium).",
            "5. Une fois validé, accédez à l'<b>espace vendeur</b> :",
            "   • Ajouter des produits (photos, prix, stock)",
            "   • Gérer les commandes reçues",
            "   • Répondre aux avis clients",
            f"6. Tableau de bord : <b>{SITE}/vendeur/dashboard/</b>",
        ]
    )
    story.append(PageBreak())

    # ── 9. Prestataire ──
    section("9. Devenir prestataire de services")
    steps(
        [
            "1. Créez un compte et connectez-vous.",
            f"2. Menu <b>Compte → Devenir prestataire</b> ou "
            f"<b>{SITE}/vendeur/prestataire/inscription/</b>.",
            "3. Décrivez votre activité, zone d'intervention et tarifs indicatifs.",
            "4. Choisissez une formule d'abonnement.",
            "5. Publiez vos services depuis l'espace prestataire.",
            "6. Recevez et traitez les demandes clients (accepter / refuser).",
            f"7. Tableau de bord : <b>{SITE}/vendeur/prestataire/dashboard/</b>",
            f"8. Liste des demandes : <b>{SITE}/vendeur/prestataire/demandes/</b>",
        ]
    )
    story.append(PageBreak())

    # ── 10. Culture ──
    section("10. Kolê Culture — Musique, concerts, artistes")
    add_illustration(
        AFFICHES / "affiche-fonctionnement-culture.png",
        ONBOARDING / "guide-culture.jpeg",
        caption="Kolê Culture : écouter, acheter, assister à des concerts.",
    )
    bullets(
        [
            f"<b>Explorer Culture :</b> {SITE}/culture/ — musique, événements, artistes.",
            "<b>Écouter et acheter</b> des titres d'artistes ivoiriens (téléchargement après achat).",
            "<b>Acheter un billet</b> de concert — QR code scanné à l'entrée de l'événement.",
            "<b>Devenir artiste :</b> Compte → Activer profil artiste → Espace artiste pour publier titres et événements.",
            "<b>Mes billets</b> et <b>Mes achats musique</b> : accessibles depuis le menu Compte.",
        ]
    )
    story.append(PageBreak())

    # ── 11. Aide ──
    section("11. Aide, contact et installation sur mobile")
    subsection("11.1 Assistant Kwa")
    story.append(
        Paragraph(
            "Une <b>bulle orange</b> en bas à droite du site ouvre l'assistant <b>Kwa</b>. "
            "Posez votre question en langage simple : Kwa vous oriente vers la bonne page "
            "(inscription, panier, vendeur, Culture…).",
            body,
        )
    )
    subsection("11.2 FAQ et contact")
    bullets(
        [
            f"<b>FAQ :</b> {SITE}/page/faq/ — réponses aux questions fréquentes",
            f"<b>Contact :</b> {SITE}/page/contact/",
            f"<b>Conditions générales :</b> {SITE}/page/conditions-generales/",
            f"<b>Confidentialité :</b> {SITE}/page/confidentialite/",
            "<b>E-mail :</b> kwakolegroup@gmail.com",
            "<b>Téléphone / WhatsApp :</b> 07 99 63 31 13",
        ]
    )
    subsection("11.3 Installer Kolê Group sur votre téléphone")
    steps(
        [
            "1. Ouvrez kolêgroup.com dans Chrome (Android) ou Safari (iPhone).",
            "2. Sur Android : un bouton <b>Installer Kolê Group</b> peut apparaître en bas.",
            "3. Sur iPhone : bouton <b>Partager</b> → <b>Sur l'écran d'accueil</b>.",
            "4. L'icône Kolê s'ajoute comme une application — accès rapide sans retaper l'adresse.",
        ]
    )
    story.append(PageBreak())

    # ── 12. Récap ──
    section("12. Récapitulatif des adresses utiles")
    recap = [
        ["Page", "Adresse complète"],
        ["Accueil", f"{SITE}/"],
        ["Produits", f"{SITE}/produits/"],
        ["Panier", f"{SITE}/panier/"],
        ["Inscription", f"{SITE}/compte/inscription/"],
        ["Connexion", f"{SITE}/compte/connexion/"],
        ["Mon profil", f"{SITE}/compte/profil/"],
        ["Mes commandes", f"{SITE}/compte/commandes/"],
        ["Mes réservations", f"{SITE}/compte/reservations/"],
        ["Devenir vendeur", f"{SITE}/vendeur/inscription/"],
        ["Devenir prestataire", f"{SITE}/vendeur/prestataire/inscription/"],
        ["Kolê Culture", f"{SITE}/culture/"],
        ["FAQ", f"{SITE}/page/faq/"],
        ["Contact", f"{SITE}/page/contact/"],
    ]
    t = Table(recap, colWidths=[4.5 * cm, 12 * cm])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#fff7ed")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e7e5e4")),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(t)
    story.append(Spacer(1, 1 * cm))
    story.append(
        Paragraph(
            f"<b>Kolê Group</b> — {SITE_DISPLAY}<br/>"
            "Ce guide peut être partagé, imprimé ou diffusé à vos clients et partenaires.<br/>"
            "Pour toute question : kwakolegroup@gmail.com · 07 99 63 31 13",
            ParagraphStyle("Fin", parent=styles["Normal"], fontSize=9, alignment=TA_CENTER, textColor=colors.HexColor("#6b5f54")),
        )
    )

    def _footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.grey)
        canvas.drawString(2 * cm, 1.2 * cm, f"Kolê Group — Guide utilisateur — {SITE_DISPLAY}")
        canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"Page {doc.page}")
        canvas.restoreState()

    doc = SimpleDocTemplate(
        str(OUT),
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2.2 * cm,
        title="Guide utilisateur Kolê Group",
        author="Kolê Group",
    )
    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    print(f"PDF créé : {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
