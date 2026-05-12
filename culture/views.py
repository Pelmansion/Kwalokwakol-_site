from __future__ import annotations

from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count, F, Q, Sum
from django.http import FileResponse, Http404, HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from payments.genius import (
    GeniusPaymentError,
    create_checkout_payment,
    fetch_payment,
    is_configured as genius_is_configured,
)

from .forms import (
    ArtistProfileForm,
    EventForm,
    SongForm,
    TicketBuyerForm,
    TicketCategoryForm,
)
from .models import (
    ArtistProfile,
    Event,
    MusicGenre,
    Song,
    SongPlay,
    SongPurchase,
    Ticket,
    TicketCategory,
)
from .utils import (
    generate_qr_svg,
    get_artist_or_redirect,
    require_artist,
    user_can_become_artist,
)


# ===========================================================================
# Helpers
# ===========================================================================
def _ip(request) -> str | None:
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def _published_artists():
    return ArtistProfile.objects.filter(is_active=True)


def _published_songs():
    return Song.objects.filter(is_published=True, artist__is_active=True).select_related(
        "artist", "genre"
    )


def _published_events():
    return Event.objects.filter(is_published=True, status=Event.STATUS_PUBLISHED).select_related(
        "headlining_artist"
    )


# ===========================================================================
# Pages publiques — accueil culture, artistes, musique, concerts
# ===========================================================================
def culture_home(request):
    now = timezone.now()
    featured_artists = _published_artists().filter(is_featured=True)[:6]
    if not featured_artists:
        featured_artists = _published_artists()[:6]

    featured_songs = _published_songs().filter(is_featured=True)[:8]
    if not featured_songs:
        featured_songs = _published_songs()[:8]

    upcoming_events = _published_events().filter(starts_at__gte=now).order_by("starts_at")[:6]
    genres = MusicGenre.objects.annotate(songs_total=Count("songs")).filter(songs_total__gt=0)

    context = {
        "featured_artists": featured_artists,
        "featured_songs": featured_songs,
        "upcoming_events": upcoming_events,
        "genres": genres,
        "stats": {
            "artists": _published_artists().count(),
            "songs": _published_songs().count(),
            "events": _published_events().count(),
        },
    }
    return render(request, "culture/home.html", context)


def artist_list(request):
    artists = _published_artists()
    q = (request.GET.get("q") or "").strip()
    genre_slug = request.GET.get("genre", "")
    region = request.GET.get("region", "")

    if q:
        artists = artists.filter(
            Q(stage_name__icontains=q) | Q(city__icontains=q) | Q(region__icontains=q)
        )
    if genre_slug:
        artists = artists.filter(primary_genre__slug=genre_slug)
    if region:
        artists = artists.filter(region__iexact=region)

    artists = artists.annotate(
        songs_total=Count("songs", filter=Q(songs__is_published=True), distinct=True)
    )

    context = {
        "artists": artists,
        "genres": MusicGenre.objects.all(),
        "q": q,
        "genre_slug": genre_slug,
        "region": region,
    }
    return render(request, "culture/artist_list.html", context)


def artist_detail(request, slug):
    artist = get_object_or_404(_published_artists(), slug=slug)
    songs = artist.songs.filter(is_published=True).order_by("-is_featured", "-created_at")
    upcoming = artist.events.filter(
        is_published=True, status=Event.STATUS_PUBLISHED, starts_at__gte=timezone.now()
    ).order_by("starts_at")[:5]
    return render(
        request,
        "culture/artist_detail.html",
        {"artist": artist, "songs": songs, "upcoming_events": upcoming},
    )


def song_list(request):
    songs = _published_songs()
    q = (request.GET.get("q") or "").strip()
    genre_slug = request.GET.get("genre", "")
    pricing = request.GET.get("pricing", "")
    if q:
        songs = songs.filter(
            Q(title__icontains=q) | Q(artist__stage_name__icontains=q)
        )
    if genre_slug:
        songs = songs.filter(genre__slug=genre_slug)
    if pricing in (Song.PRICING_FREE, Song.PRICING_PAID):
        songs = songs.filter(pricing=pricing)

    return render(
        request,
        "culture/song_list.html",
        {
            "songs": songs,
            "genres": MusicGenre.objects.all(),
            "q": q,
            "genre_slug": genre_slug,
            "pricing": pricing,
        },
    )


