from django.contrib import admin
from django.utils.html import format_html

from .models import HomepageBackground, StaticPage


@admin.register(StaticPage)
class StaticPageAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "is_active")
    search_fields = ("title", "slug")
    prepopulated_fields = {"slug": ("title",)}


@admin.register(HomepageBackground)
class HomepageBackgroundAdmin(admin.ModelAdmin):
    list_display = ("__str__", "preview", "is_active", "updated_at")
    list_filter = ("is_active",)
    list_editable = ("is_active",)
    readonly_fields = ("preview_large", "created_at", "updated_at")
    fields = ("title", "image", "preview_large", "is_active", "created_at", "updated_at")

    @admin.display(description="Aperçu")
    def preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="height:40px;border-radius:4px;" />', obj.image.url
            )
        return "—"

    @admin.display(description="Aperçu")
    def preview_large(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width:480px;border-radius:8px;" />',
                obj.image.url,
            )
        return "—"
