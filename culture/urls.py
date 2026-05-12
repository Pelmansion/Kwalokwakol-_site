from django.urls import path

from . import views

app_name = "culture"

urlpatterns = [
    # ---------- Pages publiques ----------
    path("", views.culture_home, name="home"),
    path("artistes/", views.artist_list, name="artist_list"),
    path("artistes/<slug:slug>/", views.artist_detail, name="artist_detail"),
    path("musique/", views.song_list, name="song_list"),
    path("musique/<slug:slug>/", views.song_detail, name="song_detail"),
    path("musique/<slug:slug>/ecouter/", views.song_play, name="song_play"),
    path("musique/<slug:slug>/acheter/", views.song_buy, name="song_buy"),
    path(
        "musique/<slug:slug>/paiement/<uuid:reference>/",
        views.song_payment_sandbox,
        name="song_payment",
    ),
    path(
        "musique/<slug:slug>/genius-retour/<uuid:reference>/",
        views.song_genius_return,
        name="song_genius_return",
    ),
    path(
        "musique/<slug:slug>/genius-erreur/<uuid:reference>/",
        views.song_genius_error,
        name="song_genius_error",
    ),
    path(
        "musique/telecharger/<str:token>/",
        views.song_download,
        name="song_download",
    ),
    path("concerts/", views.event_list, name="event_list"),
    path("concerts/<slug:slug>/", views.event_detail, name="event_detail"),
    path("concerts/<slug:slug>/billetterie/", views.ticket_purchase, name="ticket_purchase"),
    path(
        "concerts/<slug:slug>/genius-retour/<uuid:reference>/",
        views.ticket_genius_return,
        name="ticket_genius_return",
    ),
    path(
        "concerts/<slug:slug>/genius-erreur/<uuid:reference>/",
        views.ticket_genius_error,
        name="ticket_genius_error",
    ),
    path(
        "concerts/<slug:slug>/paiement/<uuid:reference>/",
        views.ticket_payment_sandbox,
        name="ticket_payment",
    ),
    path("billets/<uuid:reference>/", views.ticket_detail, name="ticket_detail"),
    path(
        "billets/verifier/<uuid:reference>/<str:secret>/",
        views.ticket_check,
        name="ticket_check",
    ),
    path("mes-billets/", views.my_tickets, name="my_tickets"),
    path("mes-achats/", views.my_purchases, name="my_purchases"),

    # ---------- Espace artiste (privé) ----------
    path("espace-artiste/activer/", views.artist_activate, name="artist_activate"),
    path("espace-artiste/", views.artist_dashboard, name="artist_dashboard"),
    path("espace-artiste/profil/", views.artist_profile_edit, name="artist_profile_edit"),
    path("espace-artiste/musique/", views.artist_songs, name="artist_songs"),
    path("espace-artiste/musique/ajouter/", views.artist_song_add, name="artist_song_add"),
    path(
        "espace-artiste/musique/<int:pk>/modifier/",
        views.artist_song_edit,
        name="artist_song_edit",
    ),
    path(
        "espace-artiste/musique/<int:pk>/supprimer/",
        views.artist_song_delete,
        name="artist_song_delete",
    ),
    path("espace-artiste/concerts/", views.artist_events, name="artist_events"),
    path("espace-artiste/concerts/ajouter/", views.artist_event_add, name="artist_event_add"),
    path(
        "espace-artiste/concerts/<int:pk>/modifier/",
        views.artist_event_edit,
        name="artist_event_edit",
    ),
    path(
        "espace-artiste/concerts/<int:pk>/categories/",
        views.artist_event_categories,
        name="artist_event_categories",
    ),
    path(
        "espace-artiste/concerts/<int:pk>/supprimer/",
        views.artist_event_delete,
        name="artist_event_delete",
    ),
    path(
        "espace-artiste/concerts/<int:pk>/billets/",
        views.artist_event_tickets,
        name="artist_event_tickets",
    ),
]
