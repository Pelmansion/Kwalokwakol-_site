from django.contrib import admin

from .models import Address, Favorite, UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "phone", "city", "has_avatar", "has_cover")
    search_fields = ("user__username", "user__email", "phone")
    raw_id_fields = ("user",)

    @admin.display(description="Photo profil", boolean=True)
    def has_avatar(self, obj):
        return bool(obj.avatar)

    @admin.display(description="Couverture", boolean=True)
    def has_cover(self, obj):
        return bool(obj.cover_photo)


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("user", "address", "city", "phone", "is_default")
    list_filter = ("is_default", "city")
    search_fields = ("user__username", "address", "phone")


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("user", "product", "created_at")
