import json
import logging

from django.conf import settings
from django.contrib.auth import login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView
from django.db import connection
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone

from marketplace.models import ServiceProvider, ServiceRequest, Vendor
from orders.models import Order
from .email_utils import get_user_from_token, send_verification_email
from django.core.management import call_command

from .admin_helpers import (
    overview_stats,
    pending_count,
    pending_pages,
    ranking_pages,
    require_admin,
    subscription_stats,
    user_has_admin_access,
    users_page as admin_users_page,
)
from .db_overview import (
    database_engine_label,
    database_name,
    pending_migrations_count,
    table_stats,
)
from .forms import AdminLoginForm, AdminUserCreateForm, ProfileForm, SignupForm
from .models import UserProfile
from .shopping_access import user_can_shop_as_customer
from .reservation_utils import can_client_delete_reservation, reservation_delete_deadline

logger = logging.getLogger(__name__)


def signup(request):
    if request.method == "POST":
        form = SignupForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            user.is_active = False
            user.save()
            try:
                send_verification_email(request, user)
            except Exception as e:
                logger.exception("Échec envoi email de vérification pour %s", user.email)
                messages.error(
                    request,
                    "L'email de vérification n'a pas pu être envoyé. Utilisez « Renvoyer l'email » sur la page suivante ou contactez le support.",
                )
                request.session["pending_verification_email"] = user.email
                request.session["verification_email_failed"] = True
                return redirect("accounts:signup_email_sent")
            request.session["pending_verification_email"] = user.email
            request.session.pop("verification_email_failed", None)
            return redirect("accounts:signup_email_sent")
        messages.error(
            request,
            "L'inscription n'a pas abouti. Veuillez corriger les erreurs indiquées ci-dessous.",
        )
    else:
        form = SignupForm()
    return render(request, "accounts/signup.html", {"form": form})


def signup_email_sent(request):
    """Page affichée après inscription : indique de vérifier sa boîte mail."""
    email = request.session.get("pending_verification_email")
    email_failed = request.session.get("verification_email_failed", False)
    return render(
        request,
        "accounts/signup_email_sent.html",
        {"email": email, "email_failed": email_failed},
    )


def resend_verification_email(request):
    """Renvoie l'email de confirmation pour un compte inactif."""
    if request.method != "POST":
        return redirect("accounts:signup_email_sent")

    email = (request.POST.get("email") or "").strip()
    if not email:
        messages.error(request, "Indiquez l'adresse email utilisée lors de l'inscription.")
        return redirect("accounts:signup_email_sent")

    user = User.objects.filter(email__iexact=email).first()
    if not user:
        messages.error(
            request,
            "Aucun compte trouvé avec cette adresse. Vérifiez l'orthographe ou créez un compte.",
        )
        request.session["pending_verification_email"] = email
        return redirect("accounts:signup_email_sent")

    if user.is_active:
        messages.success(
            request,
            f"Le compte {user.email} est déjà activé — aucun email de confirmation n'est nécessaire. "
            "Connectez-vous avec votre identifiant et le mot de passe choisi à l'inscription.",
        )
        request.session.pop("pending_verification_email", None)
        request.session.pop("verification_email_failed", None)
        return redirect("accounts:login")

    try:
        send_verification_email(request, user)
    except Exception:
        logger.exception("Échec renvoi email de vérification pour %s", user.email)
        messages.error(
            request,
            "Impossible d'envoyer l'email pour le moment. Réessayez dans quelques minutes ou écrivez à kwakolegroup@gmail.com.",
        )
        request.session["pending_verification_email"] = user.email
        request.session["verification_email_failed"] = True
        return redirect("accounts:signup_email_sent")

    request.session["pending_verification_email"] = user.email
    request.session.pop("verification_email_failed", None)
    messages.success(
        request,
        f"Un nouvel email de confirmation a été envoyé à {user.email}. Pensez à vérifier vos spams.",
    )
    return redirect("accounts:signup_email_sent")


