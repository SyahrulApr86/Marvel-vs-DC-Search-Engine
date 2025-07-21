from django import template

register = template.Library()

@register.filter
def mul(value, arg):
    """Multiply the value by the argument."""
    return value * arg

@register.filter
def div(value, arg):
    """Divide the value by the argument."""
    return value / arg

@register.filter
def add_float(value, arg):
    """Add a float to the value."""
    return value + arg

@register.filter(is_safe=True)
def split(value, delimiter=', '):
    """
    Returns a list of strings after splitting by delimiter.
    Usage: {{ value|split:", " }}
    """
    if value:
        return value.split(delimiter)
    return []

@register.filter
def sub(value, arg):
    """Subtract the argument from the value."""
    return value - arg 