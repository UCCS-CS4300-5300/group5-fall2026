from django import template

register = template.Library()

FOOD_CATEGORY_IMAGES = {
    "Baby Food": "baby-food.png",
    "Baked Goods: Bakery": "baked-goods-bakery.png",
    "Baked Goods: Baking and Cooking": "baked-goods-baking-cooking.png",
    "Baked Goods: Refrigerated Dough": "baked-goods-refrigerated-dough.png",
    "Beverages": "beverages.png",
    "Condiments, Sauces & Canned Goods": "condiments-sauces-canned-goods.png",
    "Dairy Products & Eggs": "dairy-products-eggs.png",
    "Deli & Prepared Foods": "deli-prepared-foods.png",
    "Food Purchased Frozen": "food-purchased-frozen.png",
    "Grains, Beans & Pasta": "grains-beans-pasta.png",
    "Meat: Fresh": "meat-fresh.png",
    "Meat: Shelf Stable Foods": "meat-shelf-stable-foods.png",
    "Meat: Smoked or Processed": "meat-smoked-processed.png",
    "Meat: Stuffed or Assembled": "meat-stuffed-assembled.png",
    "Poultry: Cooked or Processed": "poultry-cooked-processed.png",
    "Poultry: Fresh": "poultry-fresh.png",
    "Poultry: Shelf Stable Foods": "poultry-shelf-stable-foods.png",
    "Poultry: Stuffed or Assembled": "poultry-stuffed-assembled.png",
    "Produce: Fresh Fruits": "produce-fresh-fruits.png",
    "Produce: Fresh Vegetables": "produce-fresh-vegetables.png",
    "Seafood: Fresh": "seafood-fresh.png",
    "Seafood: Shellfish": "seafood-shellfish.png",
    "Seafood: Smoked": "seafood-smoked.png",
    "Shelf Stable Foods": "shelf-stable-foods.png",
    "Vegetarian Proteins": "vegetarian-proteins.png",
}


@register.filter
def food_category_image(category):
    return FOOD_CATEGORY_IMAGES.get(category, "unknown-food.png")


@register.inclusion_tag('templates/core/partials/pantryItem.html')
def render_pantry_item(pantryItem):
    # Json payload to pipe in to partial template
    return {
        'product': pantryItem
    }
