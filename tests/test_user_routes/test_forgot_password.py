"""
1. User should be able to send forgot password request
2. User should not be able to send forgot password request with invalid email address
3. Unverified should not be able to request forgot password email
4. Inactive user should not be able to request forgot password email
"""

def test_user_can_send_forgot_password_request(client, user):
    data = {'email': user.email}
    response = client.post('/users/forgot-password', json=data)
    print(response.json())
    assert response.status_code == 200


def test_user_can_not_send_forgot_password_request_with_invalid_email(client):
    data = {'email': 'invalid_email'}
    response = client.post('/users/forgot-password', json=data)
    assert response.status_code == 422


def test_unverified_user_can_not_send_forgot_password_request(client, unverified_user):
    data = {'email': unverified_user.email}
    response = client.post('/users/forgot-password', json=data)
    assert response.status_code == 401


def test_in_active_user_can_not_send_forgot_password_request(client, inactive_user):
    data = {'email': inactive_user.email}
    response = client.post('/users/forgot-password', json=data)
    assert response.status_code == 401