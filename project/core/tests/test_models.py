import pytest
import logging
from django.urls import reverse
from django.contrib.auth.models import User
from core.models import GlobalCatalogItem, Pantry, PantryItem
from django.db import IntegrityError
from django.utils import timezone
from datetime import timedelta
 
 
# --- Global Catalog Tests ---
 
@pytest.mark.django_db
def test_global_catalog():
 
 #Test whether an item was created in the global pantry
 item = GlobalCatalogItem.objects.create(
  name = "Apple",
  category = "Fruit"
 )
 
 # Need to assert that it is an apple and has all the designated fields
 assert item.name == "Apple"
 assert str(item) == "Apple"
 assert item.category == "Fruit"
 
 
@pytest.mark.django_db
def test_usda_catalog_is_loaded():
 # The USDA FoodKeeper data migration populates the catalog
 assert GlobalCatalogItem.objects.count() >= 661
 
 
@pytest.mark.django_db
def test_shelf_life_varies_by_storage():
 # Chicken keeps 2 days in the fridge and about a year in the freezer.
 # A single estimated_expiration_days per food could not express this.
 chicken = GlobalCatalogItem.objects.get(name="Chicken", name_subtitle="whole")
 
 assert chicken.shelf_life_days("refrigerate") == 2
 assert chicken.shelf_life_days("freeze") == 360
 
 
@pytest.mark.django_db
def test_duplicate_names_are_allowed():
 # FoodKeeper lists 20 kinds of Ham. A unique name would lose 19 of them.
 assert GlobalCatalogItem.objects.filter(name="Ham").count() == 20
 
 
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
  category = "Fruit"
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
 
 
@pytest.mark.django_db
def test_expiry_is_calculated_from_usda_data():
 # An item added with no expiration date gets one from the USDA shelf life
 # for the place it was put. Raw chicken has no pantry figure at all, so
 # the location is not optional detail here -- on the shelves it would
 # correctly get no date.
 user = User.objects.create_user(username="cook", password="password")
 pantry = Pantry.objects.create(user=user, name="Pantry1")
 chicken = GlobalCatalogItem.objects.get(name="Chicken", name_subtitle="whole")
 
 item = PantryItem.objects.create(
  pantry=pantry, catalog_item=chicken, location="FRIDGE")
 
 assert (item.date_expired - item.date_stored).days == 2
 
 
@pytest.mark.django_db
def test_location_changes_the_expiry():
 # The same food in two places gets two different dates. If anyone breaks
 # LOCATION_TO_STORAGE, filter(storage="FRIDGE") matches nothing and every
 # item silently saves with no date -- this is what catches that.
 user = User.objects.create_user(username="cook2", password="password")
 pantry = Pantry.objects.create(user=user, name="Pantry1")
 chicken = GlobalCatalogItem.objects.get(name="Chicken", name_subtitle="whole")
 
 fridge = PantryItem.objects.create(
  pantry=pantry, catalog_item=chicken, location="FRIDGE")
 freezer = PantryItem.objects.create(
  pantry=pantry, catalog_item=chicken, location="FREEZER")
 
 assert (fridge.date_expired - fridge.date_stored).days == 2
 assert (freezer.date_expired - freezer.date_stored).days == 360
 
 
@pytest.mark.django_db
def test_food_with_no_usda_figure_saves_without_a_date():
 # 14 foods (salt, water, hard liquor) have no USDA duration at all.
 # They must save cleanly rather than crash.
 user = User.objects.create_user(username="cook", password="password")
 pantry = Pantry.objects.create(user=user, name="Pantry1")
 salt = GlobalCatalogItem.objects.filter(name="Salt").first()
 
 item = PantryItem.objects.create(pantry=pantry, catalog_item=salt)
 
 assert item.date_expired is None
 assert item.expiration_status == "Unknown"
 
 
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
  category="Fruit"
 )
 
 pantry_item = PantryItem.objects.create(
  pantry=pantry,
  catalog_item=catalog_item,
  quantity=3,
  date_expired=timezone.localdate() + timedelta(days=7)
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
  category="Fruit"
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
  category="Dairy"
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