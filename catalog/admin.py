from django.contrib import admin

from .models import Category, Product, ProductMedia, ProductVariant


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "vendor", "service_provider", "parent", "is_active")
    list_filter = ("is_active", "vendor", "service_provider")
    search_fields = ("name", "slug")
    raw_id_fields = ("vendor", "service_provider", "parent")


class ProductMediaInline(admin.TabularInline):
    model = ProductMedia
    extra = 0


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 0


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "vendor", "price", "stock", "kind", "is_active")
    list_filter = ("kind", "is_active", "category")
    search_fields = ("name", "description")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ProductMediaInline, ProductVariantInline]
