"""
1. User should be able to login
2. User should not be able to login with incorrect password
3. Inactive user should not be able to login.
4. Unverified user should not be able to login.
.....
"""

from tests.conftest import USER_PASSWORD

def test_user_login(client, user):
    data = {'username': user.email, 'password': USER_PASSWORD}
    response = client.post('/auth/token', data=data)
    assert response.status_code == 200
    assert response.json()['access_token'] is not None
    assert response.json()['refresh_token'] is not None
    assert response.json()['expires_at'] is not None


def test_user_login_wrong_password(client, user):
    response = client.post('/auth/token', data={'username': user.email, 'password': 'wrong_password'})
    assert response.status_code == 401
    assert response.json()['detail'] == 'Incorrect email or password.'


def test_user_login_wrong_email(client):
    response = client.post('/auth/token', data={'username': 'abc@describly.com', 'password': USER_PASSWORD})
    assert response.status_code == 401


def test_user_login_inactive_account(client, inactive_user):
    response = client.post('/auth/token', data={'username': inactive_user.email, 'password': USER_PASSWORD})
    assert response.status_code == 401


def test_user_login_unverified(client, unverified_user):
    response = client.post('/auth/token', data={'username': unverified_user.email, 'password': USER_PASSWORD})
    assert response.status_code == 401