def song_detail(request, slug):
    song = get_object_or_404(_published_songs(), slug=slug)
    related = (
        _published_songs()
        .filter(artist=song.artist)
        .exclude(pk=song.pk)
        .order_by("-created_at")[:6]
    )
    user_has_access = song.user_has_access(request.user)
    return render(
        request,
        "culture/song_detail.html",
        {"song": song, "related": related, "user_has_access": user_has_access},
    )


def song_play(request, slug):
    """Endpoint d'écoute en streaming. Incrémente le compteur."""
    song = get_object_or_404(_published_songs(), slug=slug)
    if not song.allow_streaming and not song.user_has_access(request.user):
        return HttpResponseBadRequest("Streaming non autorisé pour cette chanson.")

    Song.objects.filter(pk=song.pk).update(play_count=F("play_count") + 1)
    SongPlay.objects.create(
        song=song,
        user=request.user if request.user.is_authenticated else None,
        ip_address=_ip(request),
    )

    response = FileResponse(open(song.audio_file.path, "rb"), content_type="audio/mpeg")
    response["Accept-Ranges"] = "bytes"
    return response


@login_required
def song_buy(request, slug):
    """Crée un achat en attente puis redirige vers GeniusPay ou la page de test (sandbox)."""
    song = get_object_or_404(_published_songs(), slug=slug)
    if song.is_free:
        messages.info(request, "Cette chanson est gratuite, téléchargement immédiat.")
        return redirect("culture:song_detail", slug=song.slug)

    purchase = SongPurchase.objects.create(
        song=song,
        user=request.user,
        amount_fcfa=song.price_fcfa,
    )
    if genius_is_configured():
        success_url = request.build_absolute_uri(
            reverse(
                "culture:song_genius_return",
                kwargs={"slug": song.slug, "reference": purchase.reference},
            )
        )
        error_url = request.build_absolute_uri(
            reverse(
                "culture:song_genius_error",
                kwargs={"slug": song.slug, "reference": purchase.reference},
            )
        )
        try:
            res = create_checkout_payment(
                amount=purchase.amount_fcfa,
                description=f"Achat musique — {song.title}"[:500],
                customer_name=request.user.get_full_name() or request.user.username,
                customer_email=request.user.email or "",
                customer_phone="",
                metadata={
                    "kind": "song_purchase",
                    "song_purchase_ref": str(purchase.reference),
                },
                success_url=success_url,
                error_url=error_url,
            )
        except GeniusPaymentError as exc:
            purchase.delete()
            messages.error(request, str(exc))
            return redirect("culture:song_detail", slug=song.slug)
        gref = (res.get("reference") or "")[:80]
        if gref:
            purchase.genius_reference = gref
            purchase.save(update_fields=["genius_reference"])
        return redirect(res["checkout_url"])

    return redirect("culture:song_payment", slug=song.slug, reference=purchase.reference)


@login_required
def song_payment_sandbox(request, slug, reference):
    """Page de paiement simulé (sandbox)."""
    song = get_object_or_404(_published_songs(), slug=slug)
    purchase = get_object_or_404(SongPurchase, reference=reference, song=song, user=request.user)

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "pay":
            purchase.mark_paid("sandbox")
            messages.success(request, "Paiement validé. Téléchargement disponible !")
            return redirect("culture:song_download", token=purchase.download_token)
        elif action == "cancel":
            purchase.delete()
            messages.info(request, "Achat annulé.")
            return redirect("culture:song_detail", slug=song.slug)

    return render(
        request,
        "culture/song_payment.html",
        {"song": song, "purchase": purchase},
    )


