
import pytest
import logging
from django.urls import reverse
from .models import StarterItem

@pytest.mark.django_db
def test_model():
 item=StarterItem.objects.create(title="Example"); assert str(item)=="Example"

@pytest.mark.django_db
def test_home(client):
 r=client.get(reverse("core:home"));
 logging.debug("Checking status code for 200")
 assert r.status_code==200;
 logging.debug("Checking content from response")
 assert b"Shelf Life" in r.content
 assert b"Pantry" in r.content
 assert b"Pantry Organizer" in r.content

# @pytest.mark.django_db
# def test_only_active(client):
#  StarterItem.objects.create(title="Visible",is_active=True); StarterItem.objects.create(title="Hidden",is_active=False)
#  r=client.get(reverse("core:home")); assert b"Banana" in r.content; assert b"Pantry" not in r.content
