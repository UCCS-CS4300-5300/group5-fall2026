import logging
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.contrib.auth.models import User
from .models import GlobalCatalogItem, Pantry, PantryItem
from .forms import PantryItemForm
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect

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
    if request.method == "GET":
        return render(request, "core/home.html", build_home_context())
    return redirect("core:home")


def build_home_context(invalid_form=None, invalid_id=None, add_form=None):
    """
        Builds the home page data. Each pantry item gets its own edit form
        for its pop-up. If an edit failed, that item gets the form with the
        errors and its pop-up opens again. If an add failed, the add form
        keeps its errors.
    """

    pantry, user = getOrCreateDefaults()

    pantryItems = PantryItem.objects.filter(pantry=pantry).order_by("date_expired")

    shelves_items = []
    fridge_items = []
    freezer_items = []

    for item in pantryItems:
        if item.id == invalid_id:
            item.edit_form = invalid_form
        else:
            item.edit_form = PantryItemForm(instance=item, auto_id=f"edit{item.id}_%s")

        # Routing the item into the corresponding container
        if item.location == "SHELVES":
            shelves_items.append(item)
        elif item.location == "FRIDGE":
            fridge_items.append(item)
        elif item.location == "FREEZER":
            freezer_items.append(item)

    return {
        "user" : user,
        "pantry" : pantry,
        "shelves_items": shelves_items,
        "fridge_items": fridge_items,
        "freezer_items":freezer_items,
        "pantryItems" : pantryItems,
        "catalog" : GlobalCatalogItem.objects.all(),
        "form" : add_form or PantryItemForm(),
        "open_edit_id" : invalid_id,
    }


def add_pantry_item(request):
    """
    This function will make it possible to add items into the user's storage layout.
    """

    pantry, user = getOrCreateDefaults()

    if request.method == "POST":
        form = PantryItemForm(request.POST)

        if form.is_valid():
            item = form.save(commit=False) # Instance variable
            item.pantry = pantry
            item.save()
            return redirect("core:home")

        # Re-render the layout containing errors in case of failure
        return render(request, "core/home.html", build_home_context(add_form=form))

    return redirect("core:home")


def delete_pantry_item(request, id):
    """
    Delete an active Item using an ID
    """

    item = get_object_or_404(PantryItem, id=id)
    if request.method == "POST":
        item.delete()
    return redirect("core:home")


def edit_pantry_item(request, id):
    """
    Saves changes from an item's edit pop-up
    """
    item = get_object_or_404(PantryItem, id=id)

    if request.method == "POST":
        form = PantryItemForm(request.POST, instance=item, auto_id=f"edit{id}_%s")
        if form.is_valid():
            form.save()
            return redirect("core:home")

        # Invalid input: nothing is saved, the page reloads with the pop-up open and errors shown
        return render(request, "core/home.html", build_home_context(form, id))

    return redirect("core:home")

def test_pantry_view(request):
    """
    Use this to test the pantry items while the main template is being worked
    on by another person
    """

    return render(request, "core/test_pantry.html",build_home_context())


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

@csrf_protect
def submit_drag_drop(request):
    if request.method == 'POST':
        try:
            # Parse the JSON payload sent by Fetch API
            data = json.loads(request.body)
            raw_id = data.get('raw_id')
            target_zone = data.get('target_zone')
                        
            logging.debug(target_zone)
            if target_zone:
                item = PantryItem.objects.get(id=raw_id)
                if item:
                    logging.debug(f"Moving Pantry item {item.catalog_item.name} with ide {raw_id} to {target_zone}")
                    item.location = target_zone;
                    item.save()

            return JsonResponse({'status': 'success', 'message': 'Item updated!'})
        
        except (ValueError, KeyError):
            return JsonResponse({'status': 'error', 'message': 'Invalid data'}, status=400)
            
    return JsonResponse({'status': 'error', 'message': 'Only POST allowed'}, status=405)