"""Crée ou met à jour kwalo/settings.py depuis settings.example.py (déploiement Render)."""
from __future__ import annotations

import os
import shutil
from pathlib import Path


def _on_render() -> bool:
    return bool((os.environ.get("RENDER") or os.environ.get("RENDER_EXTERNAL_HOSTNAME") or "").strip())


def ensure_settings_module() -> None:
    base = Path(__file__).resolve().parent
    target = base / "settings.py"
    source = base / "settings.example.py"
    if not source.is_file():
        raise FileNotFoundError(
            f"Fichier manquant : {source}. "
            "Vérifiez que settings.example.py est bien présent dans le dépôt."
        )
    # Sur Render, recopier à chaque démarrage : évite un settings.py obsolète en cache de build.
    if target.is_file() and not _on_render():
        return
    shutil.copyfile(source, target)
