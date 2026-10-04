import logging
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.contrib.auth.models import User
from .models import GlobalCatalogItem, Pantry, PantryItem
from .forms import PantryItemForm

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

    user = User.objects.order_by("id").first()
    if user is None:
        user = User.objects.create_user(username="user1", password="password")

    pantry = Pantry.objects.filter(user=user).first()
    if pantry is None:
        pantry = Pantry.objects.create(user=user, name="Pantry1")

    if not GlobalCatalogItem.objects.exists():
        populateDefaultCatalog()

    if not PantryItem.objects.filter(pantry=pantry).exists():
        for item in GlobalCatalogItem.objects.all():
            PantryItem.objects.get_or_create(
                pantry=pantry,
                catalog_item=item,
                defaults={"quantity": 5},
            )

    return [pantry, user]

def populateDefaultCatalog():
    """
        Handle the basic creation of default catalog .
        TODO: consider making this come from a csv file of:
            name, category, Estimated Expiration ? 
    """
    fruits = [
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

    for fruit in fruits:
        GlobalCatalogItem.objects.get_or_create(
            name = fruit,
            category = "Fruit",
            defaults={"estimated_expiration_days": 7}
        )

# TODO: Add in the createOrAdd logic here...
#       This should be a method to assist the user on a different form. 
# TODO: create addOrRetrieval methods for the various objects. 
# Should handle the scenario where an item is added and moved to the user pantry without existing first   
# TODO: handle the inital splash page as a user login / create request
# TODO: create Mock user for this situation ? 
# TODO Migrate this to a class

def home(request):
    """
        Home request. Handles the cases where we have an inital request for the user 
    """
    # Better implementation of the pantry user defaults
    # if request.method == "GET":
    pantry, user = getOrCreateDefaults()    
    pantryItems = PantryItem.objects.filter(pantry=pantry).order_by("date_expired")
    return render(
        request,
        "core/home.html",
        {
            "user" : user,
            "pantry" : pantry,
            "pantryItems" : pantryItems,
            "catalog" : GlobalCatalogItem.objects.all(),
            "form" : PantryItemForm()
        }
    )
    return redirect("core:home")


def add_pantry_item(request):
    """
    This function will make it possible to add items into the user's storage layout.
    """

    pantry, user = getOrCreateDefaults()

    # first existing pantry for now
    if request.method == "POST":
        form = PantryItemForm(request.POST)

        if form.is_valid():
            item = form.save(commit=False) # Instance variable
            item.pantry = pantry
            item.save()
            return redirect("core:home")

    else:
        form = PantryItemForm()

    # Re-render the layout containing errors in case of failure
    pantryItems = PantryItem.objects.filter(pantry=pantry)
    return render(
        request,
        "core/home.html",
        {
            "user": user,
            "pantry": pantry,
            "pantryItems": pantryItems,
            "catalog": GlobalCatalogItem.objects.all(),
            "form": form
        }
    )


def delete_pantry_item(request, id):
    """
    Delete an active Item using an ID
    """

    item = get_object_or_404(PantryItem, id=id)
    if request.method == "POST":
        item.delete()
    return redirect("core:home")


def pantry_item_detail(request, item_id):
    """
        Retrieve one pantry item by ID and display its details.
    """

    pantry_item = get_object_or_404(PantryItem, id=item_id)

    return render(
        request,
        "core/pantry_item_detail.html",
        {
            "pantry_item": pantry_item
        }
    )