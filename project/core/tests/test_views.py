import pytest
import logging
import re
from bs4 import BeautifulSoup
from django.urls import reverse
from django.test import TestCase
from django.test import TransactionTestCase
from core.models import Pantry, PantryItem, GlobalCatalogItem, User
from core import views
import json
import pytest
from django.urls import reverse

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(module)s (Line %(lineno)d): %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler("app.log", mode='w'),  # overwrites the file
        logging.StreamHandler()                    # Outputs to console
    ]
)
 
 
def countNumberOfElements(response, element):
  soup = BeautifulSoup(response.content.decode(), 'html.parser')
  matches = soup.find_all(class_="container")
  return len(matches)
 
 
def addOneItem(pantry, name="Apples", location="SHELF"):
  """
  Put one item in the pantry. The pantry no longer seeds itself, so tests
  that need an item have to create one. Defaults to the shelves, which is
  where the add form puts things unless told otherwise.
  """
  catalog_item = GlobalCatalogItem.objects.filter(name=name).first()
  if catalog_item is None:
    catalog_item = GlobalCatalogItem.objects.create(name=name, category="Fruit")
  return PantryItem.objects.create(
    pantry=pantry, catalog_item=catalog_item, quantity=5, location=location)
 
 
@pytest.fixture
def logged_in_client(client, db):
  user = User.objects.create_user(username="views-user", password="password")
  client.force_login(user)
  return client


@pytest.mark.django_db
def test_home_page_setup(logged_in_client):
  # Creating a user through the model creates its empty pantry; it does
  # not seed one pantry item per catalog entry.
  assert Pantry.objects.count() == 1
  assert PantryItem.objects.count() == 0
 
  # The catalog comes from the USDA data migration, not from a request
  assert GlobalCatalogItem.objects.count() >= 661
 
 
@pytest.mark.django_db
def test_home_page_empty(logged_in_client):
  # A new pantry is empty and each of the three containers says so
  response = logged_in_client.get(reverse("core:home"))
 
  assert response.status_code == 200
  assert countNumberOfElements(response, "container") == 0
  assert PantryItem.objects.count() == 0
  assert b"circle" not in response.content
  assert b"pantry-item-" not in response.content
  assert b"draggable-card" not in response.content
 
@pytest.mark.django_db
def test_home_page_populated(logged_in_client):
  # ARRANGE
  pantry = User.objects.get(username="views-user").pantry
  addOneItem(pantry)
  addOneItem(pantry, name="Bananas")

  # ACT
  response = logged_in_client.get(reverse("core:home"))
  # ASSERT
  assert countNumberOfElements(response, "container") == PantryItem.objects.count() == 2
 
 
@pytest.mark.django_db
def test_items_appear_in_their_own_container(logged_in_client):
  # Each item renders under the container it was stored in, not all in one
  pantry = User.objects.get(username="views-user").pantry
  addOneItem(pantry, name="Apples", location="SHELF")
  addOneItem(pantry, name="Bananas", location="FRIDGE")

  response = logged_in_client.get(reverse("core:home"))
  context = response.context
 
  assert [i.catalog_item.name for i in context["shelves_items"]] == ["Apples"]
  assert [i.catalog_item.name for i in context["fridge_items"]] == ["Bananas"]
  assert context["freezer_items"] == []
 
 
@pytest.mark.django_db
def test_home_page_Add_item(logged_in_client):
  # ARRANGE
  user = User.objects.get(username="views-user")
  catalog_item = GlobalCatalogItem.objects.filter(name="Apples").first()
  if catalog_item is None:
    catalog_item = GlobalCatalogItem.objects.create(name="Apples", category="Fruit")
 
  # location is a required field on the form now
  form_data = {
    "catalog_item": str(catalog_item),
    "quantity": 20,
    "date_stored": "2026-10-09",
    "date_expired": "2026-10-16",
    "location": "SHELF",
  }
 
  # ACT
  response = logged_in_client.post(reverse('core:add_pantry_item'), data=form_data)
 
  # ASSERT
  assert response.status_code == 302          # redirects home on success
  assert PantryItem.objects.count() == 1
 
  item = PantryItem.objects.first()
  assert item.quantity == 20
  assert item.catalog_item == catalog_item
  assert item.location == "SHELF"
 
  response = logged_in_client.get(reverse("core:home"))
  assert countNumberOfElements(response, "container") == 1


