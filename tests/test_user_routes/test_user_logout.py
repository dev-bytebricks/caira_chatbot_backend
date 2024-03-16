"""
1. Only authenticated user should be able to logout
2. A request with invalid token should not be entertained.
/users/logout
"""

from tests.conftest import USER_PASSWORD

def test_user_logout(client, user):
    data = client.post('/auth/token', data={'username': user.email, 'password': USER_PASSWORD})
    headers = {
        "Authorization": f"Bearer {data.json()['access_token']}"
    }
    response = client.get("/users/logout", headers=headers)
    assert response.status_code == 200
    
def test_user_logout_invalid_access_token(client, user):
    data = client.post('/auth/token', data={'username': user.email, 'password': USER_PASSWORD})
    headers = {
        "Authorization": f"Bearer {data.json()['access_token'][:-6]}sakd2r"
    }
    response = client.get("/users/logout", headers=headers)
    assert response.status_code == 401

def test_user_logout_old_refresh_token_does_not_works(client, user):
    data = client.post('/auth/token', data={'username': user.email, 'password': USER_PASSWORD})
    headers = {
        "Authorization": f"Bearer {data.json()['access_token']}"
    }
    response = client.get("/users/logout", headers=headers)
    
    header = {
        "refresh-token": data.json()['refresh_token']
    }
    response = client.post("/auth/refresh", json={}, headers=header)
    assert 'access_token' not in response.json()
    assert 'refresh_token' not in response.json()
    assert response.status_code == 400