from django.urls import path

from . import views

app_name = "reviews"

urlpatterns = [
    path("ajouter/<int:product_id>/", views.add_review, name="add_review"),
]
