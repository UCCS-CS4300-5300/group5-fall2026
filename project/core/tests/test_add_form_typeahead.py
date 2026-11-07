"""The add/edit form takes a typed food name rather than a 661-row <select>.

The browser filters a <datalist> as the user types, so the form receives a
string and has to turn it back into a catalog row. These cover that
round trip, including the two ways it can legitimately refuse.
"""

import pytest
from django.urls import reverse

from core.forms import PantryItemForm
from core.models import GlobalCatalogItem, PantryItem
from core import views


def form_data(catalog_item, **overrides):
    data = {
        "catalog_item": catalog_item,
        "quantity": 1,
        "date_stored": "2026-11-06",
        "location": "SHELF",
    }
    data.update(overrides)
    return data


@pytest.fixture
def ground_beef(db):
    """One of ten rows named "Beef" -- the subtitle is the only difference."""
    return GlobalCatalogItem.objects.get(name="Beef", name_subtitle="ground")


@pytest.mark.django_db
def test_the_displayed_name_resolves_to_its_row(ground_beef):
    # "Beef (ground)" is exactly what the datalist offers
    form = PantryItemForm(data=form_data(str(ground_beef)))

    assert form.is_valid(), form.errors
    assert form.cleaned_data["catalog_item"] == ground_beef


@pytest.mark.django_db
def test_matching_ignores_case(ground_beef):
    form = PantryItemForm(data=form_data("beef (GROUND)"))

    assert form.is_valid(), form.errors
    assert form.cleaned_data["catalog_item"] == ground_beef


@pytest.mark.django_db
def test_a_bare_name_works_when_only_one_food_has_it():

    from django.db.models import Count

    unique = (GlobalCatalogItem.objects
              .order_by()
              .values("name")
              .annotate(rows=Count("id"))
              .filter(rows=1)
              .order_by("name")
              .first())
    item = GlobalCatalogItem.objects.get(name=unique["name"])

    form = PantryItemForm(data=form_data(item.name))

    assert form.is_valid(), form.errors
    assert form.cleaned_data["catalog_item"] == item

@pytest.mark.django_db
def test_an_ambiguous_bare_name_is_refused(ground_beef):
    # Ten foods are called "Beef". Guessing one would silently give the
    # user brisket when they meant mince, along with the wrong shelf life.
    form = PantryItemForm(data=form_data("Beef"))

    assert not form.is_valid()
    assert "Pick the specific one" in str(form.errors["catalog_item"])


@pytest.mark.django_db
def test_an_unknown_food_is_refused():
    form = PantryItemForm(data=form_data("Dad's chili"))

    assert not form.is_valid()
    assert "No catalog food called" in str(form.errors["catalog_item"])


@pytest.mark.django_db
def test_a_blank_entry_is_refused():
    form = PantryItemForm(data=form_data("   "))

    assert not form.is_valid()


@pytest.mark.django_db
def test_the_edit_popup_opens_showing_the_name_not_the_id(ground_beef):
    pantry, _ = views.getOrCreateDefaults()
    item = PantryItem.objects.create(pantry=pantry, catalog_item=ground_beef,
                                     location="FRIDGE")

    form = PantryItemForm(instance=item)

    assert form.initial["catalog_item"] == "Beef (ground)"


@pytest.mark.django_db
def test_posting_a_typed_name_adds_the_item(client, ground_beef):
    response = client.post(reverse("core:add_pantry_item"),
                           data=form_data("Beef (ground)"))

    assert response.status_code == 302
    assert PantryItem.objects.get().catalog_item == ground_beef


@pytest.mark.django_db
def test_the_page_offers_every_food_to_the_datalist(client):
    response = client.get(reverse("core:home"))
    html = response.content.decode()

    assert 'id="catalog-options"' in html
    assert html.count("<option") >= GlobalCatalogItem.objects.count()
