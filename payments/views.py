import json
import logging
import time

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseNotAllowed, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from orders.models import Order

from .genius import (
    GeniusPaymentError,
    fetch_payment,
    is_configured,
    verify_webhook_signature,
)
from .models import Payment

logger = logging.getLogger(__name__)


def _finalize_genius_payment(payment: Payment) -> None:
    """Marque le paiement et la commande comme réussis (idempotent)."""
    order = payment.order
    if payment.status == Payment.STATUS_SUCCESS:
        return
    payment.status = Payment.STATUS_SUCCESS
    payment.save(update_fields=["status"])
    order.payment_status = Order.PAYMENT_SUCCESS
    order.status = Order.STATUS_PAID
    order.save(update_fields=["payment_status", "status"])


def payment_sandbox(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    if payment.provider == Payment.PROVIDER_GENIUS:
        return redirect("payments:genius_return", payment_id=payment.id)
    order = payment.order
    if request.method == "POST":
        payment.status = Payment.STATUS_SUCCESS
        payment.reference = f"PAY-{payment.id}"
        payment.save()
        order.payment_status = Order.PAYMENT_SUCCESS
        order.status = Order.STATUS_PAID
        order.save()
        return redirect("store:order_success", order_id=order.id)
    return render(request, "payments/payment_sandbox.html", {"payment": payment, "order": order})


@login_required
def genius_return(request, payment_id):
    """Retour utilisateur après checkout Genius (success_url) — vérifie le statut via l'API."""
    payment = get_object_or_404(
        Payment,
        id=payment_id,
        provider=Payment.PROVIDER_GENIUS,
    )
    order = payment.order
    if order.user_id and order.user_id != request.user.pk:
        messages.warning(request, "Cette commande n'est pas associée à votre compte.")
        return redirect("store:home")

    if payment.status == Payment.STATUS_SUCCESS:
        return redirect("store:order_success", order_id=order.id)

    if not payment.reference:
        return render(
            request,
            "payments/genius_pending.html",
            {
                "payment": payment,
                "order": order,
                "message": "Référence de transaction manquante. Contactez le support avec le numéro de commande.",
            },
        )

    try:
        data = fetch_payment(payment.reference)
    except GeniusPaymentError as e:
        return render(
            request,
            "payments/genius_pending.html",
            {"payment": payment, "order": order, "message": str(e)},
        )

    status = (data.get("status") or "").lower()
    if status == "completed":
        _finalize_genius_payment(payment)
        messages.success(request, "Paiement confirmé. Merci !")
        return redirect("store:order_success", order_id=order.id)

    if status == "failed":
        payment.status = Payment.STATUS_FAILED
        payment.save(update_fields=["status"])
        order.payment_status = Order.PAYMENT_FAILED
        order.save(update_fields=["payment_status"])
        messages.error(request, "Le paiement a échoué ou a été annulé.")
        return redirect("store:cart_detail")

    return render(
        request,
        "payments/genius_pending.html",
        {
            "payment": payment,
            "order": order,
            "message": "Paiement en cours de traitement. Vous recevrez une confirmation dès validation.",
        },
    )


@login_required
def genius_error(request, payment_id):
    """Redirection après échec (error_url)."""
    payment = get_object_or_404(Payment, id=payment_id, provider=Payment.PROVIDER_GENIUS)
    order = payment.order
    if order.user_id and order.user_id != request.user.pk:
        return redirect("store:home")
    messages.warning(
        request,
        "Le paiement n'a pas abouti. Vous pouvez réessayer depuis votre panier ou choisir le paiement à la livraison.",
    )
    return render(
        request,
        "payments/genius_error.html",
        {"payment": payment, "order": order},
    )


@csrf_exempt
@require_POST
def genius_webhook(request):
    """
    Webhook GeniusPay (événement payment.success, etc.).
    Configurez l'URL dans le tableau Genius : https://votre-domaine/paiement/genius/webhook/
    et définissez GENIUS_WEBHOOK_SECRET (whsec_...) dans l'environnement.
    """
    body = request.body
    secret = (getattr(settings, "GENIUS_WEBHOOK_SECRET", None) or "").strip()

    if secret:
        sig = request.headers.get("X-Webhook-Signature", "")
        ts = request.headers.get("X-Webhook-Timestamp", "")
        if not verify_webhook_signature(body, ts, sig, secret):
            logger.warning("Genius webhook signature invalide")
            return JsonResponse({"detail": "Invalid signature"}, status=401)
        try:
            if abs(int(time.time()) - int(ts)) > 300:
                return JsonResponse({"detail": "Timestamp too old"}, status=400)
        except (TypeError, ValueError):
            return JsonResponse({"detail": "Bad timestamp"}, status=400)
    elif not settings.DEBUG:
        logger.error("GENIUS_WEBHOOK_SECRET non défini — webhook refusé")
        return JsonResponse({"detail": "Webhook not configured"}, status=503)
    else:
        logger.warning("Genius webhook sans GENIUS_WEBHOOK_SECRET (DEBUG uniquement)")

    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return JsonResponse({"detail": "Invalid JSON"}, status=400)

    event = request.headers.get("X-Webhook-Event") or payload.get("event") or ""

    if event == "payment.success":
        data = payload.get("data") or {}
        meta = data.get("metadata") or {}
        pid = meta.get("payment_id")
        if not pid:
            logger.warning("Genius webhook payment.success sans payment_id: %s", payload)
            return JsonResponse({"received": True}, status=200)
        try:
            payment = Payment.objects.select_related("order").get(
                id=int(pid),
                provider=Payment.PROVIDER_GENIUS,
            )
        except (Payment.DoesNotExist, ValueError):
            logger.warning("Genius webhook payment introuvable: %s", pid)
            return JsonResponse({"received": True}, status=200)

        ref = data.get("reference") or ""
        if ref and payment.reference and payment.reference != ref:
            logger.warning(
                "Genius webhook référence discordante payment=%s ref=%s webhook=%s",
                payment.id,
                payment.reference,
                ref,
            )

        amt = data.get("amount")
        if amt is not None:
            try:
                if abs(float(amt) - float(payment.amount)) > 1:
                    logger.error(
                        "Genius webhook montant discordant payment=%s attendu=%s reçu=%s",
                        payment.id,
                        payment.amount,
                        amt,
                    )
                    return JsonResponse({"detail": "Amount mismatch"}, status=400)
            except (TypeError, ValueError):
                pass

        _finalize_genius_payment(payment)
        return JsonResponse({"received": True}, status=200)

    if event == "payment.failed":
        data = payload.get("data") or {}
        meta = data.get("metadata") or {}
        pid = meta.get("payment_id")
        if pid:
            try:
                payment = Payment.objects.get(id=int(pid), provider=Payment.PROVIDER_GENIUS)
                if payment.status == Payment.STATUS_PENDING:
                    payment.status = Payment.STATUS_FAILED
                    payment.save(update_fields=["status"])
                    order = payment.order
                    order.payment_status = Order.PAYMENT_FAILED
                    order.save(update_fields=["payment_status"])
            except (Payment.DoesNotExist, ValueError):
                pass
        return JsonResponse({"received": True}, status=200)

    return HttpResponse(status=204)
