from django.contrib import admin
from django.db.models import Q, Sum

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


@admin.register(MusicGenre)
class MusicGenreAdmin(admin.ModelAdmin):
    list_display = ("name", "icon", "display_order")
    list_editable = ("icon", "display_order")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(ArtistProfile)
class ArtistProfileAdmin(admin.ModelAdmin):
    list_display = (
        "stage_name",
        "primary_genre",
        "city",
        "is_verified",
        "is_featured",
        "is_active",
        "created_at",
    )
    list_filter = ("is_verified", "is_featured", "is_active", "primary_genre", "region")
    search_fields = ("stage_name", "city", "region", "user__username", "user__email")
    list_editable = ("is_verified", "is_featured", "is_active")
    autocomplete_fields = ("user", "primary_genre")
    readonly_fields = ("slug", "created_at", "updated_at")
    fieldsets = (
        ("Identité", {
            "fields": ("user", "stage_name", "slug", "bio", "primary_genre"),
        }),
        ("Localisation", {
            "fields": ("region", "city"),
        }),
        ("Médias", {
            "fields": ("portrait", "cover_photo"),
        }),
        ("Contact", {
            "fields": ("phone", "whatsapp", "email", "website"),
        }),
        ("Réseaux sociaux", {
            "fields": ("facebook", "instagram", "youtube", "tiktok", "spotify"),
        }),
        ("État", {
            "fields": ("is_active", "is_verified", "is_featured"),
        }),
        ("Métadonnées", {
            "fields": ("created_at", "updated_at"),
        }),
    )


class SongPurchaseInline(admin.TabularInline):
    model = SongPurchase
    extra = 0
    fields = ("user", "amount_fcfa", "is_paid", "paid_at", "download_count")
    readonly_fields = ("user", "amount_fcfa", "paid_at", "download_count")
    can_delete = False


@admin.register(Song)
class SongAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "artist",
        "genre",
        "pricing",
        "price_fcfa",
        "play_count",
        "download_count",
        "purchase_revenue_fcfa",
        "is_published",
        "is_featured",
    )
    list_filter = ("pricing", "is_published", "is_featured", "genre")
    search_fields = ("title", "artist__stage_name")
    list_editable = ("is_published", "is_featured")
    autocomplete_fields = ("artist", "genre")
    readonly_fields = ("slug", "play_count", "download_count", "created_at", "updated_at")
    inlines = [SongPurchaseInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request).annotate(
            _purchase_revenue=Sum("purchases__amount_fcfa", filter=Q(purchases__is_paid=True)),
        )
        return qs

    @admin.display(description="Revenus téléch. (FCFA)")
    def purchase_revenue_fcfa(self, obj):
        v = getattr(obj, "_purchase_revenue", None)
        if v is None:
            return "0"
        return f"{int(v):,}".replace(",", "\u202f")


@admin.register(SongPurchase)
class SongPurchaseAdmin(admin.ModelAdmin):
    list_display = ("reference", "song", "user", "amount_fcfa", "is_paid", "paid_at")
    list_filter = ("is_paid", "payment_method")
    search_fields = ("reference", "song__title", "user__username", "user__email")
    readonly_fields = ("reference", "download_token", "created_at")


@admin.register(SongPlay)
class SongPlayAdmin(admin.ModelAdmin):
    list_display = ("song", "user", "played_at", "ip_address")
    list_filter = ("played_at",)
    search_fields = ("song__title", "user__username")
    date_hierarchy = "played_at"


class TicketCategoryInline(admin.TabularInline):
    model = TicketCategory
    extra = 1
    fields = ("name", "price_fcfa", "quantity_total", "quantity_sold", "is_active", "color")
    readonly_fields = ("quantity_sold",)


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {"fields": ("organizer", "title", "slug", "description")}),
        ("Artistes", {"fields": ("headlining_artist", "featured_artists")}),
        ("Visuels", {"fields": ("poster", "digital_billboard")}),
        (
            "Lieu & dates",
            {"fields": ("starts_at", "ends_at", "venue_name", "address", "city", "region", "map_url")},
        ),
        ("Publication", {"fields": ("status", "is_published", "is_featured")}),
        ("Métadonnées", {"fields": ("created_at", "updated_at")}),
    )
    list_display = (
        "title",
        "headlining_artist",
        "starts_at",
        "city",
        "status",
        "is_published",
        "is_featured",
    )
    list_filter = ("status", "is_published", "is_featured", "city")
    search_fields = ("title", "venue_name", "city", "headlining_artist__stage_name")
    list_editable = ("is_published", "is_featured")
    autocomplete_fields = ("organizer", "headlining_artist", "featured_artists")
    inlines = [TicketCategoryInline]
    readonly_fields = ("slug", "created_at", "updated_at")


@admin.register(TicketCategory)
class TicketCategoryAdmin(admin.ModelAdmin):
    list_display = ("event", "name", "price_fcfa", "quantity_total", "quantity_sold", "is_active")
    list_filter = ("is_active",)
    search_fields = ("event__title", "name")


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = (
        "reference",
        "event",
        "category",
        "buyer_name",
        "amount_fcfa",
        "status",
        "paid_at",
    )
    list_filter = ("status", "event", "category")
    search_fields = ("reference", "buyer_name", "buyer_email", "buyer_phone")
    readonly_fields = ("reference", "secret_code", "created_at", "updated_at", "paid_at", "used_at")