@pytest.mark.django_db
def test_home_page_delete_item(logged_in_client):
  # ARRANGE
  pantry = User.objects.get(username="views-user").pantry
  item = addOneItem(pantry)
 
  response = logged_in_client.get(reverse("core:home"))

  assert countNumberOfElements(response, "container") == 1
 
  # ACT
  url = reverse('core:delete_pantry_item', kwargs={'id': item.id})
  response = logged_in_client.post(url)
 
  # ASSERT
  assert response.status_code == 302
  assert PantryItem.objects.count() == 0
 
  response = logged_in_client.get(reverse("core:home"))
  assert countNumberOfElements(response, "container") == 0

@pytest.mark.django_db
def test_drag_drop_task_assignment_view(logged_in_client):
    # Setup test data
        
    user = User.objects.create_user(username="user1", password="password")
    pantry = user.pantry
    item, _ = GlobalCatalogItem.objects.get_or_create(
      name = "fruits",
      category = "Fruit",
    )
    
    pantryItem, _ = PantryItem.objects.get_or_create(
        pantry=pantry,
        catalog_item=item,
        defaults={"quantity": 5},
        location="SHELF"
    )
    

    # Simulate the endpoint your JS calls on drop (e.g., /api/assign-task/)
    url = reverse("core:submit_drag_drop")
    payload = {
        "item_id": 1,
        "raw_id": 1, # pantryItem.id,
        "target_zone": "FRIDGE"
    }

    # Post as JSON or form data matching your JS implementation
    response = logged_in_client.post(
        url,
        data=json.dumps(payload),
        content_type="application/json"
    )

    # Assert response status and database state
    assert response.status_code == 200
    assert PantryItem.objects.get(id=pantryItem.id).location == "FRIDGE"

@pytest.mark.django_db
def test_drag_drop_task_assignment_view_fails_with_bad_data(logged_in_client):
    # Setup test data
  
    # Simulate the endpoint your JS calls on drop (e.g., /api/assign-task/)
    url = reverse("core:submit_drag_drop")
    payload = {
      "something": 'else'
    }

    # Post as JSON or form data matching your JS implementation
    response = logged_in_client.post(
        url,
        data=json.dumps(payload),
        content_type="application/json"
    )

    # Assert response status and database state
    assert response.status_code == 400

@pytest.mark.django_db
def test_drag_drop_task_assignment_view_fails_with_get(logged_in_client):
    # get url
    url = reverse("core:submit_drag_drop")
    
    response = logged_in_client.get(
        url,
        content_type="application/json"
    )

    # Assert response status
    assert response.status_code == 405


@pytest.mark.django_db
def test_drag_drop_returns_404_when_item_no_longer_exists(logged_in_client):
    url = reverse("core:submit_drag_drop")

    payload = {
        "raw_id": 999999,
        "target_zone": "FRIDGE"
    }

    response = logged_in_client.post(
        url,
        data=json.dumps(payload),
        content_type="application/json"
    )

    assert response.status_code == 404
    assert response.json() == {
        "status": "error",
        "message": "Item not found"
    }


@pytest.mark.django_db
def test_drag_drop_invalid_location_falls_back_to_shelf(logged_in_client):
    user = User.objects.create_user(username="user2", password="password")
    pantry = user.pantry
    catalog_item, _ = GlobalCatalogItem.objects.get_or_create(
        name="vegetables",
        category="Vegetable",
    )

    pantry_item = PantryItem.objects.create(
        pantry=pantry,
        catalog_item=catalog_item,
        location="FRIDGE"
    )

    url = reverse("core:submit_drag_drop")
    payload = {
        "raw_id": pantry_item.id,
        "target_zone": "CABINET"
    }

    response = logged_in_client.post(
        url,
        data=json.dumps(payload),
        content_type="application/json"
    )

    pantry_item.refresh_from_db()

    assert response.status_code == 200
    assert pantry_item.location == "SHELF"


@pytest.mark.django_db
def test_drag_drop_recalculates_expiration_when_location_changes(logged_in_client):
    user = User.objects.create_user(username="cook3", password="password")
    pantry = user.pantry
    chicken = GlobalCatalogItem.objects.get(
        name="Chicken",
        name_subtitle="whole"
    )

    pantry_item = PantryItem.objects.create(
        pantry=pantry,
        catalog_item=chicken,
        location="FRIDGE"
    )

    assert (pantry_item.date_expired - pantry_item.date_stored).days == 2

    url = reverse("core:submit_drag_drop")
    payload = {
        "raw_id": pantry_item.id,
        "target_zone": "FREEZER"
    }

    response = logged_in_client.post(
        url,
        data=json.dumps(payload),
        content_type="application/json"
    )

    pantry_item.refresh_from_db()

    assert response.status_code == 200
    assert pantry_item.location == "FREEZER"
    assert (pantry_item.date_expired - pantry_item.date_stored).days == 360