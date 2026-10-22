import pytest
import logging
import re
from bs4 import BeautifulSoup
from django.urls import reverse
from django.test import TestCase
from django.test import TransactionTestCase
from core.models import Pantry, PantryItem, GlobalCatalogItem, User
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

@pytest.mark.django_db
def test_home_page_setup():
  # added to ensure tests work. 
  views.getOrCreateDefaults()

  assert Pantry.objects.count() == 1
  assert PantryItem.objects.count() == 10
  assert GlobalCatalogItem.objects.count() == 10


@pytest.mark.django_db
def test_home_page_empty(client):
  # added to ensure tests work. 
  # views.getOrCreateDefaults()

  response = client.get(reverse("core:home"))
  assert countNumberOfElements(response, "container") == PantryItem.objects.count() == 10

@pytest.mark.django_db
def test_home_page_populated(client):
  # added to ensure tests work. 
  views.getOrCreateDefaults()

  response = client.get(reverse("core:home"))
  assert countNumberOfElements(response, "container") == PantryItem.objects.count() == 10

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
  assert response.status_code == 200 
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
  
  url = reverse('core:delete_pantry_item', kwargs={'id': 10})
  # ACT
  response = client.post(url)

  # ASSERT
  assert response.status_code == 302 
  
  response = client.get(reverse("core:home"))

  assert countNumberOfElements(response, "container") == 9

import json
import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_drag_drop_task_assignment_view(client):
    # Setup test data
        
    user = User.objects.create_user(username="user1", password="password")
    pantry = Pantry.objects.create(user=user, name="Pantry1")
    item, _ = GlobalCatalogItem.objects.get_or_create(
      name = "fruits",
      category = "Fruit",
      defaults={"estimated_expiration_days": 7}
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
    response = client.post(
        url,
        data=json.dumps(payload),
        content_type="application/json"
    )

    # Assert response status and database state
    assert response.status_code == 200
    assert PantryItem.objects.get(id=pantryItem.id).location == "FRIDGE"

    # task.refresh_from_db()
    # assert task.assigned_to == employee