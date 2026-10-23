import pytest
from django.urls import reverse
from core.models import GlobalCatalogItem, PantryItem
from core.views import search_catalog, getOrCreateDefaults


# --- Searching the catalog ---

@pytest.mark.django_db
def test_search_finds_reordered_words():
    # FoodKeeper stores "Beef, ground"; a user types "ground beef".
    # A plain substring search on the name finds nothing.
    assert search_catalog("ground beef").first().name == "Beef"


@pytest.mark.django_db
def test_search_is_case_insensitive():
    assert search_catalog("CEREAL").exists()


@pytest.mark.django_db
def test_name_matches_rank_above_keyword_matches():
    # "Canned goods" matches "pasta" only through its hidden keyword list.
    # The food actually called Pasta has to come first.
    assert search_catalog("pasta").first().name == "Pasta"


@pytest.mark.django_db
def test_blank_search_returns_nothing():
    assert not search_catalog("   ").exists()


@pytest.mark.django_db
def test_no_match_offers_manual_entry(client):
    response = client.get(reverse("core:home"), {"q": "zzzqqq"})

    assert response.status_code == 200
    assert b"add it yourself" in response.content


@pytest.mark.django_db
def test_results_appear_on_the_page(client):
    response = client.get(reverse("core:home"), {"q": "cereal"})

    assert response.status_code == 200
    assert b"Cereal" in response.content


# --- Adding from a search result ---

@pytest.mark.django_db
def test_adding_from_catalog_sets_a_usda_date(client):
    # The search result carries a location, and the date follows from it.
    # Raw chicken has no pantry figure, so adding it to the shelves would
    # correctly produce no date -- see the test below.
    chicken = GlobalCatalogItem.objects.get(name="Chicken", name_subtitle="whole")

    response = client.post(
        reverse("core:add_from_catalog", args=[chicken.id]),
        {"location": "FRIDGE"},
    )

    assert response.status_code == 302
    item = PantryItem.objects.get()
    assert item.catalog_item == chicken
    assert item.location == "FRIDGE"
    assert (item.date_expired - item.date_stored).days == 2


@pytest.mark.django_db
def test_adding_defaults_to_the_shelves(client):
    # No location posted -- the item still saves rather than erroring.
    cereal = GlobalCatalogItem.objects.filter(name="Cereal").first()

    client.post(reverse("core:add_from_catalog", args=[cereal.id]))

    assert PantryItem.objects.get().location == "SHELF"


@pytest.mark.django_db
def test_a_bogus_location_falls_back_to_the_shelves(client):
    # A posted value is not trusted against the choices field. Saving
    # "KITCHEN" would match no shelf-life row and lose the date silently.
    cereal = GlobalCatalogItem.objects.filter(name="Cereal").first()

    client.post(
        reverse("core:add_from_catalog", args=[cereal.id]),
        {"location": "KITCHEN"},
    )

    assert PantryItem.objects.get().location == "SHELF"


@pytest.mark.django_db
def test_added_item_survives_a_reload(client):
    cereal = GlobalCatalogItem.objects.filter(name="Cereal").first()
    client.post(reverse("core:add_from_catalog", args=[cereal.id]))

    assert b"Cereal" in client.get(reverse("core:home")).content


@pytest.mark.django_db
def test_the_search_stays_on_screen_after_adding(client):
    # So several foods can be added from one search without retyping it
    cereal = GlobalCatalogItem.objects.filter(name="Cereal").first()

    response = client.post(
        reverse("core:add_from_catalog", args=[cereal.id]), {"q": "cereal"}
    )

    assert "q=cereal" in response["Location"]


@pytest.mark.django_db
def test_unknown_food_adds_nothing(client):
    response = client.post(reverse("core:add_from_catalog", args=[999999]))

    assert response.status_code == 404
    assert PantryItem.objects.count() == 0


@pytest.mark.django_db
def test_add_requires_a_post(client):
    cereal = GlobalCatalogItem.objects.filter(name="Cereal").first()

    response = client.get(reverse("core:add_from_catalog", args=[cereal.id]))

    assert response.status_code == 405
    assert PantryItem.objects.count() == 0