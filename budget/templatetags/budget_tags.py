from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from django import template
register = template.Library()

@register.filter
def euros(value):
    try:
        amount = Decimal(str(value)).quantize(Decimal('.01'), rounding=ROUND_HALF_UP)
        return f'{amount:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.') + ' €'
    except (InvalidOperation, ValueError, TypeError):
        return '0,00 €'
