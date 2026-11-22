from django.urls import path

from . import views

app_name = "magazine"

urlpatterns = [
    path("", views.home, name="home"),
    path("equipe/", views.team, name="team"),
    path("charte/", views.charter, name="charter"),
    path("boutique/", views.boutique, name="boutique"),
    path("boutique/abonnement/", views.subscribe, name="subscribe"),
    path("boutique/numero/<int:issue_id>/panier/", views.add_issue_to_cart, name="add_issue_to_cart"),
    path("articles/", views.article_list, name="article_list"),
    path("articles/<slug:slug>/", views.article_detail, name="article_detail"),
    path("videos/", views.video_list, name="video_list"),
    path("videos/<slug:slug>/", views.video_detail, name="video_detail"),
    path("portraits/", views.portrait_list, name="portrait_list"),
    path("portraits/<slug:slug>/", views.portrait_detail, name="portrait_detail"),
    path("repertoire/", views.repertoire, name="repertoire"),
    path("repertoire/<slug:slug>/", views.personality_detail, name="personality_detail"),
    path("partenaires/", views.partners, name="partners"),
]
