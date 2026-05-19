from django.contrib import admin

from .models import Category, CategoryShowcaseImage, Product, ProductMedia, ProductVariant


@admin.register(CategoryShowcaseImage)
class CategoryShowcaseImageAdmin(admin.ModelAdmin):
    list_display = ("category", "vendor", "service_provider", "caption", "position", "id")
    list_filter = ("category",)
    search_fields = ("caption", "category__name")
    raw_id_fields = ("category", "vendor", "service_provider")


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
