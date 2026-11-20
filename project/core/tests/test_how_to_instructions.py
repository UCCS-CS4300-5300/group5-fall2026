import pytest

from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse


@pytest.mark.django_db
def test_how_to_instructions_are_available_from_home_page():
    user = User.objects.create_user(
        username="howto_user",
        password="password"
    )

    client = Client()
    client.force_login(user)

    response = client.get(reverse("core:home"))

    assert response.status_code == 200

    content = response.content.decode("utf-8")

    # How-To trigger and popup
    assert 'class="how-to-trigger"' in content
    assert 'id="how-to-dialog"' in content
    assert "How to Use Shelf Life" in content

    # Instructions required by issue #118
    assert "Adding Food" in content
    assert "Moving Food" in content
    assert "Viewing and Editing Items" in content
    assert "Deleting Food" in content


@pytest.mark.django_db
def test_how_to_instructions_explain_main_features():
    user = User.objects.create_user(
        username="howto_content_user",
        password="password"
    )

    client = Client()
    client.force_login(user)

    response = client.get(reverse("core:home"))
    content = response.content.decode("utf-8")

    # Important walkthrough content
    assert "Pantry Organizer" in content
    assert "three-dot menu" in content
    assert "Expiration Status" in content
    assert "AI Assisted Chef" in content

    # The instructions remain accessible from the page-level help trigger.
    assert "showModal()" in content