@login_required
def song_genius_return(request, slug, reference):
    song = get_object_or_404(_published_songs(), slug=slug)
    purchase = get_object_or_404(
        SongPurchase, reference=reference, song=song, user=request.user
    )
    if not purchase.genius_reference:
        raise Http404
    if purchase.is_paid:
        messages.success(request, "Achat déjà confirmé.")
        return redirect("culture:song_download", token=purchase.download_token)

    try:
        data = fetch_payment(purchase.genius_reference)
    except GeniusPaymentError as exc:
        return render(
            request,
            "culture/culture_genius_pending.html",
            {
                "headline": "Paiement en cours",
                "subtitle": f"« {song.title} » — {purchase.amount_fcfa} FCFA",
                "message": str(exc),
                "verify_url": request.build_absolute_uri(
                    reverse(
                        "culture:song_genius_return",
                        kwargs={"slug": slug, "reference": reference},
                    )
                ),
                "back_url": reverse("culture:song_detail", kwargs={"slug": slug}),
                "back_label": "Retour à la chanson",
            },
        )

    status = (data.get("status") or "").lower()
    if status == "completed":
        purchase.mark_paid("genius")
        messages.success(request, "Paiement confirmé. Téléchargement disponible !")
        return redirect("culture:song_download", token=purchase.download_token)

    if status == "failed":
        SongPurchase.objects.filter(pk=purchase.pk, is_paid=False).delete()
        messages.error(request, "Le paiement a échoué ou a été annulé.")
        return redirect("culture:song_detail", slug=song.slug)

    return render(
        request,
        "culture/culture_genius_pending.html",
        {
            "headline": "Paiement en cours",
            "subtitle": f"« {song.title} » — {purchase.amount_fcfa} FCFA",
            "message": "Validation en cours chez GeniusPay.",
            "verify_url": request.build_absolute_uri(
                reverse(
                    "culture:song_genius_return",
                    kwargs={"slug": slug, "reference": reference},
                )
            ),
            "back_url": reverse("culture:song_detail", kwargs={"slug": slug}),
            "back_label": "Retour à la chanson",
        },
    )


@login_required
def song_genius_error(request, slug, reference):
    song = get_object_or_404(_published_songs(), slug=slug)
    purchase = get_object_or_404(SongPurchase, reference=reference, song=song, user=request.user)
    if not purchase.is_paid:
        purchase.delete()
    messages.warning(
        request,
        "Le paiement n'a pas abouti. Vous pouvez réessayer l'achat depuis la fiche de la chanson.",
    )
    return redirect("culture:song_detail", slug=song.slug)


def song_download(request, token):
    """Téléchargement protégé. Pour chanson gratuite ou achat payé."""
    purchase = SongPurchase.objects.filter(download_token=token, is_paid=True).first()
    if purchase:
        song = purchase.song
        SongPurchase.objects.filter(pk=purchase.pk).update(
            download_count=F("download_count") + 1
        )
    else:
        song = get_object_or_404(Song, audio_file__isnull=False)
        if not song.is_free:
            raise Http404
    Song.objects.filter(pk=song.pk).update(download_count=F("download_count") + 1)

    response = FileResponse(
        open(song.audio_file.path, "rb"),
        as_attachment=True,
        filename=f"{song.artist.stage_name} - {song.title}.mp3",
    )
    return response


def event_list(request):
    now = timezone.now()
    qs = _published_events()
    when = request.GET.get("when", "upcoming")
    city = (request.GET.get("city") or "").strip()
    q = (request.GET.get("q") or "").strip()

    if when == "past":
        qs = qs.filter(starts_at__lt=now).order_by("-starts_at")
    else:
        qs = qs.filter(starts_at__gte=now).order_by("starts_at")
    if city:
        qs = qs.filter(city__iexact=city)
    if q:
        qs = qs.filter(
            Q(title__icontains=q) | Q(headlining_artist__stage_name__icontains=q) | Q(venue_name__icontains=q)
        )

    return render(
        request,
        "culture/event_list.html",
        {"events": qs, "when": when, "city": city, "q": q},
    )


def event_detail(request, slug):
    event = get_object_or_404(_published_events(), slug=slug)
    categories = event.ticket_categories.filter(is_active=True)
    return render(
        request,
        "culture/event_detail.html",
        {"event": event, "categories": categories},
    )


