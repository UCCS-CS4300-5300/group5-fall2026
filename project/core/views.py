import logging
from django.db.models import Case, IntegerField, Q, When
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.urls import reverse
from urllib.parse import quote
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
        Make sure there is a user and a pantry to work with on a /home request.
        TODO: replace with a real login when the multi-user story lands.

        The pantry starts EMPTY on purpose. It used to be seeded with one
        PantryItem per catalog entry, which was fine for the ten hardcoded
        fruits and is not fine for the 661 USDA foods -- the first page
        request would create 661 pantry items. Users add their own now.
    """

    user = User.objects.order_by("id").first()
    if user is None:
        user = User.objects.create_user(username="user1", password="password")

    pantry = Pantry.objects.filter(user=user).first()
    if pantry is None:
        pantry = Pantry.objects.create(user=user, name="Pantry1")

    return [pantry, user]

# The catalog is loaded by the USDA FoodKeeper data migration, not at
# request time, so populateDefaultCatalog() is gone.

# TODO: handle the inital splash page as a user login / create request
# TODO Migrate this to a class

def search_catalog(query, limit=25):
    """
        Find catalog foods matching every word in `query`, best match first.

        Matched word by word rather than as a substring: FoodKeeper stores
        "Beef, ground", so name__icontains="ground beef" finds nothing.

        Ranking matters as much as matching. "Pasta, dry" and "Canned goods"
        both match "pasta" -- the second only because its hidden keyword
        list happens to contain the word. Name matches rank first so the
        obvious answer is the one at the top.
    """
    if not query or not query.strip():
        return GlobalCatalogItem.objects.none()

    words = query.split()
    results = GlobalCatalogItem.objects.all()
    for word in words:
        results = results.filter(
            Q(name__icontains=word)
            | Q(name_subtitle__icontains=word)
            | Q(keywords__icontains=word)
        )

    results = results.annotate(
        rank=Case(
            When(name__iexact=query, then=0),          # "Honey"
            When(name__istartswith=words[0], then=1),  # "Pasta, dry"
            When(name__icontains=words[0], then=2),    # "Cooked pasta"
            When(name_subtitle__icontains=words[0], then=3),
            default=4,                                 # keyword-only match
            output_field=IntegerField(),
        )
    ).order_by("rank", "name", "name_subtitle")

    return results[:limit]


def home(request):
    """
        Home request. Handles the cases where we have an inital request for the user
    """
    if request.method == "GET":
        return render(request, "core/home.html", build_home_context(request=request))
    return redirect("core:home")


def build_home_context(invalid_form=None, invalid_id=None, add_form=None, request=None):
    """
        Builds the home page data. Each pantry item gets its own edit form
        for its pop-up. If an edit failed, that item gets the form with the
        errors and its pop-up opens again. If an add failed, the add form
        keeps its errors.

        Items are also sorted into their three storage containers here, so
        the template just loops over the list it needs.
    """

    pantry, user = getOrCreateDefaults()

    # select_related avoids one extra query per item for the catalog name,
    # which matters now that a pantry can hold a lot of rows. list() makes
    # it explicit that these are the same objects the loop below attaches
    # an edit_form to, rather than relying on queryset result caching.
    pantryItems = list(
        PantryItem.objects.select_related("catalog_item")
                          .filter(pantry=pantry)
                          .order_by("date_expired")
    )

    shelves_items = []
    fridge_items = []
    freezer_items = []
    bag_items = []

    for item in pantryItems:
        if item.id == invalid_id:
            item.edit_form = invalid_form
        else:
            item.edit_form = PantryItemForm(instance=item, auto_id=f"edit{item.id}_%s")

        # Routing the item into the corresponding container
        if item.location == "SHELF":
            shelves_items.append(item)
        elif item.location == "FRIDGE":
            fridge_items.append(item)
        elif item.location == "FREEZER":
            freezer_items.append(item)
        elif item.location == "BAG":
            bag_items.append(item)


    query = request.GET.get("q", "") if request else ""

    return {
        "user" : user,
        "pantry" : pantry,
        "shelves_items": shelves_items,
        "fridge_items": fridge_items,
        "freezer_items":freezer_items,
        "bag_items": bag_items,
        "pantryItems" : pantryItems,
        "form" : add_form or PantryItemForm(),
        "open_edit_id" : invalid_id,
        "query" : query,
        "searchResults" : search_catalog(query),
        "searched" : bool(query.strip()),
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


@require_POST
def add_from_catalog(request, item_id):
    """
    Add one catalog food to the pantry in a single click.

    No dates are given, so PantryItem.save() fills in the expiration date
    from the USDA shelf life for that food, in whichever location it lands.
    """
    pantry, user = getOrCreateDefaults()
    catalog_item = get_object_or_404(GlobalCatalogItem, id=item_id)

    # Never trust a posted value against a choices field. An unknown
    # location would save happily and then match no shelf-life row, so the
    # item would end up with no expiration date for no visible reason.
    location = request.POST.get("location", "SHELVES")
    if location not in dict(PantryItem.STORAGE_LOCATIONS):
        location = "SHELF"

    PantryItem.objects.create(
        pantry=pantry, catalog_item=catalog_item, location=location)

    # Keep the search on screen so several items can be added in a row
    query = request.POST.get("q", "")
    if query:
        return redirect(f"{reverse('core:home')}?q={quote(query)}")
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
                        
            if target_zone:
                item = PantryItem.objects.get(id=raw_id)
                if item:
                    logging.debug(f"Moving Pantry item {item.catalog_item.name} with ide {raw_id} to {target_zone}")
                    item.location = target_zone;
                    item.save()
                else:
                    raise(KeyError)
            else:
                raise(KeyError)

            return JsonResponse({'status': 'success', 'message': 'Item updated!'})
        
        except (ValueError, KeyError):
            return JsonResponse({'status': 'error', 'message': 'Invalid data'}, status=400)
            
    return JsonResponse({'status': 'error', 'message': 'Only POST allowed'}, status=405)