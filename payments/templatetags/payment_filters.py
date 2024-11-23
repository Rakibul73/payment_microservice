from django import template
from datetime import datetime

register = template.Library()

@register.filter
def timestamp_to_datetime(timestamp):
    if timestamp:
        return datetime.fromtimestamp(timestamp)
    return None 