def ticket_purchase(request, slug):
    event = get_object_or_404(_published_events(), slug=slug)
    if not event.is_open_for_sale:
        messages.error(request, "La billetterie de cet événement n'est plus disponible.")
        return redirect("culture:event_detail", slug=event.slug)

    categories = event.ticket_categories.filter(is_active=True)

    if request.method == "POST":
        category_id = request.POST.get("category_id")
        category = get_object_or_404(categories, pk=category_id)
        form = TicketBuyerForm(request.POST)
        if form.is_valid():
            quantity = form.cleaned_data["quantity"]
            if category.quantity_remaining < quantity:
                messages.error(
                    request,
                    f"Il ne reste que {category.quantity_remaining} billets dans la catégorie {category.name}.",
                )
            else:
                tickets = []
                for _ in range(quantity):
                    t = Ticket.objects.create(
                        event=event,
                        category=category,
                        buyer=request.user if request.user.is_authenticated else None,
                        buyer_name=form.cleaned_data["buyer_name"],
                        buyer_email=form.cleaned_data["buyer_email"],
                        buyer_phone=form.cleaned_data["buyer_phone"],
                        amount_fcfa=category.price_fcfa,
                    )
                    tickets.append(t)
                request.session["pending_tickets"] = [str(t.reference) for t in tickets]
                first_ref = tickets[0].reference
                total = sum(t.amount_fcfa for t in tickets)

                if genius_is_configured():
                    success_url = request.build_absolute_uri(
                        reverse(
                            "culture:ticket_genius_return",
                            kwargs={"slug": event.slug, "reference": first_ref},
                        )
                    )
                    error_url = request.build_absolute_uri(
                        reverse(
                            "culture:ticket_genius_error",
                            kwargs={"slug": event.slug, "reference": first_ref},
                        )
                    )
                    try:
                        res = create_checkout_payment(
                            amount=total,
                            description=f"Billets — {event.title}"[:500],
                            customer_name=form.cleaned_data["buyer_name"],
                            customer_email=form.cleaned_data["buyer_email"],
                            customer_phone=(form.cleaned_data["buyer_phone"] or "")[:30],
                            metadata={
                                "kind": "ticket_batch",
                                "ticket_refs": ",".join(str(t.reference) for t in tickets),
                            },
                            success_url=success_url,
                            error_url=error_url,
                        )
                    except GeniusPaymentError as exc:
                        for t in tickets:
                            t.delete()
                        request.session.pop("pending_tickets", None)
                        messages.error(request, str(exc))
                        return redirect("culture:event_detail", slug=event.slug)
                    gref = (res.get("reference") or "")[:80]
                    if gref:
                        Ticket.objects.filter(pk__in=[t.pk for t in tickets]).update(
                            genius_reference=gref
                        )
                    else:
                        for t in tickets:
                            t.delete()
                        request.session.pop("pending_tickets", None)
                        messages.error(
                            request,
                            "Référence de paiement GeniusPay manquante. Réessayez la billetterie.",
                        )
                        return redirect("culture:event_detail", slug=event.slug)

                return redirect(
                    "culture:ticket_payment", slug=event.slug, reference=first_ref
                )
    else:
        form = TicketBuyerForm(
            initial={
                "buyer_name": request.user.get_full_name() if request.user.is_authenticated else "",
                "buyer_email": request.user.email if request.user.is_authenticated else "",
            }
        )

    return render(
        request,
        "culture/ticket_purchase.html",
        {"event": event, "categories": categories, "form": form},
    )


def ticket_payment_sandbox(request, slug, reference):
    event = get_object_or_404(_published_events(), slug=slug)
    pending_refs = request.session.get("pending_tickets", [str(reference)])
    tickets = Ticket.objects.filter(reference__in=pending_refs, event=event).select_related(
        "category"
    )
    if not tickets:
        raise Http404
    total = sum(t.amount_fcfa for t in tickets)

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "pay":
            for t in tickets:
                t.mark_paid("sandbox")
            request.session.pop("pending_tickets", None)
            messages.success(
                request,
                f"Paiement validé ! Vos {len(tickets)} billet(s) sont disponibles.",
            )
            return redirect("culture:ticket_detail", reference=tickets[0].reference)
        elif action == "cancel":
            for t in tickets:
                t.delete()
            request.session.pop("pending_tickets", None)
            messages.info(request, "Achat annulé.")
            return redirect("culture:event_detail", slug=event.slug)

    return render(
        request,
        "culture/ticket_payment.html",
        {"event": event, "tickets": tickets, "total": total},
    )


