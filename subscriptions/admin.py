from django.contrib import admin

from .models import Subscription, SubscriptionPayment, SubscriptionPlan


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ("name", "target", "monthly_amount", "is_active", "is_featured", "display_order")
    list_filter = ("target", "is_active", "is_featured")
    search_fields = ("name", "slug", "tagline")
    prepopulated_fields = {"slug": ("name",)}


class SubscriptionPaymentInline(admin.TabularInline):
    model = SubscriptionPayment
    extra = 0
    readonly_fields = ("amount", "status", "provider", "reference", "period_start", "period_end", "paid_at", "created_at")
    can_delete = False


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "owner_display",
        "owner_kind",
        "plan",
        "monthly_amount",
        "status",
        "current_period_end",
        "updated_at",
    )
    list_filter = ("status", "plan")
    search_fields = (
        "vendor__name",
        "service_provider__name",
        "vendor__owner__username",
        "service_provider__owner__username",
    )
    autocomplete_fields = ("vendor", "service_provider", "plan")
    inlines = [SubscriptionPaymentInline]
    readonly_fields = ("started_at", "created_at", "updated_at")

    def owner_display(self, obj):
        return obj.owner_name
    owner_display.short_description = "Titulaire"

    def owner_kind(self, obj):
        return "Vendeur" if obj.vendor_id else "Prestataire"
    owner_kind.short_description = "Type"


@admin.register(SubscriptionPayment)
class SubscriptionPaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "subscription", "amount", "status", "provider", "paid_at", "created_at")
    list_filter = ("status", "provider")
    search_fields = ("reference", "subscription__vendor__name", "subscription__service_provider__name")
    readonly_fields = ("created_at", "updated_at")
