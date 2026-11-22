"""Vues publiques Dan Prestige Magazine."""

from __future__ import annotations

from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.core.mail import mail_admins
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from kwalo.contact_info import MAGAZINE_EDITORIAL

from .forms import (
    MagazineNewsletterForm,
    MagazineSubscribeForm,
    PartnershipInquiryForm,
    PersonalitySubmissionForm,
)
from .helpers import public_queryset, whatsapp_share_url
from .models import (
    Article,
    MagazineIssue,
    MagazineNewsletterSignup,
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
    {"icon": "interview", "title": "Interviews vidéo", "text": "Rencontres filmées avec les figures qui font bouger la communauté Dan."},
    {"icon": "reportage", "title": "Reportages", "text": "Enquêtes et récits de terrain sur les enjeux locaux et diaspora."},
    {"icon": "portrait", "title": "Portraits photographiques", "text": "Une galerie élégante des personnalités et talents."},
    {"icon": "emission", "title": "Émissions spéciales", "text": "Formats longs pour approfondir les réussites et les projets."},
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
        "editorial": MAGAZINE_EDITORIAL,
        "newsletter_form": MagazineNewsletterForm(),
        **extra,
    }


def _articles_qs():
    return public_queryset(Article.objects.filter(is_published=True))


def _videos_qs():
    return public_queryset(Video.objects.filter(is_published=True))


def _portraits_qs():
    return public_queryset(Portrait.objects.filter(is_published=True))


def _personalities_qs():
    return public_queryset(Personality.objects.filter(consent_validated=True))


def _partners_qs():
    return public_queryset(Partner.objects.filter(is_active=True))


def _latest_issue():
    latest = MagazineIssue.objects.filter(is_published=True, is_latest=True).select_related("product").first()
    if not latest:
        latest = MagazineIssue.objects.filter(is_published=True).select_related("product").first()
    return latest


def home(request):
    latest_issue = _latest_issue()
    buy_url = None
    if latest_issue and latest_issue.product_id and getattr(latest_issue.product, "slug", None):
        from django.urls import reverse

        buy_url = reverse("store:product_detail", args=[latest_issue.product.slug])

    newsletter_form = MagazineNewsletterForm(request.POST or None)
    if request.method == "POST" and request.POST.get("form_kind") == "newsletter":
        if newsletter_form.is_valid():
            email = newsletter_form.cleaned_data["email"]
            obj, created = MagazineNewsletterSignup.objects.get_or_create(
                email=email,
                defaults={"full_name": newsletter_form.cleaned_data.get("full_name") or ""},
            )
            if not created:
                obj.is_active = True
                if newsletter_form.cleaned_data.get("full_name"):
                    obj.full_name = newsletter_form.cleaned_data["full_name"]
                obj.save()
            messages.success(request, "Merci ! Vous êtes inscrit(e) à la newsletter Dan Prestige.")
            return redirect("magazine:home")
        messages.error(request, "Vérifiez votre adresse e-mail pour la newsletter.")

    return render(
        request,
        "magazine/home.html",
        _base_ctx(
            latest_issue=latest_issue,
            buy_url=buy_url,
            content_types=CONTENT_TYPES,
            impact_points=IMPACT_POINTS,
            articles=_articles_qs()[:3],
            videos=_videos_qs()[:3],
            portraits=_portraits_qs()[:4],
            partners=_partners_qs()[:8],
            plans=MagazineSubscriptionPlan.objects.filter(is_active=True)[:2],
            newsletter_form=newsletter_form,
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
    issues = MagazineIssue.objects.filter(is_published=True).select_related("product")
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
    qs = _articles_qs()
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
        _articles_qs()
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
    qs = _articles_qs().select_related("sponsor")
    article = get_object_or_404(qs, slug=slug)
    related = _articles_qs().exclude(pk=article.pk)[:3]
    share_url = request.build_absolute_uri(article.get_absolute_url())
    return render(
        request,
        "magazine/article_detail.html",
        _base_ctx(
            article=article,
            related=related,
            share_whatsapp=whatsapp_share_url(article.title, share_url),
            canonical_url=share_url,
        ),
    )


def video_list(request):
    qs = _videos_qs()
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
    video = get_object_or_404(_videos_qs().select_related("sponsor"), slug=slug)
    share_url = request.build_absolute_uri(video.get_absolute_url())
    return render(
        request,
        "magazine/video_detail.html",
        _base_ctx(
            video=video,
            share_whatsapp=whatsapp_share_url(video.title, share_url),
            canonical_url=share_url,
        ),
    )


def portrait_list(request):
    qs = _portraits_qs()
    locality = (request.GET.get("localite") or "").strip()
    if locality:
        qs = qs.filter(locality__icontains=locality)
    return render(
        request,
        "magazine/portrait_list.html",
        _base_ctx(portraits=qs, filters={"localite": locality}),
    )


def portrait_detail(request, slug):
    portrait = get_object_or_404(_portraits_qs().select_related("sponsor"), slug=slug)
    share_url = request.build_absolute_uri(portrait.get_absolute_url())
    return render(
        request,
        "magazine/portrait_detail.html",
        _base_ctx(
            portrait=portrait,
            share_whatsapp=whatsapp_share_url(portrait.title, share_url),
            canonical_url=share_url,
        ),
    )


def repertoire(request):
    qs = _personalities_qs()
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
    person = get_object_or_404(_personalities_qs(), slug=slug)
    share_url = request.build_absolute_uri(person.get_absolute_url())
    return render(
        request,
        "magazine/personality_detail.html",
        _base_ctx(
            person=person,
            share_whatsapp=whatsapp_share_url(person.full_name, share_url),
            canonical_url=share_url,
        ),
    )


def referencement(request):
    form = PersonalitySubmissionForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        submission = form.save()
        try:
            mail_admins(
                subject=f"[Dan Prestige] Demande de référencement — {submission.full_name}",
                message=(
                    f"Nouvelle demande en attente.\n\n"
                    f"Nom : {submission.full_name}\n"
                    f"Profession : {submission.profession}\n"
                    f"Localité : {submission.locality}\n"
                    f"E-mail : {submission.email}\n"
                    f"Téléphone : {submission.phone}\n\n"
                    f"Parcours :\n{submission.bio}\n"
                ),
                fail_silently=True,
            )
        except Exception:
            pass
        messages.success(
            request,
            "Votre demande a été envoyée. Elle sera examinée par la rédaction avant publication.",
        )
        return redirect("magazine:referencement")
    return render(
        request,
        "magazine/referencement.html",
        _base_ctx(form=form),
    )


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
            partners=_partners_qs(),
        ),
    )


@require_POST
def newsletter_signup(request):
    form = MagazineNewsletterForm(request.POST)
    next_url = request.POST.get("next") or "magazine:home"
    if form.is_valid():
        email = form.cleaned_data["email"]
        obj, created = MagazineNewsletterSignup.objects.get_or_create(
            email=email,
            defaults={"full_name": form.cleaned_data.get("full_name") or ""},
        )
        if not created:
            obj.is_active = True
            if form.cleaned_data.get("full_name"):
                obj.full_name = form.cleaned_data["full_name"]
            obj.save()
        messages.success(request, "Merci ! Vous êtes inscrit(e) à la newsletter Dan Prestige.")
    else:
        messages.error(request, "Vérifiez votre adresse e-mail pour la newsletter.")
    if next_url.startswith("/"):
        return redirect(next_url)
    return redirect(next_url)


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
