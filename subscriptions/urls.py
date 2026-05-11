from django.urls import path

from . import views

app_name = "subscriptions"

urlpatterns = [
    # Côté vendeur / prestataire
    path("", views.my_subscription, name="my_subscription"),
    path("formules/", views.choose_plan, name="choose_plan"),
    path("payer/", views.start_payment, name="start_payment"),
    path("sandbox/<int:payment_id>/", views.payment_sandbox, name="payment_sandbox"),
    path("succes/<int:payment_id>/", views.payment_success, name="payment_success"),

    # Administration
    path("admin-panel/", views.admin_list, name="admin_list"),
    path(
        "admin-panel/<str:kind>/<int:target_id>/fixer-montant/",
        views.admin_set_amount,
        name="admin_set_amount",
    ),
    path(
        "admin-panel/abonnement/<int:subscription_id>/marquer-paye/",
        views.admin_mark_paid,
        name="admin_mark_paid",
    ),
    path(
        "admin-panel/abonnement/<int:subscription_id>/annuler/",
        views.admin_cancel,
        name="admin_cancel",
    ),
    path("admin-panel/formules/", views.admin_plans, name="admin_plans"),
    path("admin-panel/formules/ajouter/", views.admin_plan_edit, name="admin_plan_create"),
    path(
        "admin-panel/formules/<int:plan_id>/modifier/",
        views.admin_plan_edit,
        name="admin_plan_edit",
    ),
    path(
        "admin-panel/formules/<int:plan_id>/supprimer/",
        views.admin_plan_delete,
        name="admin_plan_delete",
    ),
]
