from django import template

register = template.Library()

@register.inclusion_tag('templates/core/partials/pantryItem.html')
def render_pantry_item(pantryItem):
    # Json payload to pipe in to partial template 
    return {
        'product': pantryItem
    }
