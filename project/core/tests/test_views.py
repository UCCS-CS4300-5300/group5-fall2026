import pytest
import logging
import re
from bs4 import BeautifulSoup
from django.urls import reverse
from django.test import TestCase
from django.test import TransactionTestCase
from core.models import Pantry, PantryItem, GlobalCatalogItem
from core import views
 
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
 
 
def addOneItem(pantry, name="Apples", location="SHELVES"):
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
 
 
@pytest.mark.django_db
def test_home_page_setup():
  # getOrCreateDefaults makes a user and a pantry, and nothing else.
  # It used to seed one pantry item per catalog entry, which would now
  # create 661 of them on the first page request.
  views.getOrCreateDefaults()
 
  assert Pantry.objects.count() == 1
  assert PantryItem.objects.count() == 0
 
  # The catalog comes from the USDA data migration, not from a request
  assert GlobalCatalogItem.objects.count() >= 661
 
 
@pytest.mark.django_db
def test_home_page_empty(client):
  # A new pantry is empty and each of the three containers says so
  response = client.get(reverse("core:home"))
 
  assert response.status_code == 200
  assert countNumberOfElements(response, "container") == 0
  assert PantryItem.objects.count() == 0
  assert b"No shelf products found" in response.content
  assert b"No fridge products found" in response.content
  assert b"No freezer products found" in response.content
 
 
@pytest.mark.django_db
def test_home_page_populated(client):
  # ARRANGE
  pantry, user = views.getOrCreateDefaults()
  addOneItem(pantry)
  addOneItem(pantry, name="Bananas")
 
  # ACT
  response = client.get(reverse("core:home"))
 
  # ASSERT
  assert countNumberOfElements(response, "container") == PantryItem.objects.count() == 2
 
 
@pytest.mark.django_db
def test_items_appear_in_their_own_container(client):
  # Each item renders under the container it was stored in, not all in one
  pantry, user = views.getOrCreateDefaults()
  addOneItem(pantry, name="Apples", location="SHELVES")
  addOneItem(pantry, name="Bananas", location="FRIDGE")
 
  response = client.get(reverse("core:home"))
  context = response.context
 
  assert [i.catalog_item.name for i in context["shelves_items"]] == ["Apples"]
  assert [i.catalog_item.name for i in context["fridge_items"]] == ["Bananas"]
  assert context["freezer_items"] == []
 
 
@pytest.mark.django_db
def test_home_page_Add_item(client):
  # ARRANGE
  pantry, user = views.getOrCreateDefaults()
  catalog_item = GlobalCatalogItem.objects.filter(name="Apples").first()
  if catalog_item is None:
    catalog_item = GlobalCatalogItem.objects.create(name="Apples", category="Fruit")
 
  # location is a required field on the form now
  form_data = {
    "catalog_item": catalog_item.id,
    "quantity": 20,
    "date_stored": "2026-10-09",
    "date_expired": "2026-10-16",
    "location": "SHELVES",
  }
 
  # ACT
  response = client.post(reverse('core:add_pantry_item'), data=form_data)
 
  # ASSERT
  assert response.status_code == 302          # redirects home on success
  assert PantryItem.objects.count() == 1
 
  item = PantryItem.objects.first()
  assert item.quantity == 20
  assert item.catalog_item == catalog_item
  assert item.location == "SHELVES"
 
  response = client.get(reverse("core:home"))
  assert countNumberOfElements(response, "container") == 1
 
 
@pytest.mark.django_db
def test_home_page_delete_item(client):
  # ARRANGE
  pantry, user = views.getOrCreateDefaults()
  item = addOneItem(pantry)
 
  response = client.get(reverse("core:home"))
  assert countNumberOfElements(response, "container") == 1
 
  # ACT
  url = reverse('core:delete_pantry_item', kwargs={'id': item.id})
  response = client.post(url)
 
  # ASSERT
  assert response.status_code == 302
  assert PantryItem.objects.count() == 0
 
  response = client.get(reverse("core:home"))
  assert countNumberOfElements(response, "container") == 0