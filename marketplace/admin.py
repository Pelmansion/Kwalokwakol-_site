from django.contrib import admin

from .models import ServiceProvider, ServiceRequest, Vendor


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "email", "location", "verification_status", "is_active")
    list_filter = ("verification_status", "is_active")
    search_fields = ("name", "phone", "email")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(ServiceProvider)
class ServiceProviderAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "email", "location", "verification_status", "is_active")
    list_filter = ("verification_status", "is_active")
    search_fields = ("name", "phone", "email")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(ServiceRequest)
class ServiceRequestAdmin(admin.ModelAdmin):
    list_display = ("service", "customer", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("service__name", "customer__username", "comment")
