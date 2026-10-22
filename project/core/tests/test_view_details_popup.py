import datetime

import pytest
from django.contrib.auth.models import User
from django.urls import reverse

from core.models import GlobalCatalogItem, Pantry, PantryItem


# Makes a normal pantry item that I can use in the popup test
@pytest.fixture
def pantry_item():

    # Need a user first because the pantry belongs to a user
    user = User.objects.create_user(
        username="popup_test_user",
        password="test-password"
    )

    # Test pantry for the item
    pantry = Pantry.objects.create(
        user=user,
        name="Test Pantry"
    )

    # PantryItem needs a catalog item connected to it
    catalog_item = GlobalCatalogItem.objects.create(
        name="Milk",
        category="Dairy"
    )

    # This is the item I will look for on the home page
    return PantryItem.objects.create(
        pantry=pantry,
        catalog_item=catalog_item,
        quantity=2,
        date_stored=datetime.date(2026, 10, 15),
        date_expired=datetime.date(2026, 10, 25),
        location="FRIDGE"
    )


@pytest.mark.django_db
def test_view_details_popup_contains_item_information(client, pantry_item):
    """
    Checks that a normal item has a details popup
    and that the right info shows up in it.
    """

    # Load the main pantry page
    response = client.get(reverse("core:home"))

    # Make sure the page loaded correctly
    assert response.status_code == 200

    # Turn the response into text so I can check the HTML
    content = response.content.decode()

    # Each item should have its own popup based on the item id
    assert f'details-dialog-{pantry_item.id}' in content

    # Check that the item's info is somewhere in the popup/page
    assert pantry_item.catalog_item.name in content
    assert pantry_item.catalog_item.category in content
    assert str(pantry_item.quantity) in content
    assert "Fridge" in content

    # Check the dates too
    assert "Oct. 15, 2026" in content
    assert "Oct. 25, 2026" in content


@pytest.mark.django_db
def test_expired_item_still_has_view_details_popup(client):
    """
    Checks that expired food can still use View Details.
    """

    # Separate user just for this test
    user = User.objects.create_user(
        username="expired_popup_user",
        password="test-password"
    )

    # Pantry for the expired item
    pantry = Pantry.objects.create(
        user=user,
        name="Expired Test Pantry"
    )

    # Different item so it is easy to find in the page
    catalog_item = GlobalCatalogItem.objects.create(
        name="Old Yogurt",
        category="Dairy"
    )

    # Give it an old expiration date so the status will be Expired
    item = PantryItem.objects.create(
        pantry=pantry,
        catalog_item=catalog_item,
        quantity=1,
        date_stored=datetime.date(2026, 10, 1),
        date_expired=datetime.date(2026, 10, 5),
        location="FRIDGE"
    )

    # Load the pantry page again
    response = client.get(reverse("core:home"))

    assert response.status_code == 200

    # Get the HTML from the response
    content = response.content.decode()

    # Expired items should still get a details popup
    assert f'details-dialog-{item.id}' in content

    # Make sure this is actually the expired item I created
    assert "Old Yogurt" in content
    assert "Expired" in content