import pytest

from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse


@pytest.mark.django_db
def test_statistics_sidebar_section_is_available():
    user = User.objects.create_user(
        username="statistics_user",
        password="password"
    )

    client = Client()
    client.force_login(user)

    response = client.get(reverse("core:home"))

    assert response.status_code == 200

    content = response.content.decode("utf-8")

    assert 'data-target="panel-statistics"' in content
    assert 'id="panel-statistics"' in content
    assert "Food Statistics" in content
    assert 'class="back-to-menu-btn"' in content


@pytest.mark.django_db
def test_statistics_sidebar_contains_future_statistics_options():
    user = User.objects.create_user(
        username="statistics_options_user",
        password="password"
    )

    client = Client()
    client.force_login(user)

    response = client.get(reverse("core:home"))

    assert response.status_code == 200

    content = response.content.decode("utf-8")

    assert 'id="statistics-history-option"' in content
    assert "Consumed / Trashed History" in content

    assert 'id="statistics-leaderboard-option"' in content
    assert "Top Consumed / Trashed Foods" in content

    assert 'data-target="panel-pantry"' in content
    assert 'data-target="panel-ai"' in content
    assert 'data-target="panel-manual"' in content