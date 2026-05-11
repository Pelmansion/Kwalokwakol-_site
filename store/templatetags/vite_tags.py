import json
from pathlib import Path

from django import template
from django.templatetags.static import static
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def vite_asset(entrypoint):
    base_dir = Path(__file__).resolve().parent.parent.parent
    manifest_path = base_dir / "static" / "react" / ".vite" / "manifest.json"
    if not manifest_path.exists():
        manifest_path = base_dir / "static" / "react" / "manifest.json"
    if not manifest_path.exists():
        return ""
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if entrypoint not in manifest:
        return ""

    chunk = manifest[entrypoint]
    tags = []
    css_files = chunk.get("css", [])
    for css in css_files:
        tags.append(f'<link rel="stylesheet" href="{static("react/" + css)}">')
    tags.append(f'<script type="module" src="{static("react/" + chunk["file"])}"></script>')
    return mark_safe("\n".join(tags))
