"""
1. User shoud be able to generate the login token with valid refresh token.
2. User should not be able to generate login token with invalid refresh token.
.....
"""

from tests.conftest import USER_PASSWORD

# Refresh token doesnt works after expiry

def test_refresh_token(client, user):
    data = client.post('/auth/token', data={'username': user.email, 'password': USER_PASSWORD})
    header = {
        "refresh-token": data.json()['refresh_token']
    }
    response = client.post("/auth/refresh", json={}, headers=header)
    assert response.status_code == 200
    assert 'access_token' in response.json()
    assert 'refresh_token' in response.json()
    
def test_refresh_token_with_invalid_token(client):
    header = {
        "refresh-token": 'myrefreshtoken'
    }
    response = client.post("/auth/refresh", json={}, headers=header)
    assert response.status_code == 400
    assert 'access_token' not in response.json()
    assert 'refresh_token' not in response.json()