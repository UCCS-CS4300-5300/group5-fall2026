import pytest
import logging
import re
from bs4 import BeautifulSoup
from django.urls import reverse
from django.test import TestCase
from django.test import TransactionTestCase
from core.models import Pantry, PantryItem, GlobalCatalogItem
from . import views

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

@pytest.mark.django_db
def test_home_page_setup():
  # added to ensure tests work. 
  views.getOrCreateDefaults()

  assert Pantry.objects.count() == 1
  assert PantryItem.objects.count() == 11
  assert GlobalCatalogItem.objects.count() == 11


@pytest.mark.django_db
def test_home_page_empty(client):
  # added to ensure tests work. 
  # views.getOrCreateDefaults()

  response = client.get(reverse("core:home"))
  assert countNumberOfElements(response, "container") == PantryItem.objects.count() == 11

@pytest.mark.django_db
def test_home_page_populated(client):
  # added to ensure tests work. 
  views.getOrCreateDefaults()

  response = client.get(reverse("core:home"))
  assert countNumberOfElements(response, "container") == PantryItem.objects.count() == 11

@pytest.mark.django_db
def test_home_page_Add_item(client):
  # added to ensure tests work. 
  
  # ARRANGE
  views.getOrCreateDefaults()
  
  # ACT
  response = client.post(reverse("core:home"))

  # ASSERT
  countNumberOfElements(response, "container") == 11

  # ARRANGE
  form_data = {
    "pantry": Pantry.objects.first().name,
    "catalog_item" : GlobalCatalogItem.objects.first().name,
    "quantity" : 20,
    "date_stored" : "Oct. 9, 2026",
    "date_expired" : "Oct. 9, 2026"
  }
        
  # ACT
  response = client.post(reverse('core:add_pantry_item'), data=form_data)

  # ASSERT
  assert response.status_code == 302 
  countNumberOfElements(response, "container") == 12

@pytest.mark.django_db
def test_home_page_delete_item(client):
  # added to ensure tests work. 
  
  # ARRANGE
  views.getOrCreateDefaults()
  
  # ACT
  response = client.post(reverse("core:home"))

  # ASSERT
  countNumberOfElements(response, "container") == 11

  # ARRANGE
  
  url = reverse('core:delete_pantry_item', kwargs={'id': 11})
  # ACT
  response = client.post(url)

  # ASSERT
  assert response.status_code == 302 
  
  response = client.get(reverse("core:home"))

  assert countNumberOfElements(response, "container") == 10