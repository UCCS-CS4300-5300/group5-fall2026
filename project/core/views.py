import logging
from django.shortcuts import get_object_or_404, redirect, render
from .models import PantryItem
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
    if request.method == "GET":
        return render(request, "core/home.html", build_home_context())
    return redirect("core:home")

def build_home_context(invalid_form=None, invalid_id=None):
    """
        Builds the home page data. Each pantry item gets its own edit form
        for its pop-up. If an edit failed, that item gets the form with the
        errors and its pop-up opens again.
    """
    [pantry, user, catalogItems] = getOrCreateDefaults()

    # TODO: add ability to make this per user in objects query. 
    pantryItems = list(PantryItem.objects.all())
    for item in pantryItems:
        if item.id == invalid_id:
            item.edit_form = invalid_form
        else:
            item.edit_form = PantryItemForm(instance=item, auto_id=f"edit{item.id}_%s")

    return {
        "user" : user,
        "pantry" : pantry,
        "pantryItems" : pantryItems,
        "catalog" : GlobalCatalogItem.objects.all(),
        "form" : PantryItemForm(),
        "open_edit_id" : invalid_id,
    }
    return redirect("core:home")

def add_pantry_item(request):
    # first existing pantry for now
    # TODO pass Id for pantry back in post URL ? 
    if request.method == "POST":
        form = PantryItemForm(request.POST)
        if form.is_valid():

            # pantry isn't set yet
            item = form.save(commit=False)
            pantry = Pantry.objects.get(name=item.pantry)

            # attach item to pantry
            item.pantry = pantry
            item.save()
        return redirect("core:home")            
    else:
        #empty form for GET request
        form = PantryItemForm()
        return redirect("core:home")

def delete_pantry_item(request, id):
    #any item can be deleted by id
    logging.debug(id)
    logging.debug(id)
    logging.debug(id)
    logging.debug(id)
    item = get_object_or_404(PantryItem, id=id)

    if request.method == "POST":
        item.delete()
    return redirect("core:home")

def edit_pantry_item(request, id):
    # Saves changes from an item's edit pop-up
    item = get_object_or_404(PantryItem, id=id)

    if request.method == "POST":
        form = PantryItemForm(request.POST, instance=item, auto_id=f"edit{id}_%s")
        if form.is_valid():
            form.save()
            return redirect("core:home")

        # Invalid input: nothing is saved, the page reloads with the pop-up open and errors shown
        return render(request, "core/home.html", build_home_context(form, id))

    return redirect("core:home")