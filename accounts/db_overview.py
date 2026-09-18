"""Statistiques et état de la base de données pour l'espace admin."""

from __future__ import annotations

from django.apps import apps
from django.conf import settings
from django.db import connection
from django.db.migrations.executor import MigrationExecutor


# Modèles principaux affichés dans le tableau de bord système.
MONITORED_MODELS = (
    "auth.User",
    "accounts.UserProfile",
    "catalog.Category",
    "catalog.Product",
    "marketplace.Vendor",
    "marketplace.ServiceProvider",
    "orders.Order",
    "payments.Payment",
    "subscriptions.Subscription",
    "content.StaticPage",
    "culture.ArtistProfile",
    "culture.Song",
    "culture.Event",
)


def database_engine_label() -> str:
    engine = settings.DATABASES["default"]["ENGINE"]
    if "postgresql" in engine:
        return "PostgreSQL"
    if "sqlite" in engine:
        return "SQLite"
    return engine.rsplit(".", 1)[-1]


def database_name() -> str:
    return str(settings.DATABASES["default"].get("NAME", ""))


def pending_migrations_count() -> int:
    executor = MigrationExecutor(connection)
    targets = executor.loader.graph.leaf_nodes()
    return len(executor.migration_plan(targets))


def table_stats() -> list[dict]:
    rows: list[dict] = []
    for label in MONITORED_MODELS:
        try:
            model = apps.get_model(label)
            rows.append(
                {
                    "label": label,
                    "verbose": str(model._meta.verbose_name_plural).capitalize(),
                    "count": model.objects.count(),
                }
            )
        except LookupError:
            continue
    return rows
