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
SITE = "https://xn--kolgroup-m1a.com"


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
        fontSize=22,
        spaceAfter=12,
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
    url_style = ParagraphStyle(
        "URL",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#c2410c"),
        alignment=TA_CENTER,
    )

    story: list = []
    page_w = A4[0] - 4 * cm

    # ── Couverture ──
    story.append(Spacer(1, 2.5 * cm))
    logo = _img(ROOT / "static" / "images" / "icons" / "icon-192.png", 3.2)
    if logo:
        story.append(logo)
        story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph("Guide utilisateur", title))
    story.append(Paragraph("Kolê Group — Marketplace Afro-moderne", cover_sub))
    story.append(
        Paragraph(
            "Acheter · Réserver · Célébrer",
            ParagraphStyle("Tag", parent=cover_sub, fontSize=11, textColor=colors.HexColor("#d4a24c")),
        )
    )
    story.append(Spacer(1, 0.6 * cm))
    story.append(Paragraph(f"<b>Site :</b> {SITE}", url_style))
    story.append(
        Paragraph(
            f"Document généré le {date.today().strftime('%d/%m/%Y')} — "
            "pour clients, vendeurs, prestataires et artistes.",
            ParagraphStyle("Meta", parent=styles["Normal"], fontSize=8, textColor=colors.grey, alignment=TA_CENTER),
        )
    )
    story.append(PageBreak())

    # ── 1. Introduction ──
    story.append(Paragraph("1. Bienvenue sur Kolê Group", h2))
    story.append(
        Paragraph(
            "Kolê Group rassemble sur une seule plateforme les <b>boutiques locales</b>, "
            "les <b>artisans</b>, les <b>prestataires de services</b> et l'univers "
            "<b>Culture</b> (musique, concerts, artistes). Que vous souhaitiez acheter, "
            "vendre, proposer un service ou publier votre musique, ce guide vous indique "
            "où aller et comment démarrer.",
            body,
        )
    )
    img = _img(AFFICHES / "affiche-fonctionnement-profils.png", 16)
    if img:
        story.append(Spacer(1, 0.3 * cm))
        story.append(img)
    story.append(PageBreak())

    # ── 2. Se connecter ──
    story.append(Paragraph("2. Créer un compte et se connecter", h2))
    story.append(Paragraph("2.1 Inscription (nouveau compte)", h3))
    for line in [
        f"1. Ouvrez <b>{SITE}</b> dans votre navigateur (Chrome, Safari, Firefox…).",
        "2. En haut à droite, cliquez sur <b>Compte</b>, puis <b>Créer un compte</b>.",
        f"3. Ou allez directement à : <b>{SITE}/compte/inscription/</b>",
        "4. Renseignez email, nom d'utilisateur et mot de passe, puis validez.",
        "5. Vérifiez votre boîte mail et cliquez sur le lien de confirmation.",
        "6. Vous pouvez aussi vous inscrire avec <b>Google</b> ou <b>Facebook</b>.",
    ]:
        story.append(Paragraph(line, step))

    story.append(Paragraph("2.2 Connexion (déjà inscrit)", h3))
    for line in [
        "1. Cliquez sur <b>Compte → Connexion</b> en haut de la page.",
        f"2. Ou : <b>{SITE}/compte/connexion/</b>",
        "3. Saisissez votre identifiant (email ou nom d'utilisateur) et mot de passe.",
        "4. Sur mobile : utilisez l'icône <b>Compte</b> dans la barre du bas.",
    ]:
        story.append(Paragraph(line, step))

    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph("2.3 Mot de passe oublié", h3))
    story.append(
        Paragraph(
            "Sur la page de connexion, utilisez le lien <b>Mot de passe oublié ?</b> "
            "et suivez les instructions reçues par email.",
            body,
        )
    )
    story.append(PageBreak())

    # ── 3. Navigation ──
    story.append(Paragraph("3. Naviguer sur le site", h2))
    nav_data = [
        ["Zone", "Où cliquer", "À quoi ça sert"],
        ["Accueil", "Logo Kolê ou barre du bas « Accueil »", "Page d'accueil, offres, catégories"],
        ["Explorer", "Barre du bas ou menu « Explorer »", "Tous les produits et services"],
        ["Recherche", "Barre en haut de page", "Chercher un produit, une boutique, un service"],
        ["Panier", "Icône panier (barre du haut ou du bas)", "Voir et valider vos achats"],
        ["Favoris", "Icône cœur", "Produits enregistrés pour plus tard"],
        ["Compte", "Menu Compte (en haut) ou barre du bas", "Profil, commandes, réservations"],
        ["Culture", "Bouton « Culture » dans le menu", "Musique, concerts, artistes"],
        ["Aide", "Menu Aide", "FAQ, contact, conditions générales"],
        ["Assistant Kwa", "Bulle orange en bas à droite", "Questions fréquentes, aide rapide"],
    ]
    t = Table(nav_data, colWidths=[3.2 * cm, 5.5 * cm, 7.8 * cm])
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
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(t)
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph("Pages utiles (adresses directes)", h3))
    pages = [
        f"<b>Accueil :</b> {SITE}/",
        f"<b>Produits :</b> {SITE}/produits/",
        f"<b>Panier :</b> {SITE}/panier/",
        f"<b>Mon profil :</b> {SITE}/compte/profil/",
        f"<b>Mes commandes :</b> {SITE}/compte/commandes/",
        f"<b>FAQ :</b> {SITE}/page/faq/",
        f"<b>Contact :</b> {SITE}/page/contact/",
    ]
    for p in pages:
        story.append(Paragraph(f"• {p}", bullet))
    story.append(PageBreak())

    # ── 4. Comment ça marche ──
    story.append(Paragraph("4. Comment ça marche ? (vue d'ensemble)", h2))
    img = _img(AFFICHES / "affiche-fonctionnement-vue-ensemble.png", 16)
    if img:
        story.append(img)
    story.append(Spacer(1, 0.2 * cm))
    for line in [
        "<b>Étape 1</b> — Créez votre compte et vérifiez votre email.",
        "<b>Étape 2</b> — Explorez les catégories, produits et services.",
        "<b>Étape 3</b> — Recevez vos achats ou réservez un service en ligne.",
    ]:
        story.append(Paragraph(f"• {line}", bullet))
    story.append(PageBreak())

    # ── 5. Client ──
    story.append(Paragraph("5. Je suis client — Acheter ou réserver", h2))
    img = _img(AFFICHES / "affiche-fonctionnement-client.png", 16)
    if img:
        story.append(img)
        story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph("Parcours en 5 étapes", h3))
    for line in [
        "<b>1. Inscription & connexion</b> — Créez un compte ou connectez-vous.",
        "<b>2. Parcourir</b> — Catégories, recherche, fiches produit ou service.",
        "<b>3. Panier ou réservation</b> — Ajoutez au panier OU choisissez une date pour un service.",
        "<b>4. Payer</b> — Paiement sécurisé (GeniusPay) ou à la livraison selon l'offre.",
        "<b>5. Suivi</b> — Menu Compte → Mes commandes / Mes réservations.",
    ]:
        story.append(Paragraph(line, step))
    story.append(
        Paragraph(
            "<i>Livraison gratuite dès 15 000 FCFA sur les commandes éligibles.</i>",
            ParagraphStyle("Note", parent=body, fontSize=9, textColor=colors.grey),
        )
    )
    story.append(PageBreak())

    # ── 6. Vendeur & Prestataire ──
    story.append(Paragraph("6. Je veux vendre ou proposer un service", h2))
    img = _img(AFFICHES / "affiche-fonctionnement-vendeur-prestataire.png", 16)
    if img:
        story.append(img)
        story.append(Spacer(1, 0.2 * cm))

    story.append(Paragraph("6.1 Devenir vendeur (boutique en ligne)", h3))
    for line in [
        "1. Créez un compte client et connectez-vous.",
        f"2. Menu <b>Compte → Devenir vendeur</b> ou {SITE}/vendeur/inscription/",
        "3. Remplissez le formulaire (boutique, identité, documents KYC).",
        "4. Choisissez une formule d'abonnement (Starter, Pro ou Premium).",
        "5. Accédez à l'<b>espace vendeur</b> : ajoutez vos produits, gérez les commandes.",
        f"6. Tableau de bord : {SITE}/vendeur/dashboard/",
    ]:
        story.append(Paragraph(line, step))

    story.append(Paragraph("6.2 Devenir prestataire de services", h3))
    for line in [
        "1. Créez un compte et connectez-vous.",
        f"2. Menu <b>Compte → Devenir prestataire</b> ou {SITE}/vendeur/prestataire/inscription/",
        "3. Décrivez vos services, zone d'intervention et tarifs.",
        "4. Choisissez une formule d'abonnement.",
        "5. Publiez vos services et gérez les demandes clients.",
        f"6. Tableau de bord : {SITE}/vendeur/prestataire/dashboard/",
    ]:
        story.append(Paragraph(line, step))
    story.append(PageBreak())

    # ── 7. Culture ──
    story.append(Paragraph("7. Kolê Culture — Musique & concerts", h2))
    img = _img(AFFICHES / "affiche-fonctionnement-culture.png", 16)
    if img:
        story.append(img)
        story.append(Spacer(1, 0.2 * cm))
    for line in [
        f"<b>Explorer :</b> {SITE}/culture/ — musique, événements, artistes.",
        "<b>Écouter & acheter</b> des titres d'artistes ivoiriens.",
        "<b>Billets de concert</b> avec QR code scanné à l'entrée.",
        "<b>Devenir artiste :</b> Compte → Activer profil artiste → Espace artiste.",
        f"<b>Mes billets :</b> {SITE}/compte/ (menu Culture) — Mes billets / Mes achats musique.",
    ]:
        story.append(Paragraph(f"• {line}", bullet))
    story.append(PageBreak())

    # ── 8. Aide ──
    story.append(Paragraph("8. Besoin d'aide ?", h2))
    story.append(
        Paragraph(
            "• <b>Assistant Kwa</b> — bulle en bas à droite sur le site, réponses automatiques.<br/>"
            f"• <b>FAQ :</b> {SITE}/page/faq/<br/>"
            f"• <b>Contact :</b> {SITE}/page/contact/<br/>"
            f"• <b>Conditions générales :</b> {SITE}/page/conditions-generales/<br/>"
            "• <b>Installer l'app</b> — sur mobile, bouton « Installer Kolê Group » ou ajout à l'écran d'accueil.",
            body,
        )
    )
    story.append(Spacer(1, 0.5 * cm))
    story.append(
        Paragraph(
            f"<b>Kolê Group</b> — {SITE}<br/>"
            "Ce guide peut être partagé, imprimé ou diffusé à vos clients et partenaires.",
            ParagraphStyle("Fin", parent=styles["Normal"], fontSize=9, alignment=TA_CENTER, textColor=colors.HexColor("#6b5f54")),
        )
    )

    def _footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.grey)
        canvas.drawString(2 * cm, 1.2 * cm, f"Kolê Group — Guide utilisateur — {SITE}")
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
