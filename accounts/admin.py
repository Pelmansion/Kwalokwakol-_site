from django.contrib import admin

from .models import Address, Favorite, UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "phone", "city")
    search_fields = ("user__username", "phone")


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("user", "address", "city", "phone", "is_default")
    list_filter = ("is_default", "city")
    search_fields = ("user__username", "address", "phone")


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("user", "product", "created_at")
