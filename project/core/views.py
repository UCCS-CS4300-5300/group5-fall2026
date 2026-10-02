import logging
from django.shortcuts import render, get_object_or_404
from .models import PantryItem
from django.contrib.auth.models import User
from django.utils import timezone
from .models import GlobalCatalogItem, Pantry, PantryItem

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(module)s (Line %(lineno)d): %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler("app.log", mode='w'),  # overwrites the file
        logging.StreamHandler()                    # Outputs to console
    ]
)

def getOrCreateDefaults():
    """
        Sample method to populate models to template on /home request. 
        Makes inital models to allow user see on basic request.
        TODO: Remove / replace this placeholder with Add / edit logic. 
    """

    pantry_item = {}
    pantry = {}
    user = {}
    catalog_item = {}

    # gate this path so that this clause only runs once. This is to prevent database collisions. 
    if User.objects.count() == 0:
        user = User.objects.create_user(username="user1", password = "password")
        logging.debug("Creating user: " + user.username)

        pantry = Pantry.objects.create(user=user, name = "Pantry1")
        populateDefaultCatalog()
        catalog_item = GlobalCatalogItem.objects.create(
            name = "Apple",
            category = "Fruit",
            estimated_expiration_days = 7
        )
        for item in GlobalCatalogItem.objects.all():
            pantry_item = PantryItem.objects.create(
                pantry = pantry,
                catalog_item = item,
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

    # return Pantry
    return [pantry, user, catalog_item]

def populateDefaultCatalog():
    """
        Handle the basic creation of default catalog .
        TODO: consider making this come from a csv file of:
            name, category, Estimated Expiration ? 
    """
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
        GlobalCatalogItem.objects.create(
            name = fruit,
            category = "Fruit",
            estimated_expiration_days = 7
        )

# TODO: Add in the createOrAdd logic here...
# TODO: create addOrRetrieval methods for the various objects. 
# Should handle the scenario where an item is added and moved to the user pantry without existing first   
# TODO: handle the inital splash page as a user login / create request
# TODO: create Mock user for this situation ? 

def home(request):
    """
        Home request. Handles the cases where we have an inital request for the user 
    """
    [pantry, user, catalogItems] = getOrCreateDefaults()

    # Retrieve only pantry items that are still current.
    pantryItems = PantryItem.objects.filter(
        date_expired__gt=timezone.localdate()
    )
    # TODO: add ability to make this per user in objects query. 
    
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

def pantry_item_detail(request, item_id):
    """
        Retrieve one pantry item and display its details.
    """
    pantry_item = get_object_or_404(PantryItem, id=item_id)

    return render(
        request,
        "core/pantry_item_detail.html",
        {
            "pantry_item" : pantry_item
        }
    )