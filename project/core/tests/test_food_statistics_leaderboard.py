import pytest

from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse

from core.models import PantryItemHistory


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="leaderboard_user",
        password="password"
    )


@pytest.fixture
def client_in(user):
    client = Client()
    client.force_login(user)
    return client


@pytest.mark.django_db
def test_statistics_leaderboard_ranks_most_deleted_foods(client_in, user):
    pantry = user.pantry

    for _ in range(3):
        PantryItemHistory.objects.create(
            pantry=pantry,
            item_name="Milk"
        )

    for _ in range(2):
        PantryItemHistory.objects.create(
            pantry=pantry,
            item_name="Bread"
        )

    PantryItemHistory.objects.create(
        pantry=pantry,
        item_name="Eggs"
    )

    response = client_in.get(reverse("core:home"))

    assert response.status_code == 200

    foods = list(response.context["top_trashed_foods"])

    assert foods[0]["item_name"] == "Milk"
    assert foods[0]["times_deleted"] == 3

    assert foods[1]["item_name"] == "Bread"
    assert foods[1]["times_deleted"] == 2

    assert foods[2]["item_name"] == "Eggs"
    assert foods[2]["times_deleted"] == 1


@pytest.mark.django_db
def test_statistics_leaderboard_only_shows_top_five(client_in, user):
    pantry = user.pantry

    for i in range(6):
        for _ in range(6 - i):
            PantryItemHistory.objects.create(
                pantry=pantry,
                item_name=f"Food {i}"
            )

    response = client_in.get(reverse("core:home"))

    foods = list(response.context["top_trashed_foods"])

    assert len(foods) == 5


@pytest.mark.django_db
def test_statistics_leaderboard_displays_in_template(client_in, user):
    PantryItemHistory.objects.create(
        pantry=user.pantry,
        item_name="Apples"
    )

    response = client_in.get(reverse("core:home"))

    content = response.content.decode("utf-8")

    assert "Top Trashed Foods" in content
    assert "Apples" in content
    assert "Deleted 1 time" in " ".join(content.split())