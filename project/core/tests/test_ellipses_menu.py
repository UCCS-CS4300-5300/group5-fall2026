import pytest
from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse
from core.models import GlobalCatalogItem, Pantry, PantryItem


# We need a test to ensure pantry view successfully renders ellipse menu
# container and button class
@pytest.mark.django_db
def test_ellipse_menu_rendering():
    user = User.objects.create_user(username="testuser", password="password")
    pantry = Pantry.objects.create(user=user)
    catalog_item = GlobalCatalogItem.objects.create(name="Milk", category="Dairy")
    PantryItem.objects.create(
        pantry=pantry,
        catalog_item=catalog_item,
        quantity=1,
        location="FRIDGE"
    )

    client = Client()
    client.force_login(user) 
    response = client.get(reverse('core:home'))
    assert response.status_code == 200
    content = response.content.decode('utf-8')

    assert 'item-menu-container' in content
    assert 'class="ellipses-btn"' in content

# We need a test to ensure the ellipse submenu contains edit, delete view detail
@pytest.mark.django_db
def test_ellipses_submenu_container():
    user, _ = User.objects.get_or_create(username="testuser")
    pantry, _ = Pantry.objects.get_or_create(user=user)
    catalog_item, _ = GlobalCatalogItem.objects.get_or_create(name="Milk", category="Dairy")
    
    if not PantryItem.objects.filter(pantry=pantry).exists():
        PantryItem.objects.create(
            pantry=pantry,
            catalog_item=catalog_item,
            quantity=1,
            location="FRIDGE"
        )

    client = Client()
    client.force_login(user)
    response = client.get(reverse('core:home'))
    assert response.status_code == 200
    content = response.content.decode('utf-8')
    assert 'item-submenu' in content
    assert 'View Details' in content
    assert 'Edit' in content
    assert 'Delete' in content

# We need a test to test that the ellipses menu works for certain pantry
# item identifiers (certain pantry items)
@pytest.mark.django_db
def test_ellipses_submenu_unique_id():
    user = User.objects.create_user(username="ellipsestester", password="password")
    pantry = Pantry.objects.create(user=user)
    catalog_item = GlobalCatalogItem.objects.create(name="Apples", category="Fruit")
    
    # Specific test item
    item = PantryItem.objects.create(
        pantry=pantry,
        catalog_item=catalog_item,
        quantity=3,
        location="SHELF"
    )

    client = Client()
    client.force_login(user)
    response = client.get(reverse('core:home'))
    assert response.status_code == 200
    content = response.content.decode('utf-8')

    # We will assert if it has that specific item ID
    assert f'item-submenu-{item.id}' in content
    assert f'delete_pantry_item/{item.id}/' in content
    assert f'edit-dialog-{item.id}' in content

# We need a test to check when the pantry is empty as well so
# that there is no button present
@pytest.mark.django_db
def test_ellipses_menu_absent_when_pantry_empty():
    user = User.objects.create_user(username="emptyuser", password="password")
    Pantry.objects.create(user=user)

    client = Client()
    client.force_login(user)
    response = client.get(reverse('core:home'))
    assert response.status_code == 200
    content = response.content.decode('utf-8')

    assert 'item-menu-container' not in content
    assert 'class="ellipses-btn"' not in content

# We need a test to verify ellipses menu render across Shelves, 
# freezer and fridge as well. 
@pytest.mark.django_db
def test_ellipses_menu_renders_across_all_locations():
    user = User.objects.create_user(username="multiuser", password="password")
    pantry = Pantry.objects.create(user=user)
    catalog_item = GlobalCatalogItem.objects.create(name="MultiItem", category="General")

    item_shelf = PantryItem.objects.create(pantry=pantry, catalog_item=catalog_item, quantity=1, location="SHELF")
    item_freezer = PantryItem.objects.create(pantry=pantry, catalog_item=catalog_item, quantity=1, location="FREEZER")
    item_fridge = PantryItem.objects.create(pantry=pantry, catalog_item=catalog_item, quantity=1, location="FRIDGE")

    client = Client()
    client.force_login(user)
    response = client.get(reverse('core:home'))
    assert response.status_code == 200
    content = response.content.decode('utf-8')

    for item in [item_shelf, item_freezer, item_fridge]:
        assert f'item-submenu-{item.id}' in content