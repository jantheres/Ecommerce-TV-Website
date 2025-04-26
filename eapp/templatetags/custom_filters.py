from django import template

register = template.Library()

@register.filter
def multiply(value, arg):
    """Multiply the value by the argument"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def sub(value, arg):
    """Subtract the argument from the value"""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0

@register.simple_tag
def product_image(product, image_number):
    """Get the specified product image URL"""
    try:
        image_field = getattr(product, f'image_{str(image_number)}')
        return image_field.url if image_field else ''
    except (AttributeError, ValueError):
        return ''

@register.filter
def product_image_filter(product, image_number):
    """Get the specified product image URL as a filter"""
    try:
        image_field = getattr(product, f'image_{str(image_number)}')
        return image_field.url if image_field else ''
    except (AttributeError, ValueError):
        return ''
    
@register.filter
def split(value, arg):
    return value.split(arg)
