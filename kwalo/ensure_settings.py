"""Crée kwalo/settings.py depuis settings.example.py si absent (déploiement Render)."""
from __future__ import annotations

import shutil
from pathlib import Path


def ensure_settings_module() -> None:
    base = Path(__file__).resolve().parent
    target = base / "settings.py"
    source = base / "settings.example.py"
    if target.is_file():
        return
    if not source.is_file():
        raise FileNotFoundError(
            f"Fichier manquant : {source}. "
            "Vérifiez que settings.example.py est bien présent dans le dépôt."
        )
    shutil.copyfile(source, target)
