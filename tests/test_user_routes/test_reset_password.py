"""
1. User should be able to reset his password with combination of valid token and valid email
2. User can not reset password with invalid token
3. User can not reset password with invalid email
4. User can not reset password with any email and valid token
"""

from app.common.security import hash_password
from app.utils.email_context import FORGOT_PASSWORD

NEW_PASSWORD = "321#Bytebricks"

def _get_token(user):
    string_context = user.get_context_string(context=FORGOT_PASSWORD)
    return hash_password(string_context)

def test_reset_password(client, user):
    data = {
        "token": _get_token(user),
        "email": user.email,
        "password": NEW_PASSWORD
    }
    response = client.put("/users/reset-password", json=data)
    assert response.status_code == 200
    del data['token']
    del data['email']
    data['username'] = user.email
    login_resp = client.post("/auth/token", data=data)
    assert login_resp.status_code == 200
    
def test_reset_password_invalid_token(client, user):
    data = {
        "token": "myinvalidtoken",
        "email": user.email,
        "password": NEW_PASSWORD
    }
    response = client.put("/users/reset-password", json=data)
    assert response.status_code == 400
    del data['token']
    del data['email']
    data['username'] = user.email
    login_resp = client.post("/auth/token", data=data)
    assert login_resp.status_code != 200
    
def test_reset_password_invalid_email(client, user):
    data = {
        "token": _get_token(user),
        "email": "test@email.com",
        "password": NEW_PASSWORD
    }
    response = client.put("/users/reset-password", json=data)
    assert response.status_code == 401
    del data['token']
    del data['email']
    data['username'] = user.email
    login_resp = client.post("/auth/token", data=data)
    assert login_resp.status_code != 200