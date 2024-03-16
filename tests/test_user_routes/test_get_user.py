"""
1. Only authenticated user should be able to fetch the user details
2. A request with invalid token should not be entertained.
/users/me
"""

from tests.conftest import USER_PASSWORD

# Access token doesnt works after expiry
# And then Access token works after refreshing

def test_fetch_me(client, user):
    data = client.post('/auth/token', data={'username': user.email, 'password': USER_PASSWORD})
    headers = {
        "Authorization": f"Bearer {data.json()['access_token']}"
    }
    response = client.get("/users/me", headers=headers)
    assert response.status_code == 200
    assert response.json()['email'] == user.email
    
def test_fetch_me_invalid_access_token(client, user):
    data = client.post('/auth/token', data={'username': user.email, 'password': USER_PASSWORD})
    headers = {
        "Authorization": f"Bearer {data.json()['access_token'][:-6]}sakd2r"
    }
    response = client.get("/users/me", headers=headers)
    assert response.status_code == 401
    assert 'email' not in response.json()
    assert 'id' not in response.json()