def ticket_genius_return(request, slug, reference):
    event = get_object_or_404(_published_events(), slug=slug)
    first = get_object_or_404(Ticket, reference=reference, event=event)
    if not first.genius_reference:
        raise Http404
    tickets = list(
        Ticket.objects.filter(event=event, genius_reference=first.genius_reference).select_related(
            "category"
        )
    )
    if not tickets:
        raise Http404
    if all(t.status == Ticket.STATUS_VALID for t in tickets):
        request.session.pop("pending_tickets", None)
        messages.success(request, "Paiement déjà confirmé.")
        return redirect("culture:ticket_detail", reference=tickets[0].reference)

    try:
        data = fetch_payment(first.genius_reference)
    except GeniusPaymentError as exc:
        return render(
            request,
            "culture/culture_genius_pending.html",
            {
                "headline": "Paiement en cours",
                "subtitle": f"{event.title} — {len(tickets)} billet(s)",
                "message": str(exc),
                "verify_url": request.build_absolute_uri(
                    reverse(
                        "culture:ticket_genius_return",
                        kwargs={"slug": slug, "reference": reference},
                    )
                ),
                "back_url": reverse("culture:event_detail", kwargs={"slug": slug}),
                "back_label": "Retour à l'événement",
            },
        )

    status = (data.get("status") or "").lower()
    if status == "completed":
        for t in tickets:
            t.mark_paid("genius")
        request.session.pop("pending_tickets", None)
        messages.success(
            request,
            f"Paiement confirmé ! Vos {len(tickets)} billet(s) sont disponibles.",
        )
        return redirect("culture:ticket_detail", reference=tickets[0].reference)

    if status == "failed":
        Ticket.objects.filter(
            event=event,
            genius_reference=first.genius_reference,
            status=Ticket.STATUS_PENDING,
        ).delete()
        request.session.pop("pending_tickets", None)
        messages.error(request, "Le paiement a échoué ou a été annulé.")
        return redirect("culture:event_detail", slug=event.slug)

    return render(
        request,
        "culture/culture_genius_pending.html",
        {
            "headline": "Paiement en cours",
            "subtitle": f"{event.title} — {len(tickets)} billet(s)",
            "message": "Validation en cours chez GeniusPay.",
            "verify_url": request.build_absolute_uri(
                reverse(
                    "culture:ticket_genius_return",
                    kwargs={"slug": slug, "reference": reference},
                )
            ),
            "back_url": reverse("culture:event_detail", kwargs={"slug": slug}),
            "back_label": "Retour à l'événement",
        },
    )


def ticket_genius_error(request, slug, reference):
    event = get_object_or_404(_published_events(), slug=slug)
    first = get_object_or_404(Ticket, reference=reference, event=event)
    pending_refs = request.session.get("pending_tickets") or []
    if pending_refs:
        Ticket.objects.filter(
            event=event,
            reference__in=pending_refs,
            status=Ticket.STATUS_PENDING,
        ).delete()
    elif first.genius_reference:
        Ticket.objects.filter(event=event, genius_reference=first.genius_reference).delete()
    elif first.status == Ticket.STATUS_PENDING:
        first.delete()
    request.session.pop("pending_tickets", None)
    messages.warning(
        request,
        "Le paiement n'a pas abouti. Vous pouvez créer une nouvelle commande de billets.",
    )
    return redirect("culture:event_detail", slug=event.slug)


def ticket_detail(request, reference):
    ticket = get_object_or_404(Ticket, reference=reference)
    qr_svg = generate_qr_svg(ticket.qr_payload, size=220)
    return render(
        request,
        "culture/ticket_detail.html",
        {"ticket": ticket, "qr_svg": qr_svg},
    )


