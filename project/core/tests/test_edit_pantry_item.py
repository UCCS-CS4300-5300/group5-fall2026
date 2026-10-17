import datetime
import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from core.models import GlobalCatalogItem, Pantry, PantryItem

ORIGINAL_DATE = datetime.date(2026, 10, 10)


@pytest.fixture
def item(db):
    user = User.objects.create_user(username="cook", password="pw")
    pantry = Pantry.objects.create(user=user, name="Pantry1")
    milk = GlobalCatalogItem.objects.create(name="Milk", category="Dairy")
    return PantryItem.objects.create(
        pantry=pantry, catalog_item=milk, quantity=1,
        date_stored=datetime.date(2026, 10, 1), date_expired=ORIGINAL_DATE,
    )


def form_data(item, **changes):
    data = {
        "pantry": item.pantry.id,
        "catalog_item": item.catalog_item.id,
        "quantity": item.quantity,
        "date_stored": item.date_stored.isoformat(),
        "date_expired": item.date_expired.isoformat(),
        "location": item.location
    }
    data.update(changes)
    return data


def edit_url(item):
    return reverse("core:edit_pantry_item", args=[item.id])


def test_home_shows_edit_popup(client, item):
    response = client.get(reverse("core:home"))
    assert response.status_code == 200
    assert f'id="edit-dialog-{item.id}"'.encode() in response.content


def test_valid_edit_saves(client, item):
    response = client.post(edit_url(item), form_data(item, quantity=3, date_expired="2026-10-20"))
    assert response.status_code == 302
    item.refresh_from_db()
    assert item.quantity == 3
    assert item.date_expired == datetime.date(2026, 10, 20)


def test_invalid_edit_changes_nothing(client, item):
    response = client.post(edit_url(item), form_data(item, quantity=3, date_expired="not-a-date"))
    assert response.status_code == 200
    assert response.context["open_edit_id"] == item.id
    item.refresh_from_db()
    assert item.quantity == 1
    assert item.date_expired == ORIGINAL_DATE


def test_get_does_not_change_item(client, item):
    response = client.get(edit_url(item))
    assert response.status_code == 302
    item.refresh_from_db()
    assert item.quantity == 1


@pytest.mark.django_db
def test_missing_item_returns_404(client):
    response = client.post(reverse("core:edit_pantry_item", args=[9999]))
    assert response.status_code == 404