def verify_email(request):
    """Active le compte après clic sur le lien reçu par email."""
    token = request.GET.get("token")
    if not token:
        messages.error(request, "Lien de vérification invalide.")
        return redirect("accounts:login")
    user, err = get_user_from_token(token)
    if err:
        messages.error(request, err)
        return redirect("accounts:login")
    if user.is_active:
        messages.success(
            request,
            "Ce compte est déjà activé. Vous pouvez vous connecter.",
        )
        return redirect("accounts:login")
    user.is_active = True
    user.save()
    messages.success(
        request,
        "Votre adresse email a été confirmée. Vous pouvez maintenant vous connecter.",
    )
    return redirect("accounts:login")


@login_required
def profile(request):
    profile_obj, _ = UserProfile.objects.get_or_create(user=request.user)
    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=profile_obj)
        if form.is_valid():
            try:
                form.save()
                profile_obj.refresh_from_db()
            except Exception as exc:
                logger.exception("Échec enregistrement photos profil user=%s", request.user.pk)
                messages.error(
                    request,
                    "Impossible d’enregistrer les photos. Vérifiez la configuration R2 sur le serveur "
                    "ou réessayez avec une image plus légère (max. 5 Mo).",
                )
                if settings.DEBUG:
                    messages.error(request, f"Détail technique : {exc}")
            else:
                messages.success(
                    request,
                    "Votre profil a bien été mis à jour.",
                )
                return redirect("accounts:profile")
        else:
            messages.error(
                request,
                "Le formulaire contient des erreurs. Corrigez les champs signalés ci-dessous.",
            )
    else:
        form = ProfileForm(instance=profile_obj)
    return render(
        request,
        "accounts/profile.html",
        {"form": form, "profile_obj": profile_obj},
    )


def _is_client(user):
    """True si l'utilisateur peut consulter commandes et réservations en tant qu'acheteur."""
    return user_can_shop_as_customer(user)


@login_required
def order_history(request):
    if not _is_client(request.user):
        return redirect("accounts:profile")
    orders = (
        Order.objects.filter(user=request.user)
        .filter(
            Q(payment_status=Order.PAYMENT_SUCCESS)
            | Q(payment_method=Order.METHOD_LOCAL)
        )
        .exclude(payment_status=Order.PAYMENT_FAILED)
        .prefetch_related("items__product")
        .order_by("-created_at")
    )
    return render(request, "accounts/orders.html", {"orders": orders})


@login_required
def service_reservations(request):
    """Réservations / demandes de services du client (location, hôtel, prestations)."""
    if not _is_client(request.user):
        return redirect("accounts:profile")
    reservations = (
        ServiceRequest.objects.filter(customer=request.user)
        .select_related(
            "service",
            "service__category",
            "vendor",
            "service_provider",
        )
        .order_by("-created_at")
    )
    reservation_rows = [
        {
            "item": item,
            "can_delete": can_client_delete_reservation(item),
            "delete_deadline": reservation_delete_deadline(item.created_at),
        }
        for item in reservations
    ]
    return render(
        request,
        "accounts/reservations.html",
        {"reservation_rows": reservation_rows},
    )


@login_required
def cancel_service_reservation(request, pk):
    if request.method != "POST":
        return redirect("accounts:service_reservations")
    if not _is_client(request.user):
        return redirect("accounts:profile")
    service_request = get_object_or_404(
        ServiceRequest,
        pk=pk,
        customer=request.user,
    )
    if not can_client_delete_reservation(service_request):
        messages.error(
            request,
            "Cette réservation ne peut plus être annulée (délai dépassé ou statut non modifiable).",
        )
        return redirect("accounts:service_reservations")
    label = service_request.service.name if service_request.service else "Réservation"
    service_request.delete()
    messages.success(request, f"La demande « {label} » a été annulée.")
    return redirect("accounts:service_reservations")


class AdminLoginView(LoginView):
    """Connexion dédiée à l'espace admin avec contrôle du rôle."""

    template_name = "accounts/admin_login.html"
    authentication_form = AdminLoginForm
    # Ne pas renvoyer automatiquement les utilisateurs connectés vers ?next=
    # (sinon boucle : admin-panel → connexion-admin → admin-panel pour un non-admin).
    redirect_authenticated_user = False

    def get_success_url(self):
        return self.get_redirect_url() or reverse_lazy("accounts:admin_dashboard")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and user_has_admin_access(request.user):
            return redirect(self.get_success_url())
        return super().dispatch(request, *args, **kwargs)


def _admin_nav_context(profile) -> dict:
    return {"profile": profile, "pending_count": pending_count()}


