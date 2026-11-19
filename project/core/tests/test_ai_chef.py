import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse

from core.ai_chef import (
    FALLBACK_MESSAGE_1,
    FALLBACK_MESSAGE_2,
    ask_chef,
    build_content,
    pantry_item_lookup,
)
from core.models import GlobalCatalogItem, Pantry, PantryItem

# We need a test to ensure home view renders the AI Chef sidebar UI stages
@pytest.mark.django_db
def test_ai_chef_sidebar_ui_renders():
    user = User.objects.create_user(username="chefuiuser", password="password")
    Pantry.objects.get_or_create(user=user)

    client = Client()
    client.force_login(user)
    response = client.get(reverse("core:home"))
    assert response.status_code == 200
    content = response.content.decode("utf-8")

    assert 'id="panel-ai"' in content
    assert 'id="chef-bell-stage"' in content
    assert 'id="chef-bell-btn"' in content
    assert "Ring for Chef" in content
    assert 'id="chef-loading"' in content
    assert 'class="chef-spinner"' in content
    assert 'id="chef-chat-room"' in content
    assert 'id="chef-chat-form"' in content

# We need a test to verify pantry_item_lookup excludes expired items and
# formats usable items cleanly
def test_pantry_item_lookup_filters_expired():
    items = [
        SimpleNamespace(
            display_name="Eggs",
            quantity=6,
            location="FRIDGE",
            expiration_status="Expiring Soon",
        ),
        SimpleNamespace(
            display_name="Old Milk",
            quantity=1,
            location="FRIDGE",
            expiration_status="Expired",
        ),
    ]

    summary = pantry_item_lookup(items)

    assert "Eggs" in summary
    assert "Expiring Soon" in summary
    assert "Old Milk" not in summary

# We need a test to verify pantry_item_lookup handles an empty pantry
def test_pantry_item_lookup_empty():
    assert pantry_item_lookup([]) == "The pantry is currently empty."

# We need a test to ensure ask_chef falls back cleanly when GEMINI_API_KEY
# is missing
def test_ask_chef_missing_api_key_fallback(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    result = ask_chef([], fallback_message=FALLBACK_MESSAGE_1)

    assert result == {
        "ok": False,
        "reply": FALLBACK_MESSAGE_1,
        "fallback": True,
    }

# We need a test to verify the /ai-chef/ endpoint handles initial recipe
# requests using the user's pantry items
@pytest.mark.django_db
def test_ai_chef_chat_init_endpoint():
    user = User.objects.create_user(username="chefendpointuser", password="password")
    pantry, _ = Pantry.objects.get_or_create(user=user)
    catalog_item = GlobalCatalogItem.objects.create(name="Pasta", category="Pantry")
    PantryItem.objects.create(
        pantry=pantry,
        catalog_item=catalog_item,
        quantity=2,
        location="SHELF",
    )

    client = Client()
    client.force_login(user)

    with patch(
        "core.views.ask_chef",
        return_value={"ok": True, "reply": "1. Pasta Aglio", "fallback": False},
    ) as mock_ask:
        response = client.post(
            reverse("core:ai_chef_chat"),
            data=json.dumps({"action": "init"}),
            content_type="application/json",
        )

    assert response.status_code == 200
    assert response.json()["reply"] == "1. Pasta Aglio"
    mock_ask.assert_called_once()

# We need a test to verify /ai-chef/ rejects blank follow-up messages and
# invalid JSON bodies with 400
@pytest.mark.django_db
def test_ai_chef_chat_bad_requests():
    user = User.objects.create_user(username="chefbadreq", password="password")
    Pantry.objects.get_or_create(user=user)

    client = Client()
    client.force_login(user)

    blank_res = client.post(
        reverse("core:ai_chef_chat"),
        data=json.dumps({"action": "message", "message": "   "}),
        content_type="application/json",
    )
    assert blank_res.status_code == 400

    bad_json_res = client.post(
        reverse("core:ai_chef_chat"),
        data="{not-json",
        content_type="application/json",
    )
    assert bad_json_res.status_code == 400
    assert bad_json_res.json()["reply"] == FALLBACK_MESSAGE_1