def ticket_check(request, reference, secret):
    """Page publique de validation d'un billet (lue par scanner QR)."""
    ticket = get_object_or_404(Ticket, reference=reference, secret_code=secret)
    valid = ticket.status == Ticket.STATUS_VALID
    already_used = ticket.status == Ticket.STATUS_USED

    if request.method == "POST" and valid:
        ticket.status = Ticket.STATUS_USED
        ticket.used_at = timezone.now()
        ticket.used_by = request.POST.get("controller", "")[:120]
        ticket.save(update_fields=["status", "used_at", "used_by"])
        valid = False
        already_used = True

    return render(
        request,
        "culture/ticket_check.html",
        {"ticket": ticket, "valid": valid, "already_used": already_used},
    )


@login_required
def my_tickets(request):
    tickets = Ticket.objects.filter(
        Q(buyer=request.user) | Q(buyer_email=request.user.email)
    ).order_by("-created_at")
    return render(request, "culture/my_tickets.html", {"tickets": tickets})


@login_required
def my_purchases(request):
    purchases = SongPurchase.objects.filter(user=request.user, is_paid=True).select_related(
        "song", "song__artist"
    ).order_by("-paid_at")
    return render(request, "culture/my_purchases.html", {"purchases": purchases})


# ===========================================================================
# Espace artiste (privé)
# ===========================================================================
@login_required
def artist_activate(request):
    """Active un profil artiste pour un vendeur ou prestataire existant."""
    if not user_can_become_artist(request.user):
        messages.error(
            request,
            "Le profil artiste est réservé aux vendeurs et prestataires inscrits sur Kolê.",
        )
        return redirect("culture:home")

    existing = ArtistProfile.objects.filter(user=request.user).first()
    if existing:
        return redirect("culture:artist_dashboard")

    if request.method == "POST":
        form = ArtistProfileForm(request.POST, request.FILES)
        if form.is_valid():
            artist = form.save(commit=False)
            artist.user = request.user
            artist.save()
            messages.success(
                request,
                "Profil artiste activé ! Tu peux maintenant publier ta musique et tes concerts.",
            )
            return redirect("culture:artist_dashboard")
    else:
        form = ArtistProfileForm()

    return render(request, "culture/artist_activate.html", {"form": form})


@login_required
def artist_dashboard(request):
    artist = require_artist(request.user)
    songs = artist.songs.all().order_by("-created_at")[:5]
    events = artist.events.order_by("-starts_at")[:5]
    revenue = (
        SongPurchase.objects.filter(song__artist=artist, is_paid=True).aggregate(
            total=Sum("amount_fcfa")
        )["total"]
        or Decimal("0")
    )
    sold_tickets_count = Ticket.objects.filter(
        event__headlining_artist=artist, status__in=[Ticket.STATUS_VALID, Ticket.STATUS_USED]
    ).count()
    return render(
        request,
        "culture/artist_dashboard.html",
        {
            "artist": artist,
            "songs": songs,
            "events": events,
            "revenue": revenue,
            "sold_tickets_count": sold_tickets_count,
        },
    )


@login_required
def artist_profile_edit(request):
    artist = require_artist(request.user)
    if request.method == "POST":
        form = ArtistProfileForm(request.POST, request.FILES, instance=artist)
        if form.is_valid():
            form.save()
            messages.success(request, "Profil mis à jour.")
            return redirect("culture:artist_dashboard")
    else:
        form = ArtistProfileForm(instance=artist)
    return render(request, "culture/artist_profile_edit.html", {"form": form, "artist": artist})


@login_required
def artist_songs(request):
    artist = require_artist(request.user)
    songs = artist.songs.all().order_by("-created_at")
    return render(request, "culture/artist_songs.html", {"artist": artist, "songs": songs})


@login_required
def artist_song_add(request):
    artist = require_artist(request.user)
    if request.method == "POST":
        form = SongForm(request.POST, request.FILES)
        if form.is_valid():
            song = form.save(commit=False)
            song.artist = artist
            song.save()
            messages.success(request, "Chanson ajoutée !")
            return redirect("culture:artist_songs")
    else:
        form = SongForm()
    return render(
        request,
        "culture/artist_song_form.html",
        {"form": form, "artist": artist, "is_new": True},
    )


