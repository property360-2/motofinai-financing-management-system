"""
Custom template filters for dashboard calculations
"""
from django import template

register = template.Library()


@register.filter
def mul(value, arg):
    """Multiply the arg with the value"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def div(value, arg):
    """Divide the value by arg"""
    try:
        return float(value) / float(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0
