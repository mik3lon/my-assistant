from django import template

register = template.Library()

@register.filter
def bytes_to_mb(value):
    """Converts bytes to MB."""
    if value is None:
        return "0 MB"
    mb_value = value / (1024 * 1024)  # Convert bytes to MB
    return "{:.2f} MB".format(mb_value)