@login_required
def artist_song_edit(request, pk):
    artist = require_artist(request.user)
    song = get_object_or_404(Song, pk=pk, artist=artist)
    if request.method == "POST":
        form = SongForm(request.POST, request.FILES, instance=song)
        if form.is_valid():
            form.save()
            messages.success(request, "Chanson mise à jour.")
            return redirect("culture:artist_songs")
    else:
        form = SongForm(instance=song)
    return render(
        request,
        "culture/artist_song_form.html",
        {"form": form, "artist": artist, "is_new": False, "song": song},
    )


@login_required
@require_POST
def artist_song_delete(request, pk):
    artist = require_artist(request.user)
    song = get_object_or_404(Song, pk=pk, artist=artist)
    song.delete()
    messages.success(request, "Chanson supprimée.")
    return redirect("culture:artist_songs")


@login_required
def artist_events(request):
    artist = require_artist(request.user)
    events = artist.events.all().order_by("-starts_at")
    return render(request, "culture/artist_events.html", {"artist": artist, "events": events})


@login_required
def artist_event_add(request):
    artist = require_artist(request.user)
    if request.method == "POST":
        form = EventForm(request.POST, request.FILES, artist=artist)
        if form.is_valid():
            event = form.save(commit=False)
            event.organizer = request.user
            if not event.headlining_artist:
                event.headlining_artist = artist
            event.save()
            form.save_m2m()
            messages.success(
                request,
                "Concert créé. Définis maintenant les catégories de billets.",
            )
            return redirect("culture:artist_event_categories", pk=event.pk)
    else:
        form = EventForm(artist=artist, initial={"headlining_artist": artist})
    return render(
        request,
        "culture/artist_event_form.html",
        {"form": form, "artist": artist, "is_new": True},
    )


@login_required
def artist_event_edit(request, pk):
    artist = require_artist(request.user)
    event = get_object_or_404(Event, pk=pk, headlining_artist=artist)
    if request.method == "POST":
        form = EventForm(request.POST, request.FILES, instance=event, artist=artist)
        if form.is_valid():
            form.save()
            messages.success(request, "Concert mis à jour.")
            return redirect("culture:artist_events")
    else:
        form = EventForm(instance=event, artist=artist)
    return render(
        request,
        "culture/artist_event_form.html",
        {"form": form, "artist": artist, "is_new": False, "event": event},
    )


@login_required
def artist_event_categories(request, pk):
    artist = require_artist(request.user)
    event = get_object_or_404(Event, pk=pk, headlining_artist=artist)

    if request.method == "POST":
        if request.POST.get("action") == "delete":
            cat_id = request.POST.get("category_id")
            TicketCategory.objects.filter(pk=cat_id, event=event).delete()
            messages.success(request, "Catégorie supprimée.")
            return redirect("culture:artist_event_categories", pk=event.pk)

        form = TicketCategoryForm(request.POST)
        if form.is_valid():
            cat = form.save(commit=False)
            cat.event = event
            cat.save()
            messages.success(request, f"Catégorie « {cat.name} » créée.")
            return redirect("culture:artist_event_categories", pk=event.pk)
    else:
        form = TicketCategoryForm()

    categories = event.ticket_categories.all()
    return render(
        request,
        "culture/artist_event_categories.html",
        {"event": event, "categories": categories, "form": form},
    )


@login_required
@require_POST
def artist_event_delete(request, pk):
    artist = require_artist(request.user)
    event = get_object_or_404(Event, pk=pk, headlining_artist=artist)
    event.delete()
    messages.success(request, "Concert supprimé.")
    return redirect("culture:artist_events")


@login_required
def artist_event_tickets(request, pk):
    artist = require_artist(request.user)
    event = get_object_or_404(Event, pk=pk, headlining_artist=artist)
    tickets = event.tickets.exclude(status=Ticket.STATUS_PENDING).order_by("-created_at")
    paid_total = (
        tickets.filter(status__in=[Ticket.STATUS_VALID, Ticket.STATUS_USED]).aggregate(
            total=Sum("amount_fcfa")
        )["total"]
        or Decimal("0")
    )
    return render(
        request,
        "culture/artist_event_tickets.html",
        {
            "event": event,
            "tickets": tickets,
            "paid_total": paid_total,
        },
    )
