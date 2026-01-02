from django import template
from django.conf import settings
from django.utils.translation import get_language

register = template.Library()


@register.inclusion_tag("leases/tags/language_switcher.html", takes_context=True)
def language_switcher(context):
    """Render language switching buttons."""
    request = context.get("request")
    current_language = get_language()

    languages = [{"code": code, "name": name, "active": code == current_language} for code, name in settings.LANGUAGES]

    return {
        "languages": languages,
        "current_language": current_language,
        "request": request,
    }
