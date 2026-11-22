"""Vues publiques Dan Prestige Magazine."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import MagazineSubscribeForm, PartnershipInquiryForm
from .models import (
    Article,
    MagazineIssue,
    MagazineSubscription,
    MagazineSubscriptionPlan,
    Partner,
    Personality,
    Portrait,
    TeamMember,
    Video,
)

VISION = (
    "Devenir la principale plateforme médiatique de référence consacrée à la connaissance, "
    "à la valorisation et à la promotion des personnalités, des talents et des réussites "
    "du peuple Dan, en Côte d'Ivoire et dans la diaspora."
)

IMPACT_POINTS = [
    "Constituer un répertoire des personnalités et compétences Dan",
    "Renforcer les liens entre cadres, élus, artistes et populations",
    "Rapprocher la diaspora de ses terres d'origine",
    "Susciter des opportunités de collaboration et d'investissement",
    "Transmettre aux générations futures les parcours des personnalités marquantes",
    "Contribuer à une meilleure visibilité de l'Ouest montagneux",
]

CONTENT_TYPES = [
    {"icon": "🎥", "title": "Interviews vidéo", "text": "Rencontres filmées avec les figures qui font bouger la communauté Dan."},
    {"icon": "📰", "title": "Reportages", "text": "Enquêtes et récits de terrain sur les enjeux locaux et diaspora."},
    {"icon": "📷", "title": "Portraits photographiques", "text": "Une galerie élégante des personnalités et talents."},
    {"icon": "🎙️", "title": "Émissions spéciales", "text": "Formats longs pour approfondir les réussites et les projets."},
]

CHARTE_POINTS = [
    {
        "title": "Neutralité politique et indépendance éditoriale",
        "text": "Dan Prestige Magazine n'est affilié à aucun parti. Les choix éditoriaux relèvent exclusivement de la rédaction.",
    },
    {
        "title": "Vérification des informations et des parcours",
        "text": "Chaque fiche et chaque article font l'objet d'une vérification des sources avant publication.",
    },
    {
        "title": "Respect de la vie privée et de la dignité",
        "text": "Nous traitons les personnes avec respect ; aucune information sensible n'est publiée sans justification éditoriale claire.",
    },
    {
        "title": "Équité dans la représentation",
        "text": "Nous veillons à une représentation équilibrée des localités, des générations et des domaines d'activité.",
    },
    {
        "title": "Consentement",
        "text": "Les portraits et informations non publiques nécessitent un consentement explicite et validé.",
    },
    {
        "title": "Information vs communication commerciale",
        "text": "Les publireportages et contenus sponsorisés sont clairement identifiés et distincts du journalisme.",
    },
]

PARTNERSHIP_OFFERS = [
    {"title": "Espaces publicitaires", "text": "Pages et encarts dans le magazine papier et sur le site."},
    {"title": "Publireportages", "text": "Contenus éditoriaux sponsorisés, signalés comme tels."},
    {"title": "Sponsoring d'éditions spéciales", "text": "Associéz votre marque à un numéro thématique."},
    {"title": "Couverture d'événements", "text": "Reportages photo et vidéo autour de vos manifestations."},
    {"title": "Partenariats institutionnels", "text": "Collaborations avec associations, mutuelles et collectivités."},
]


def _base_ctx(**extra):
    return {
        "magazine_name": "Dan Prestige Magazine",
        "vision": VISION,
        **extra,
    }


def home(request):
    latest_issue = MagazineIssue.objects.filter(is_published=True, is_latest=True).first()
    if not latest_issue:
        latest_issue = MagazineIssue.objects.filter(is_published=True).first()
    return render(
        request,
        "magazine/home.html",
        _base_ctx(
            latest_issue=latest_issue,
            content_types=CONTENT_TYPES,
            impact_points=IMPACT_POINTS,
            articles=Article.objects.filter(is_published=True)[:3],
            videos=Video.objects.filter(is_published=True)[:3],
            portraits=Portrait.objects.filter(is_published=True)[:4],
            partners=Partner.objects.filter(is_active=True)[:8],
            plans=MagazineSubscriptionPlan.objects.filter(is_active=True)[:2],
        ),
    )


def team(request):
    return render(
        request,
        "magazine/team.html",
        _base_ctx(members=TeamMember.objects.filter(is_active=True)),
    )


def charter(request):
    return render(
        request,
        "magazine/charter.html",
        _base_ctx(charter_points=CHARTE_POINTS),
    )


def boutique(request):
    issues = MagazineIssue.objects.filter(is_published=True)
    plans = MagazineSubscriptionPlan.objects.filter(is_active=True)
    subscribe_form = MagazineSubscribeForm(
        initial={"plan": plans.filter(is_featured=True).first() or plans.first()}
    )
    return render(
        request,
        "magazine/boutique.html",
        _base_ctx(issues=issues, plans=plans, subscribe_form=subscribe_form),
    )


@require_POST
def subscribe(request):
    form = MagazineSubscribeForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Vérifiez le formulaire d'abonnement.")
        return redirect("magazine:boutique")

    plan = form.cleaned_data["plan"]
    sub = MagazineSubscription.objects.create(
        user=request.user if request.user.is_authenticated else None,
        plan=plan,
        email=form.cleaned_data["email"],
        full_name=form.cleaned_data["full_name"],
        phone=form.cleaned_data.get("phone") or "",
        amount_fcfa=plan.price_fcfa,
        status=MagazineSubscription.STATUS_PENDING,
    )

    # Activation démo / sandbox : sans flux Genius dédié magazine, on active directement
    # si le montant est 0, sinon on marque actif en mode DEBUG pour faciliter les tests.
    from django.conf import settings

    if plan.price_fcfa <= 0 or settings.DEBUG:
        now = timezone.now()
        delta = timedelta(days=365) if plan.period == plan.PERIOD_YEARLY else timedelta(days=30)
        sub.status = MagazineSubscription.STATUS_ACTIVE
        sub.starts_at = now
        sub.ends_at = now + delta
        sub.save(update_fields=["status", "starts_at", "ends_at"])
        messages.success(
            request,
            f"Abonnement « {plan.name} » enregistré (réf. {sub.reference}). "
            + ("Activation immédiate (mode test)." if settings.DEBUG else "Bienvenue !"),
        )
    else:
        messages.success(
            request,
            f"Demande d'abonnement enregistrée (réf. {sub.reference}). "
            "Notre équipe vous contactera pour finaliser le paiement Mobile Money.",
        )
    return redirect("magazine:boutique")


def article_list(request):
    qs = Article.objects.filter(is_published=True)
    category = (request.GET.get("categorie") or "").strip()
    locality = (request.GET.get("localite") or "").strip()
    q = (request.GET.get("q") or "").strip()
    if category:
        qs = qs.filter(category=category)
    if locality:
        qs = qs.filter(locality__icontains=locality)
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(excerpt__icontains=q) | Q(body__icontains=q))
    localities = (
        Article.objects.filter(is_published=True)
        .exclude(locality="")
        .values_list("locality", flat=True)
        .distinct()
        .order_by("locality")
    )
    return render(
        request,
        "magazine/article_list.html",
        _base_ctx(
            articles=qs,
            categories=Article.CATEGORY_CHOICES,
            localities=localities,
            filters={"categorie": category, "localite": locality, "q": q},
        ),
    )


def article_detail(request, slug):
    article = get_object_or_404(Article, slug=slug, is_published=True)
    related = Article.objects.filter(is_published=True).exclude(pk=article.pk)[:3]
    return render(
        request,
        "magazine/article_detail.html",
        _base_ctx(article=article, related=related),
    )


def video_list(request):
    qs = Video.objects.filter(is_published=True)
    kind = (request.GET.get("type") or "").strip()
    locality = (request.GET.get("localite") or "").strip()
    if kind:
        qs = qs.filter(kind=kind)
    if locality:
        qs = qs.filter(locality__icontains=locality)
    return render(
        request,
        "magazine/video_list.html",
        _base_ctx(
            videos=qs,
            kinds=Video.KIND_CHOICES,
            filters={"type": kind, "localite": locality},
        ),
    )


def video_detail(request, slug):
    video = get_object_or_404(Video, slug=slug, is_published=True)
    return render(request, "magazine/video_detail.html", _base_ctx(video=video))


def portrait_list(request):
    qs = Portrait.objects.filter(is_published=True)
    locality = (request.GET.get("localite") or "").strip()
    if locality:
        qs = qs.filter(locality__icontains=locality)
    return render(
        request,
        "magazine/portrait_list.html",
        _base_ctx(portraits=qs, filters={"localite": locality}),
    )


def portrait_detail(request, slug):
    portrait = get_object_or_404(Portrait, slug=slug, is_published=True)
    return render(request, "magazine/portrait_detail.html", _base_ctx(portrait=portrait))


def repertoire(request):
    qs = Personality.objects.filter(consent_validated=True)
    q = (request.GET.get("q") or "").strip()
    locality = (request.GET.get("localite") or "").strip()
    profession = (request.GET.get("profession") or "").strip()
    if q:
        qs = qs.filter(
            Q(first_name__icontains=q)
            | Q(last_name__icontains=q)
            | Q(profession__icontains=q)
            | Q(bio__icontains=q)
        )
    if locality:
        qs = qs.filter(Q(locality__icontains=locality) | Q(region__icontains=locality))
    if profession:
        qs = qs.filter(profession__icontains=profession)
    return render(
        request,
        "magazine/repertoire.html",
        _base_ctx(
            personalities=qs,
            filters={"q": q, "localite": locality, "profession": profession},
        ),
    )


def personality_detail(request, slug):
    person = get_object_or_404(Personality, slug=slug, consent_validated=True)
    return render(request, "magazine/personality_detail.html", _base_ctx(person=person))


def partners(request):
    form = PartnershipInquiryForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Votre demande a bien été envoyée. Nous vous recontacterons.")
        return redirect("magazine:partners")
    return render(
        request,
        "magazine/partners.html",
        _base_ctx(
            form=form,
            offers=PARTNERSHIP_OFFERS,
            partners=Partner.objects.filter(is_active=True),
        ),
    )


@require_POST
def add_issue_to_cart(request, issue_id):
    """Ajoute le produit lié au numéro dans le panier store existant."""
    issue = get_object_or_404(MagazineIssue, pk=issue_id, is_published=True)
    if not issue.product_id:
        messages.error(
            request,
            "Ce numéro n'est pas encore disponible à l'achat en ligne. Contactez-nous.",
        )
        return redirect("magazine:boutique")
    cart = request.session.get("cart", {})
    key = str(issue.product_id)
    cart[key] = cart.get(key, 0) + 1
    request.session["cart"] = cart
    request.session.modified = True
    messages.success(
        request,
        f"Le numéro « {issue.title} » a été ajouté au panier.",
    )
    return redirect("store:cart_detail")
