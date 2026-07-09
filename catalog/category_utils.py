"""Regroupement des catégories (orthographes différentes → catégorie plateforme)."""

from __future__ import annotations

import re
import unicodedata

from django.db.models import QuerySet

from catalog.models import Category


def normalize_category_name(name: str) -> str:
    """Clé de comparaison : minuscules, sans accents ni ponctuation superflue."""
    text = (name or "").strip().lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def category_name_keys(name: str) -> set[str]:
    """Variantes comparables (singulier / pluriel simple)."""
    base = normalize_category_name(name)
    if not base:
        return set()
    keys = {base}
    if base.endswith("s") and len(base) > 3:
        keys.add(base[:-1])
    return keys


def category_names_match(left: str, right: str) -> bool:
    return bool(category_name_keys(left) & category_name_keys(right))


def platform_categories_queryset() -> QuerySet[Category]:
    return Category.objects.filter(
        is_active=True,
        parent__isnull=True,
        vendor__isnull=True,
        service_provider__isnull=True,
    )


def find_platform_category_by_name(name: str) -> Category | None:
    """Retourne la catégorie plateforme dont le nom correspond (orthographe proche)."""
    keys = category_name_keys(name)
    if not keys:
        return None
    for category in platform_categories_queryset().order_by("name"):
        if category_name_keys(category.name) & keys:
            return category
    return None


def resolve_product_category(
    name: str,
    *,
    vendor=None,
    service_provider=None,
) -> Category | None:
    """
    Choisit la catégorie à enregistrer sur un produit.
    Priorité : catégorie plateforme équivalente, sinon catégorie perso du pro.
    """
    label = (name or "").strip()[:120]
    if not label:
        return None

    platform = find_platform_category_by_name(label)
    if platform:
        return platform

    owner_filter = {}
    if vendor is not None:
        owner_filter["vendor"] = vendor
    elif service_provider is not None:
        owner_filter["service_provider"] = service_provider
    else:
        return None

    for category in Category.objects.filter(is_active=True, **owner_filter):
        if category_names_match(category.name, label):
            return category

    return Category.objects.create(name=label, is_active=True, **owner_filter)


def _matching_category_ids(platform_category: Category) -> list[int]:
    """IDs de catégories regroupées sous une catégorie plateforme."""
    ids = {platform_category.pk}
    keys = category_name_keys(platform_category.name)
    for category in Category.objects.filter(is_active=True).exclude(pk=platform_category.pk):
        if category.parent_id == platform_category.pk:
            ids.add(category.pk)
        elif keys and category_name_keys(category.name) & keys:
            ids.add(category.pk)
    return list(ids)


def grouped_category_ids(platform_category: Category) -> list[int]:
    """Catégorie plateforme + variantes vendeur + sous-catégories."""
    ids = set(_matching_category_ids(platform_category))

    def add_tree(category: Category) -> None:
        ids.add(category.pk)
        for child in Category.objects.filter(parent=category, is_active=True):
            add_tree(child)

    for child in Category.objects.filter(parent=platform_category, is_active=True):
        add_tree(child)
    return list(ids)


def products_for_platform_category(
    products_qs: QuerySet,
    platform_category: Category,
) -> QuerySet:
    """Produits rattachés à une catégorie plateforme (y compris variantes vendeur)."""
    category_ids = _matching_category_ids(platform_category)
    return products_qs.filter(category_id__in=category_ids)


def count_products_for_platform_category(
    products_qs: QuerySet,
    platform_category: Category,
) -> int:
    return products_for_platform_category(products_qs, platform_category).count()
