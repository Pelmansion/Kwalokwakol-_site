from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def required_star(field):
    """Astérisque rouge si le champ Django est obligatoire."""
    if getattr(field, "field", None) and field.field.required:
        return mark_safe('<span class="required" aria-hidden="true">*</span>')
    return ""


@register.filter
def is_required_field(field):
    return bool(getattr(field, "field", None) and field.field.required)