def _is_app_super_admin(request, profile) -> bool:
    return request.user.is_superuser or profile.role == UserProfile.ROLE_SUPER_ADMIN


def _assignable_role_choices(request, profile):
    if _is_app_super_admin(request, profile):
        return UserProfile.ROLE_CHOICES
    return [
        choice
        for choice in UserProfile.ROLE_CHOICES
        if choice[0] != UserProfile.ROLE_SUPER_ADMIN
    ]


def _user_is_super_admin(user) -> bool:
    if user.is_superuser:
        return True
    try:
        return user.userprofile.role == UserProfile.ROLE_SUPER_ADMIN
    except UserProfile.DoesNotExist:
        return False


def _user_role(user) -> str:
    if user.is_superuser:
        return UserProfile.ROLE_SUPER_ADMIN
    try:
        return user.userprofile.role
    except UserProfile.DoesNotExist:
        return UserProfile.ROLE_CUSTOMER


def _create_app_user(data, role):
    user = User.objects.create_user(
        username=data["username"],
        email=data["email"],
        password=data["password1"],
        first_name=data.get("first_name", ""),
        last_name=data.get("last_name", ""),
    )
    user.is_active = True
    if role == UserProfile.ROLE_SUPER_ADMIN:
        user.is_staff = True
        user.is_superuser = True
    user.save()
    user_profile, _ = UserProfile.objects.get_or_create(user=user)
    user_profile.role = role
    user_profile.save()
    return user, user_profile


@login_required(login_url=reverse_lazy("accounts:admin_login"))
def admin_dashboard(request):
    access = require_admin(request)
    if access.redirect:
        return access.redirect
    profile = access.profile
    stats = overview_stats()
    return render(
        request,
        "accounts/admin_dashboard.html",
        {
            **_admin_nav_context(profile),
            "total_vendors": stats["total_vendors"],
            "total_providers": stats["total_providers"],
            "total_orders": stats["total_orders"],
            "global_revenue": stats["global_revenue"],
            "sub_stats": subscription_stats(),
        },
    )


@login_required(login_url=reverse_lazy("accounts:admin_login"))
def admin_validations(request):
    access = require_admin(request)
    if access.redirect:
        return access.redirect
    profile = access.profile
    return render(
        request,
        "accounts/admin_validations.html",
        {**_admin_nav_context(profile), **pending_pages(request)},
    )


@login_required(login_url=reverse_lazy("accounts:admin_login"))
def admin_rankings(request):
    access = require_admin(request)
    if access.redirect:
        return access.redirect
    profile = access.profile
    return render(
        request,
        "accounts/admin_rankings.html",
        {**_admin_nav_context(profile), **ranking_pages(request)},
    )


@login_required(login_url=reverse_lazy("accounts:admin_login"))
def admin_users(request):
    access = require_admin(request)
    if access.redirect:
        return access.redirect
    profile = access.profile
    super_admin = _is_app_super_admin(request, profile)
    create_form = AdminUserCreateForm(allow_super_admin=super_admin)

    if request.method == "POST" and request.POST.get("form_type") == "create_user":
        create_form = AdminUserCreateForm(
            request.POST,
            allow_super_admin=super_admin,
        )
        if create_form.is_valid():
            data = create_form.cleaned_data
            user, user_profile = _create_app_user(data, data["role"])
            messages.success(
                request,
                f"Compte « {user.username} » créé avec le rôle "
                f"{user_profile.get_role_display()}.",
            )
            return redirect("accounts:admin_users")

    users_page = admin_users_page(request)
    for user in users_page.object_list:
        user.app_role = _user_role(user)
        user.role_locked = not super_admin and _user_is_super_admin(user)

    return render(
        request,
        "accounts/admin_users.html",
        {
            **_admin_nav_context(profile),
            "users_page": users_page,
            "role_choices": _assignable_role_choices(request, profile),
            "create_form": create_form,
            "is_super_admin": super_admin,
        },
    )


