"""Utilitaires communs pour les téléversements d'images."""

from __future__ import annotations

from django import forms


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


def replace_image_field(instance, field_name, new_file):
    """Supprime l'ancien fichier puis assigne le nouveau (évite doublons / cache R2)."""
    if not new_file:
        return
    current = getattr(instance, field_name, None)
    if current:
        current.delete(save=False)
    setattr(instance, field_name, new_file)
