"""Adding food the USDA catalog has never heard of.

Closes #127. The catalog covers 661 foods; people eat more than that. A
pantry item can now carry its own name instead of a catalog row, which
means every path that assumed catalog_item exists has to cope without it.
"""

from datetime import date

import pytest
from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse

from core.forms import PantryItemForm
from core.models import GlobalCatalogItem, PantryItem


def form_data(food, **overrides):
    data = {
        "catalog_item": food,
        "quantity": 1,
        "date_stored": "2026-11-15",
        "location": "SHELF",
    }
    data.update(overrides)
    return data


@pytest.fixture
def user(db):
    # A post_save receiver gives every new user a pantry.
    return User.objects.create_user(username="cook", password="password")


@pytest.fixture
def client_in(user):
    client = Client()
    client.force_login(user)
    return client


# --- the form ---------------------------------------------------------

@pytest.mark.django_db
def test_an_unknown_name_becomes_a_custom_food(user):
    form = PantryItemForm(data=form_data("Dad's chili"))

    assert form.is_valid(), form.errors
    item = form.save(commit=False)
    item.pantry = user.pantry
    item.save()

    assert item.catalog_item is None
    assert item.custom_name == "Dad's chili"


@pytest.mark.django_db
def test_a_catalog_name_still_resolves_to_its_row(user):
    beef = GlobalCatalogItem.objects.get(name="Beef", name_subtitle="ground")

    form = PantryItemForm(data=form_data(str(beef)))

    assert form.is_valid(), form.errors
    assert form.cleaned_data["catalog_item"] == beef


@pytest.mark.django_db
def test_an_ambiguous_name_is_still_refused(user):
    # Ten catalog foods are called "Beef". Treating that as a custom food
    # would quietly throw away the USDA shelf life they were entitled to.
    form = PantryItemForm(data=form_data("Beef"))

    assert not form.is_valid()
    assert "Pick the specific one" in str(form.errors["catalog_item"])


@pytest.mark.django_db
def test_a_blank_name_is_still_refused(user):
    form = PantryItemForm(data=form_data("   "))

    assert not form.is_valid()


@pytest.mark.django_db
def test_switching_a_custom_item_to_a_catalog_food_clears_the_custom_name(user):
    item = PantryItem.objects.create(
        pantry=user.pantry, custom_name="Dad's chili", location="SHELF")
    beef = GlobalCatalogItem.objects.get(name="Beef", name_subtitle="ground")

    form = PantryItemForm(data=form_data(str(beef)), instance=item)

    assert form.is_valid(), form.errors
    saved = form.save()

    assert saved.catalog_item == beef
    assert saved.custom_name == ""


@pytest.mark.django_db
def test_the_edit_popup_opens_showing_the_custom_name(user):
    item = PantryItem.objects.create(
        pantry=user.pantry, custom_name="Dad's chili", location="SHELF")

    form = PantryItemForm(instance=item)

    assert form.initial["catalog_item"] == "Dad's chili"


# --- the model --------------------------------------------------------

@pytest.mark.django_db
def test_a_custom_item_has_no_expiry_and_reads_as_unknown(user):
    # No catalog row means no USDA shelf life to compute from. Blank is
    # the honest answer, and expiration_status already handles it.
    item = PantryItem.objects.create(
        pantry=user.pantry, custom_name="Dad's chili", location="FRIDGE")

    assert item.date_expired is None
    assert item.expiration_status == "Unknown"


@pytest.mark.django_db
def test_a_custom_item_keeps_a_date_the_user_gave_it(user):
    item = PantryItem.objects.create(
        pantry=user.pantry, custom_name="Dad's chili", location="FRIDGE",
        date_expired=date(2026, 12, 1))

    assert item.date_expired == date(2026, 12, 1)
    assert item.expiration_status != "Unknown"


@pytest.mark.django_db
def test_display_name_and_category_work_without_a_catalog_row(user):
    item = PantryItem.objects.create(
        pantry=user.pantry, custom_name="Dad's chili", location="SHELF")

    assert item.display_name == "Dad's chili"
    assert item.category == ""
    assert "Dad's chili" in str(item)


# --- the page ---------------------------------------------------------

@pytest.mark.django_db
def test_a_custom_item_renders_with_the_question_mark_image(client_in, user):
    # No apostrophe in the name on purpose: Django escapes it to &#x27;
    # in the rendered page, which makes the assertion about escaping
    # rather than about the feature.
    PantryItem.objects.create(
        pantry=user.pantry, custom_name="Grandmas Chili", location="SHELF")

    response = client_in.get(reverse("core:home"))
    content = response.content.decode()

    assert response.status_code == 200
    assert "Grandmas Chili" in content
    assert "unknown-food.png" in content


@pytest.mark.django_db
def test_adding_a_custom_food_through_the_form_lands_in_the_pantry(client_in):
    response = client_in.post(reverse("core:add_pantry_item"),
                              data=form_data("Dad's chili"))

    assert response.status_code == 302
    item = PantryItem.objects.get()
    assert item.catalog_item is None
    assert item.custom_name == "Dad's chili"


@pytest.mark.django_db
def test_a_custom_item_can_be_dragged_between_containers(client_in, user):
    # submit_drag_drop logs the item name, which used to come straight off
    # catalog_item and would raise AttributeError on a custom food.
    item = PantryItem.objects.create(
        pantry=user.pantry, custom_name="Dad's chili", location="SHELF")

    response = client_in.post(
        reverse("core:submit_drag_drop"),
        data='{"raw_id": "%s", "target_zone": "FREEZER", "query_string": ""}'
             % item.id,
        content_type="application/json")

    assert response.status_code == 200
    item.refresh_from_db()
    assert item.location == "FREEZER"


@pytest.mark.django_db
def test_dragging_a_custom_item_keeps_the_date_the_user_gave_it(client_in, user):
    # A move clears date_expired so save() can recompute it from USDA
    # data. There is nothing to recompute for a custom food, so clearing
    # it would silently throw away the only date the item will ever have.
    item = PantryItem.objects.create(
        pantry=user.pantry, custom_name="Dad's chili", location="FRIDGE",
        date_expired=date(2026, 12, 1))

    client_in.post(
        reverse("core:submit_drag_drop"),
        data='{"raw_id": "%s", "target_zone": "FREEZER", "query_string": ""}'
             % item.id,
        content_type="application/json")

    item.refresh_from_db()
    assert item.location == "FREEZER"
    assert item.date_expired == date(2026, 12, 1)