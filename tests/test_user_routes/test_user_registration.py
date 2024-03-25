from app.models.user import Role
from tests.conftest import USER_NAME, USER_EMAIL, USER_PASSWORD

def test_create_user(client):
    data = {
        "name": USER_NAME,
        "email": USER_EMAIL,
        "password": USER_PASSWORD,
        "role": Role.User.value
    }
    response = client.post('/users/register', json=data)
    assert response.status_code == 201
    assert "password" not in response.json()
    

def test_create_user_with_existing_email(client, inactive_user):
    data = {
        "name": USER_NAME,
        "email": inactive_user.email,
        "password": USER_PASSWORD,
        "role": Role.User.value
    }
    response = client.post("/users/register", json=data)
    assert response.status_code != 201


def test_create_user_with_invalid_email(client):
    data = {
        "name": USER_NAME,
        "email": "wrongemail.com",
        "password": USER_PASSWORD,
        "role": Role.User.value
    }
    response = client.post("/users/register", json=data)
    assert response.status_code != 201


def test_create_user_with_empty_password(client):
    data = {
        "name": USER_NAME,
        "email": USER_EMAIL,
        "password": "",
        "role": Role.User.value
    }
    response = client.post("/users/register", json=data)
    assert response.status_code != 201


def test_create_user_with_numeric_password(client):
    data = {
        "name": USER_NAME,
        "email": USER_EMAIL,
        "password": "1232382318763",
        "role": Role.User.value
    }
    response = client.post("/users/register", json=data)
    assert response.status_code != 201


def test_create_user_with_char_password(client):
    data = {
        "name": USER_NAME,
        "email": USER_EMAIL,
        "password": "charpassword",
        "role": Role.User.value
    }
    response = client.post("/users/register", json=data)
    assert response.status_code != 201


def test_create_user_with_alphanumeric_password(client):
    data = {
        "name": USER_NAME,
        "email": USER_EMAIL,
        "password": "alphanum3ricpassw0rd",
        "role": Role.User.value
    }
    response = client.post("/users/register", json=data)
    assert response.status_code != 201