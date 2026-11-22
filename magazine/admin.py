from django.contrib import admin

from .models import (
    Article,
    MagazineIssue,
    MagazineNewsletterSignup,
    MagazineSubscription,
    MagazineSubscriptionPlan,
    Partner,
    PartnershipInquiry,
    Personality,
    PersonalitySubmission,
    Portrait,
    TeamMember,
    Video,
)


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ("name", "role", "display_order", "is_active")
    list_editable = ("display_order", "is_active")
    search_fields = ("name", "role")


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "category",
        "locality",
        "is_sponsored",
        "is_demo",
        "is_published",
        "published_at",
    )
    list_filter = ("category", "is_sponsored", "is_demo", "is_published", "is_featured")
    search_fields = ("title", "excerpt", "locality", "author_name")
    prepopulated_fields = {"slug": ("title",)}
    raw_id_fields = ("sponsor",)


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "kind",
        "locality",
        "duration_seconds",
        "is_sponsored",
        "is_demo",
        "is_published",
        "published_at",
    )
    list_filter = ("kind", "is_sponsored", "is_demo", "is_published")
    search_fields = ("title", "locality")
    prepopulated_fields = {"slug": ("title",)}
    raw_id_fields = ("sponsor",)


@admin.register(Portrait)
class PortraitAdmin(admin.ModelAdmin):
    list_display = ("title", "subject_name", "locality", "is_sponsored", "is_demo", "is_published")
    list_filter = ("is_sponsored", "is_demo", "is_published")
    search_fields = ("title", "subject_name", "locality")
    prepopulated_fields = {"slug": ("title",)}
    raw_id_fields = ("sponsor",)


@admin.register(Personality)
class PersonalityAdmin(admin.ModelAdmin):
    list_display = ("full_name", "profession", "locality", "consent_validated", "is_demo", "is_featured")
    list_filter = ("consent_validated", "is_demo", "is_featured", "region")
    search_fields = ("first_name", "last_name", "profession", "locality")
    prepopulated_fields = {"slug": ("first_name", "last_name")}


@admin.register(PersonalitySubmission)
class PersonalitySubmissionAdmin(admin.ModelAdmin):
    list_display = ("full_name", "profession", "email", "status", "consent", "created_at")
    list_filter = ("status", "consent")
    search_fields = ("first_name", "last_name", "email", "profession")
    readonly_fields = ("created_at", "updated_at")


@admin.register(MagazineIssue)
class MagazineIssueAdmin(admin.ModelAdmin):
    list_display = ("number", "title", "price_fcfa", "is_latest", "is_special", "is_published", "product")
    list_filter = ("is_latest", "is_special", "is_published")
    search_fields = ("title",)
    prepopulated_fields = {"slug": ("title",)}
    raw_id_fields = ("product",)


@admin.register(MagazineSubscriptionPlan)
class MagazineSubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ("name", "period", "price_fcfa", "is_active", "is_featured", "display_order")
    list_editable = ("display_order", "is_active", "is_featured")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(MagazineSubscription)
class MagazineSubscriptionAdmin(admin.ModelAdmin):
    list_display = ("full_name", "plan", "status", "amount_fcfa", "reference", "created_at")
    list_filter = ("status", "plan")
    search_fields = ("full_name", "email", "reference")


@admin.register(MagazineNewsletterSignup)
class MagazineNewsletterSignupAdmin(admin.ModelAdmin):
    list_display = ("email", "full_name", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("email", "full_name")


@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    list_display = ("name", "is_sponsor", "is_demo", "is_active", "display_order")
    list_editable = ("display_order", "is_active")
    list_filter = ("is_sponsor", "is_demo", "is_active")


@admin.register(PartnershipInquiry)
class PartnershipInquiryAdmin(admin.ModelAdmin):
    list_display = ("organization", "name", "offer_type", "is_handled", "created_at")
    list_filter = ("offer_type", "is_handled")
    search_fields = ("organization", "name", "email")
