import pytest
from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse
from core.models import GlobalCatalogItem, Pantry, PantryItem

# We need to test that the collapsible container is there in the page
# as well as the trigger buttons, arrow indicator (menu), and the
# other panels (submenus)
@pytest.mark.django_db
def test_collapsible_menu_structure_and_triggers():
    user = User.objects.create_user(username="menuuser", password="password")
    client = Client()
    client.force_login(user)

    response = client.get(reverse('core:home'))
    assert response.status_code == 200
    content = response.content.decode('utf-8')

    # Sidebar elements & dropdown toggle button
    assert 'id="side-container"' in content
    assert 'id="menu-dropdown-toggle"' in content
    assert 'class="menu-arrow"' in content

    # Sidebar views & feature panels
    assert 'id="sidebar-main-menu"' in content
    assert 'data-target="panel-pantry"' in content
    assert 'data-target="panel-ai"' in content
    assert 'data-target="panel-manual"' in content
    assert 'id="panel-pantry"' in content
    assert 'id="panel-ai"' in content
    assert 'id="panel-manual"' in content

# We need to test that when the user triggers a query, the sidebar
# remains open as to allow for more queries without going back to main menu
@pytest.mark.django_db
def test_collapsible_menu_search_query_integration():
    user = User.objects.create_user(username="searchuser", password="password")
    client = Client()
    client.force_login(user)

    response = client.get(reverse('core:home') + '?q=Milk')
    assert response.status_code == 200
    content = response.content.decode('utf-8')

    # Verify search input value populated & search panel context rendered
    assert 'value="Milk"' in content
    assert 'id="search-form"' in content