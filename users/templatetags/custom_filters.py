from django import template
from django.template.defaultfilters import date as django_date_filter
from django.utils.dateparse import parse_datetime
from django.utils import translation
from django.template.defaultfilters import date as django_date_filter

register = template.Library()

@register.filter
def parse_and_format_date(value, arg="d M Y, H:i"):
    if not value:
        return "-"
    if isinstance(value, str):
        value = parse_datetime(value)
    if value:
        # Paksa Django menggunakan bahasa Indonesia untuk format ini
        with translation.override("id"):
            return django_date_filter(value, arg)
    return "-"