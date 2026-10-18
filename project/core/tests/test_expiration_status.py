import pytest
from datetime import timedelta
from django.contrib.auth.models import User
from django.utils import timezone
from core.models import GlobalCatalogItem, Pantry, PantryItem


def make_item(days_until_expiry):
    user = User.objects.create_user("tester")
    pantry = Pantry.objects.create(user=user)
    catalog = GlobalCatalogItem.objects.create(name="Milk", category="Dairy")
    return PantryItem(
        pantry=pantry,
        catalog_item=catalog,
        date_expired=timezone.localdate() + timedelta(days=days_until_expiry),
    )


@pytest.mark.django_db
def test_four_days_out_is_fresh():
    assert make_item(4).expiration_status == "Fresh"


@pytest.mark.django_db
def test_three_days_out_is_expiring_soon():
    assert make_item(3).expiration_status == "Expiring Soon"


@pytest.mark.django_db
def test_yesterday_is_expired():
    assert make_item(-1).expiration_status == "Expired"