@login_required(login_url=reverse_lazy("accounts:admin_login"))
def set_user_role(request, user_id):
    access = require_admin(request)
    if access.redirect:
        return access.redirect
    profile = access.profile
    super_admin = _is_app_super_admin(request, profile)
    target = get_object_or_404(User.objects.select_related("userprofile"), id=user_id)
    if request.method == "POST":
        role = request.POST.get("role")
        if not super_admin and _user_is_super_admin(target):
            messages.error(
                request,
                "Vous ne pouvez pas modifier le rôle d'un super admin.",
            )
            return redirect("accounts:admin_users")
        valid_roles = {
            choice[0] for choice in _assignable_role_choices(request, profile)
        }
        if role in valid_roles:
            target_profile, _ = UserProfile.objects.get_or_create(user=target)
            target_profile.role = role
            target_profile.save()
            if role == UserProfile.ROLE_SUPER_ADMIN and super_admin:
                target.is_staff = True
                target.is_superuser = True
                target.save(update_fields=["is_staff", "is_superuser"])
            elif _user_is_super_admin(target) and role != UserProfile.ROLE_SUPER_ADMIN:
                target.is_staff = False
                target.is_superuser = False
                target.save(update_fields=["is_staff", "is_superuser"])
            messages.success(request, f"Rôle de « {target.username} » mis à jour.")
        else:
            messages.error(request, "Rôle non autorisé.")
    return redirect("accounts:admin_users")


@login_required(login_url=reverse_lazy("accounts:admin_login"))
def moderate_vendor(request, vendor_id, action):
    access = require_admin(request)
    if access.redirect:
        return access.redirect
    vendor = get_object_or_404(Vendor, id=vendor_id)
    if request.method == "POST":
        if action == "approve":
            vendor.verification_status = Vendor.STATUS_VERIFIED
            vendor.verified_at = timezone.now()
        elif action == "reject":
            vendor.verification_status = Vendor.STATUS_REJECTED
            vendor.verified_at = timezone.now()
        vendor.save()
    return redirect("accounts:admin_validations")


@login_required(login_url=reverse_lazy("accounts:admin_login"))
def moderate_service_provider(request, provider_id, action):
    access = require_admin(request)
    if access.redirect:
        return access.redirect
    provider = get_object_or_404(ServiceProvider, id=provider_id)
    if request.method == "POST":
        if action == "approve":
            provider.verification_status = ServiceProvider.STATUS_VERIFIED
            provider.verified_at = timezone.now()
        elif action == "reject":
            provider.verification_status = ServiceProvider.STATUS_REJECTED
            provider.verified_at = timezone.now()
        provider.save()
    return redirect("accounts:admin_validations")


@login_required(login_url=reverse_lazy("accounts:admin_login"))
def view_vendor_details(request, vendor_id):
    """Vue détaillée d'un vendeur pour validation admin."""
    access = require_admin(request)
    if access.redirect:
        return access.redirect
    vendor = get_object_or_404(Vendor, id=vendor_id)
    return render(
        request,
        "accounts/vendor_details.html",
        {"vendor": vendor},
    )


@login_required(login_url=reverse_lazy("accounts:admin_login"))
def view_service_provider_details(request, provider_id):
    """Vue détaillée d'un prestataire pour validation admin."""
    access = require_admin(request)
    if access.redirect:
        return access.redirect
    provider = get_object_or_404(ServiceProvider, id=provider_id)
    return render(
        request,
        "accounts/service_provider_details.html",
        {"provider": provider},
    )


@login_required(login_url=reverse_lazy("accounts:admin_login"))
def admin_system(request):
    """Super admin uniquement : état et maintenance de la base de données."""
    access = require_admin(request, super_only=True)
    if access.redirect:
        return access.redirect
    profile = access.profile

    if request.method == "POST":
        action = (request.POST.get("db_action") or "").strip()
        if action == "sync_static_pages":
            call_command("sync_static_pages")
            messages.success(request, "Pages statiques synchronisées (FAQ, CGU, contact…).")
        elif action == "sync_contact":
            call_command("sync_contact_info")
            messages.success(request, "Informations de contact synchronisées.")
        else:
            messages.error(request, "Action de base de données non reconnue.")
        return redirect("accounts:admin_system")

    return render(
        request,
        "accounts/admin_system.html",
        {
            **_admin_nav_context(profile),
            "db_engine": database_engine_label(),
            "db_name": database_name(),
            "db_vendor": connection.vendor,
            "pending_migrations": pending_migrations_count(),
            "table_stats": table_stats(),
            "debug_mode": settings.DEBUG,
        },
    )
