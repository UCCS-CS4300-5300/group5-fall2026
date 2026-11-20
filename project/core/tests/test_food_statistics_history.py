import json

import pytest

from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse
from django.utils.html import escape

from core.models import GlobalCatalogItem, PantryItem, PantryItemHistory


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="history_user",
        password="password"
    )


@pytest.fixture
def client_in(user):
    client = Client()
    client.force_login(user)
    return client


@pytest.fixture
def catalog_item(db):
    return GlobalCatalogItem.objects.first()


@pytest.mark.django_db
def test_delete_button_records_history(client_in, user, catalog_item):
    item = PantryItem.objects.create(
        pantry=user.pantry,
        catalog_item=catalog_item,
        location="SHELF"
    )

    response = client_in.post(
        reverse("core:delete_pantry_item", args=[item.id])
    )

    assert response.status_code == 302
    assert not PantryItem.objects.filter(id=item.id).exists()

    history = PantryItemHistory.objects.get()
    assert history.pantry == user.pantry
    assert history.item_name == catalog_item.name


@pytest.mark.django_db
def test_drag_to_trash_records_history(client_in, user, catalog_item):
    item = PantryItem.objects.create(
        pantry=user.pantry,
        catalog_item=catalog_item,
        location="SHELF"
    )

    response = client_in.post(
        reverse("core:submit_drag_drop"),
        data=json.dumps({
            "item_id": f"pantry-item-{item.id}",
            "raw_id": str(item.id),
            "target_zone": "DELETE",
            "query_string": ""
        }),
        content_type="application/json"
    )

    assert response.status_code == 200
    assert not PantryItem.objects.filter(id=item.id).exists()

    history = PantryItemHistory.objects.get()
    assert history.item_name == catalog_item.name


@pytest.mark.django_db
def test_multiple_deletions_create_multiple_history_records(
    client_in,
    user,
    catalog_item
):
    for _ in range(2):
        item = PantryItem.objects.create(
            pantry=user.pantry,
            catalog_item=catalog_item,
            location="SHELF"
        )

        client_in.post(
            reverse("core:delete_pantry_item", args=[item.id])
        )

    assert PantryItemHistory.objects.filter(
        pantry=user.pantry,
        item_name=catalog_item.name
    ).count() == 2


@pytest.mark.django_db
def test_statistics_panel_displays_deleted_food_history(
    client_in,
    user,
    catalog_item
):
    for _ in range(2):
        item = PantryItem.objects.create(
            pantry=user.pantry,
            catalog_item=catalog_item,
            location="SHELF"
        )

        client_in.post(
            reverse("core:delete_pantry_item", args=[item.id])
        )

    response = client_in.get(reverse("core:home"))

    assert response.status_code == 200

    content = response.content.decode("utf-8")
    normalized_content = " ".join(content.split())

    assert "Trashed Food History" in content
    assert escape(catalog_item.name) in content
    assert "Deleted 2 times" in normalized_content
    assert "Last deleted:" in content