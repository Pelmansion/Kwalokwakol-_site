"""Utilitaires communs pour les téléversements d'images."""

from __future__ import annotations

import logging

from django import forms

logger = logging.getLogger(__name__)


def uploaded_image_file(files, field_name):
    """Fichier image réellement envoyé (ignore le champ vide du navigateur)."""
    uploaded = files.get(field_name)
    if uploaded and getattr(uploaded, "size", 0) > 0:
        return uploaded
    return None


def validate_profile_image(uploaded, *, label):
    max_bytes = 5 * 1024 * 1024
    if uploaded.size > max_bytes:
        raise forms.ValidationError(
            f"{label} : fichier trop lourd (max. 5 Mo). Compressez l’image ou choisissez un autre fichier."
        )
    content_type = (getattr(uploaded, "content_type", None) or "").lower()
    if content_type and not content_type.startswith("image/"):
        raise forms.ValidationError(f"{label} : format non pris en charge (JPG ou PNG recommandé).")


def delete_stored_file(field_file) -> None:
    """Supprime un fichier déjà enregistré (ignore si absent ou erreur R2)."""
    if not field_file:
        return
    name = getattr(field_file, "name", None) or ""
    if not name:
        return
    try:
        field_file.storage.delete(name)
    except Exception as exc:
        logger.warning("Suppression média ignorée (%s): %s", name, exc)


def clear_old_image_before_upload(instance, field_name: str, *, new_upload) -> None:
    """Efface l’ancien fichier en base avant d’enregistrer le nouveau."""
    if not new_upload:
        return
    current = getattr(instance, field_name, None)
    if current and current.name:
        delete_stored_file(current)
