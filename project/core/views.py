from django.shortcuts import render
from .models import PantryItem

from django.contrib.auth.models import User
from .models import GlobalCatalogItem, Pantry, PantryItem

def getOrCreateDefaults():
    pantry_item = {}
    pantry = {}
    user = {}
    catalog_item = {}

    if User.objects.count() == 0:
        user = User.objects.create_user(username="user1", password = "password")
        pantry = Pantry.objects.create(user=user, name = "Pantry1")
        # populateDefaultCatalog()
        catalog_item = GlobalCatalogItem.objects.create(
            name = "Apple",
            category = "Fruit",
            estimated_expiration_days = 7
        )
        for i in range(0, 20):
            pantry_item = PantryItem.objects.create(
                pantry = pantry,
                catalog_item = catalog_item,
                quantity = 5
            )
        
        user.save()
        pantry.save()
        pantry_item.save()
        catalog_item.save()

    else:
        user = User.objects.get(id=1)
        pantry = Pantry.objects.get(id=1)
        pantry_item = PantryItem.objects.get(id=1)
        catalog_item = GlobalCatalogItem.objects.get(id=1)
        
    return [pantry, user, catalog_item]
    
def populateDefaultCatalog():
    fruit = [
        "Apples",
        "Bananas",
        "Oranges",
        "Grapes",
        "Strawberries",
        "Watermelons",
        "Mangoes",
        "Pineapples",
        "Pears",
        "Cherries",
    ]

    for fruit in fruit:
        catalog_item = GlobalCatalogItem.objects.create(
            name = fruit,
            category = "Fruit",
            estimated_expiration_days = 7
        )
        catalog_item.save()


def home(request):

    [pantry, user, catalogItems] = getOrCreateDefaults()

    pantryItems = PantryItem.objects.all()
    #PantryItem.objects.create(name="cream puff")

    return render(
        request,
        "core/home.html",
        {
            "user" : user,
            "pantry" : pantry,
            "pantryItems" : pantryItems,
            "catalog" : GlobalCatalogItem.objects.all()
        }
    )
    # return render(
    #     request,
    #     "core/home.html",
    #     {
    #         "food": items,
    #         "name": items.name,
    #         "created_at": items.created_at(),
    #     },
    # )


# Original starter item
"""from .models import StarterItem
def home(request): return render(request,"core/home.html",{"items":StarterItem.objects.filter(is_active=True).order_by("title")})"""