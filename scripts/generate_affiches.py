#!/usr/bin/env python
"""Regénère les affiches : restaure l'original puis logo + kolêgroup.com."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    subprocess.run(
        ["git", "checkout", "fb5cfaf", "--", "docs/affiches/", "docs/affiche-pub-kole-group.png"],
        cwd=ROOT,
        check=True,
    )
    subprocess.run([sys.executable, str(ROOT / "scripts" / "patch_affiches.py")], cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
