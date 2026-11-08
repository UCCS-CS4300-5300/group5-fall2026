import pytest
from django.contrib.auth.models import User
from django.urls import reverse


@pytest.mark.django_db
def test_login_page_renders(client):
    response = client.get(reverse("login"))

    assert response.status_code == 200
    assert b"Log in" in response.content
    assert b"Create an account" in response.content


@pytest.mark.django_db
def test_user_can_log_in_with_valid_credentials(client):
    User.objects.create_user(username="testuser", password="StrongPass123!")

    response = client.post(reverse("login"), {
        "username": "testuser",
        "password": "StrongPass123!",
    })

    assert response.status_code == 302
    assert response.url == reverse("core:home")
    assert int(client.session["_auth_user_id"]) == User.objects.get(username="testuser").id


@pytest.mark.django_db
def test_login_rejects_invalid_password(client):
    User.objects.create_user(username="testuser", password="StrongPass123!")

    response = client.post(reverse("login"), {
        "username": "testuser",
        "password": "wrong-password",
    })

    assert response.status_code == 200
    assert "Please enter a correct username and password" in response.content.decode()
    assert "_auth_user_id" not in client.session


@pytest.mark.django_db
def test_login_redirects_to_requested_protected_page(client):
    user = User.objects.create_user(username="testuser", password="StrongPass123!")

    response = client.get(reverse("core:home"))
    login_url = response.url

    assert login_url.startswith(reverse("login") + "?next=")

    response = client.post(login_url, {
        "username": user.username,
        "password": "StrongPass123!",
        "next": reverse("core:home"),
    })

    assert response.status_code == 302
    assert response.url == reverse("core:home")


@pytest.mark.django_db
def test_signup_creates_authenticated_user(client):
    response = client.post(reverse("core:signup"), {
        "username": "newuser",
        "password1": "StrongPass123!",
        "password2": "StrongPass123!",
    })

    assert response.status_code == 302
    assert response.url == reverse("core:home")
    assert User.objects.filter(username="newuser").exists()
    assert client.session["_auth_user_id"] == str(User.objects.get(username="newuser").id)


@pytest.mark.django_db
def test_logout_logs_user_out(client):
    user = User.objects.create_user(username="testuser", password="StrongPass123!")
    client.force_login(user)

    response = client.post(reverse("logout"))

    assert response.status_code == 302
    assert response.url == reverse("login")
    assert "_auth_user_id" not in client.session
