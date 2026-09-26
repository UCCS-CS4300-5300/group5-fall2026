
import pytest
import logging
from django.urls import reverse
#from .models import StarterItem
from django.contrib.auth.models import User
from .models import GlobalCatalogItem, Pantry, PantryItem
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
