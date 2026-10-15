import pytest
import logging
from django.urls import reverse
#from .models import StarterItem
from django.contrib.auth.models import User
from core.models import GlobalCatalogItem, Pantry, PantryItem
from django.db import IntegrityError
from django.utils import timezone
from datetime import timedelta

"""
@pytest.mark.django_db
def test_model():
 item=StarterItem.objects.create(title="Example"); assert str(item)=="Example"

@pytest.mark.django_db

def test_home(client):
 r=client.get(reverse("core:home")); assert r.status_code==200; assert b"Your project starts here." in r.content

@pytest.mark.django_db
def test_only_active(client):
 StarterItem.objects.create(title="Visible",is_active=True); StarterItem.objects.create(title="Hidden",is_active=False)
 r=client.get(reverse("core:home")); assert b"Visible" in r.content; assert b"Hidden" not in r.content
"""


# --- Global Catalog Tests ---

@pytest.mark.django_db
def test_global_catalog():
 
 #Test whether an item was created in the global pantry
 item = GlobalCatalogItem.objects.create(
  name = "Apple",
  category = "Fruit",
  estimated_expiration_days = 7
 )

 # Need to assert that it is an apple and has all the designated fields
 assert item.name == "Apple"
 assert str(item) == "Apple"
 assert item.category == "Fruit"
 assert item.estimated_expiration_days == 7
  

# --- Pantry tests ---

@pytest.mark.django_db
def test_unique_pantry():
 # We will test whether a single user can only have one pantry
 user = User.objects.create_user(username="user1", password = "password")
 Pantry.objects.create(user=user, name = "Pantry1")

 # Creating a second pantry for the test
 with pytest.raises(IntegrityError):
  Pantry.objects.create(user=user, name="Pantry2")


# --- Pantry Item tests ---

@pytest.mark.django_db
def test_item_passed():
 # This test tests whether a catalog item can be added to the pantry
 user = User.objects.create_user(username="user1", password = "password")
 pantry = Pantry.objects.create(user=user, name = "Pantry1")

 catalog_item = GlobalCatalogItem.objects.create(
  name = "Apple",
  category = "Fruit",
  estimated_expiration_days = 7
 )

 pantry_item = PantryItem.objects.create(
  pantry = pantry,
  catalog_item = catalog_item,
  quantity = 5
 )

 assert pantry_item.pantry == pantry
 assert pantry_item.catalog_item == catalog_item
 assert pantry_item.quantity == 5
 assert pantry.items.filter(id=pantry_item.id).exists()


# --- Pantry Retrieve / Read Tests ---

@pytest.mark.django_db
def test_pantry_item_details(client):
 # Create a pantry item for the detail page
 user = User.objects.create_user(
  username="detail_test_user",
  password="password"
 )

 pantry = Pantry.objects.create(
  user=user,
  name="Test Pantry"
 )

 catalog_item = GlobalCatalogItem.objects.create(
  name="Orange",
  category="Fruit",
  estimated_expiration_days=7
 )

 pantry_item = PantryItem.objects.create(
  pantry=pantry,
  catalog_item=catalog_item,
  quantity=3
 )

 # Open the detail page for this item
 response = client.get(
  reverse(
   "core:pantry_item_detail",
   args=[pantry_item.id]
  )
 )

 # Make sure the details page works and displays the item information
 assert response.status_code == 200
 assert b"Orange" in response.content
 assert b"Quantity:" in response.content
 assert b"Date Stored:" in response.content
 assert b"Expiration Date:" in response.content
 assert b"Status:" in response.content
 assert b"Fresh" in response.content


@pytest.mark.django_db
def test_missing_pantry_item_returns_404(client):
 # Try to open an item that does not exist
 response = client.get(
  reverse(
   "core:pantry_item_detail",
   args=[9999]
  )
 )

 assert response.status_code == 404


@pytest.mark.django_db
def test_current_pantry_item_displayed_on_home_page(client):
 # Create a current pantry item
 user = User.objects.create_user(
  username="home_test_user",
  password="password"
 )

 pantry = Pantry.objects.create(
  user=user,
  name="Test Pantry"
 )

 catalog_item = GlobalCatalogItem.objects.create(
  name="Banana",
  category="Fruit",
  estimated_expiration_days=7
 )

 pantry_item = PantryItem.objects.create(
  pantry=pantry,
  catalog_item=catalog_item,
  quantity=4,
  date_expired=timezone.localdate() + timedelta(days=7)
 )

 response = client.get(reverse("core:home"))

 # The current item should appear on the pantry page
 assert response.status_code == 200
 assert b"Banana" in response.content

 # The page should include a link to the item's detail page
 detail_url = reverse(
  "core:pantry_item_detail",
  args=[pantry_item.id]
 )

 assert detail_url.encode() in response.content
 assert b"View Details" in response.content


@pytest.mark.django_db
def test_expired_pantry_item_not_displayed_as_current(client):
 # Create an expired pantry item
 user = User.objects.create_user(
  username="expired_test_user",
  password="password"
 )

 pantry = Pantry.objects.create(
  user=user,
  name="Test Pantry"
 )

 catalog_item = GlobalCatalogItem.objects.create(
  name="Old Milk",
  category="Dairy",
  estimated_expiration_days=7
 )

 pantry_item = PantryItem.objects.create(
  pantry=pantry,
  catalog_item=catalog_item,
  quantity=9,
  date_expired=timezone.localdate() - timedelta(days=1)
 )

 response = client.get(reverse("core:home"))

 assert response.status_code == 200

 # The expired item should not have a detail link in the current pantry
 detail_url = reverse(
  "core:pantry_item_detail",
  args=[pantry_item.id]
 )

 assert detail_url.encode() not in response.content