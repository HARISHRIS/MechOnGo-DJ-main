from django import template

register = template.Library()

@register.filter
def lookup(obj, key):
    if isinstance(key, str) and '.' in key:
        # Handle nested dictionary access (e.g., 'otp_mapping.id.otp')
        keys = key.split('.')
        current = obj
        for k in keys:
            current = current.get(k, '') if isinstance(current, dict) else ''
            if not current:
                break
        return current
    return obj.get(key, '') if isinstance(obj, dict) else ''