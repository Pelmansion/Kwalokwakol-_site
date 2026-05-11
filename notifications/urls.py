from django.urls import path

from . import views

app_name = "notifications"

urlpatterns = [
    path("", views.notifications_list, name="list"),
    path("lu/<int:notification_id>/", views.mark_read, name="mark_read"),
]
