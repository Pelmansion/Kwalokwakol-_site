#!/usr/bin/env python3
"""
Génère un PDF de description du projet KwaloKWakolê (Django).
Usage : depuis la racine du projet : python scripts/generate_projet_pdf.py
Sortie : docs/Description_Projet_KwaloKWakole.pdf
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "Description_Projet_KwaloKWakole.pdf"


def main() -> int:
    try:
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import cm
        from reportlab.platypus import (
            Paragraph,
            SimpleDocTemplate,
            Spacer,
            Table,
            TableStyle,
        )
    except ImportError:
        print("Installez les dépendances : pip install reportlab", file=sys.stderr)
        return 1

    OUT.parent.mkdir(parents=True, exist_ok=True)

    styles = getSampleStyleSheet()
    title = ParagraphStyle(
        "Titre",
        parent=styles["Heading1"],
        fontSize=18,
        spaceAfter=16,
        textColor=colors.HexColor("#9a3412"),
    )
    h2 = ParagraphStyle(
        "H2",
        parent=styles["Heading2"],
        fontSize=13,
        spaceBefore=14,
        spaceAfter=8,
        textColor=colors.HexColor("#c2410c"),
    )
    body = ParagraphStyle(
        "Corps",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        alignment=TA_JUSTIFY,
        spaceAfter=8,
    )
    bullet = ParagraphStyle(
        "Puce",
        parent=styles["Normal"],
        fontSize=10,
        leading=13,
        leftIndent=12,
        bulletIndent=6,
    )

    story: list = []

    story.append(Paragraph("KwaloKWakolê Group", title))
    story.append(
        Paragraph(
            "Description du projet &mdash; plateforme e-commerce et culture "
            "(document généré automatiquement).",
            ParagraphStyle("Soustitre", parent=styles["Normal"], fontSize=9, textColor=colors.grey),
        )
    )
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("1. Vue d'ensemble", h2))
    story.append(
        Paragraph(
            "Le projet est une application web <b>Django 6</b> dédiée à une marketplace "
            "afro-moderne : produits locaux, artisans, boutiques, prestataires de services, "
            "ainsi qu'un espace <b>Culture</b> (musique, artistes, concerts et billets avec QR). "
            "L'interface inclut une <b>PWA</b> (installation mobile), un assistant conversationnel "
            "<b>Kwa</b> (FAQ), et des flux de paiement incluant <b>GeniusPay</b> pour le e-commerce "
            "et les abonnements, avec possibilité de paiement à la livraison.",
            body,
        )
    )

    story.append(Paragraph("2. Fonctionnalités principales", h2))
    items = [
        "<b>Boutique</b> : catalogue, catégories, panier, favoris, commandes clients.",
        "<b>Marketplace</b> : vendeurs et prestataires, tableaux de bord, demandes de service.",
        "<b>Abonnements</b> : formules vendeur/prestataire, montants paramétrables par l'admin, paiement (GeniusPay ou simulation).",
        "<b>Culture</b> : profils artistes, catalogue musical, événements, achat de billets et QR.",
        "<b>Comptes</b> : inscription, django-allauth (Google, Facebook), rôles client / vendeur / prestataire / admin.",
        "<b>Paiements commandes</b> : GeniusPay (checkout) ou espèces à la livraison ; webhooks et pages de retour.",
        "<b>Avis, messagerie, notifications</b> : engagement utilisateurs autour des commandes.",
    ]
    for t in items:
        story.append(Paragraph(f"• {t}", bullet))
    story.append(Spacer(1, 0.2 * cm))

    story.append(Paragraph("3. Structure technique (applications Django)", h2))
    data = [
        ["Composant", "Rôle"],
        ["kwalo/", "Configuration (settings, URLs racine, middleware, static)."],
        ["store/, catalog/", "Vitrine, liste produits, panier, checkout, catégories."],
        ["marketplace/", "Vendeurs, prestataires, inscriptions, dashboards."],
        ["orders/", "Commandes et statuts."],
        ["payments/", "Paiements (GeniusPay, webhooks, retours utilisateur)."],
        ["subscriptions/", "Plans, abonnements, paiements récurrents / Genius."],
        ["culture/", "Artistes, musique, concerts, billets, QR."],
        ["accounts/", "Profils, authentification, espace admin métier."],
        ["reviews/, messaging/, notifications/", "Avis, fil de discussion, alertes."],
        ["content/", "Pages éditoriales simples."],
        ["templates/, static/", "Thème UI, PWA (manifest, service worker), chatbot JS."],
        ["frontend/", "Assets React / Vite (intégration sélective sur certaines pages)."],
    ]
    t = Table(data, colWidths=[4.2 * cm, 12.3 * cm])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#fff7ed")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#9a3412")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 10),
                ("FONTSIZE", (0, 1), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e7e5e4")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(t)
    story.append(Spacer(1, 0.3 * cm))

    story.append(Paragraph("4. Prérequis & déploiement", h2))
    story.append(
        Paragraph(
            "<b>Python 3.12+</b>, PostgreSQL en production (dj-database-url), variables d'environnement "
            "pour les secrets (SECRET_KEY, DATABASE_URL, clés GeniusPay GENIUS_API_KEY / GENIUS_API_SECRET, "
            "webhook GENIUS_WEBHOOK_SECRET, email SMTP). "
            "Fichiers statiques via WhiteNoise ; HTTPS et CSRF_TRUSTED_ORIGINS configurés pour le domaine public.",
            body,
        )
    )

    story.append(Paragraph("5. Installation locale (rappel)", h2))
    for line in [
        "1. Créer un environnement virtuel et <b>pip install -r requirements.txt</b>.",
        "2. Copier <b>.env.example</b> vers <b>.env</b> et renseigner les variables.",
        "3. Exécuter <b>python manage.py migrate</b> puis <b>python manage.py runserver</b>.",
        "4. Optionnel : <b>python manage.py seed_test_data</b> pour des données de démonstration.",
    ]:
        story.append(Paragraph(line, bullet))
    story.append(Spacer(1, 0.2 * cm))

    story.append(Paragraph("6. Points d'entrée URL (racine)", h2))
    urls_txt = (
        "<b>/admin/</b> &mdash; Administration Django ; "
        "<b>/compte/</b> &mdash; Comptes ; "
        "<b>/vendeur/</b> &mdash; Marketplace ; "
        "<b>/paiement/</b> &mdash; Paiements ; "
        "<b>/abonnement/</b> &mdash; Abonnements ; "
        "<b>/culture/</b> &mdash; Culture ; "
        "<b>/messagerie/</b>, <b>/notifications/</b>, <b>/avis/</b> ; "
        "<b>/</b> &mdash; Store (accueil, produits, panier). "
        "Fichiers PWA : manifest.webmanifest, sw.js, hors-ligne/."
    )
    story.append(Paragraph(urls_txt, body))

    story.append(Spacer(1, 0.5 * cm))
    story.append(
        Paragraph(
            f"<i>Fichier généré : {OUT.name} &mdash; emplacement : docs/</i>",
            ParagraphStyle("Fin", parent=styles["Normal"], fontSize=8, textColor=colors.grey, alignment=TA_LEFT),
        )
    )

    doc = SimpleDocTemplate(
        str(OUT),
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title="Description du projet KwaloKWakolê",
        author="KwaloKWakolê Group",
    )
    doc.build(story)
    print(f"PDF créé : {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
