from datetime import datetime, timezone
import sys
import os
from typing import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from starlette.testclient import TestClient

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.common.email import fm
from app.common.database import Base, get_session
from app.models.user import User, Role
from app.common.security import hash_password
from app.services.auth import get_login_tokens

USER_NAME = "Pytest"
USER_EMAIL = "pytest@email.com"
USER_PASSWORD = "TestUser@123"

engine = create_engine("sqlite:///./fastapi.db")
SessionTesting = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def test_session() -> Generator:
    session = SessionTesting()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture(scope="function")
def app_test():
    Base.metadata.create_all(bind=engine)
    yield app
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(app_test, test_session):
    def _test_db():
        try:
            yield test_session
        finally:
            pass

    app_test.dependency_overrides[get_session] = _test_db
    fm.config.SUPPRESS_SEND = 1
    return TestClient(app_test)

@pytest.fixture(scope="function")
async def auth_client(app_test, test_session, user):
    def _test_db():
        try:
            yield test_session
        finally:
            pass

    app_test.dependency_overrides[get_session] = _test_db
    fm.config.SUPPRESS_SEND = 1
    data = await get_login_tokens(user, test_session)
    client = TestClient(app_test)
    client.headers['Authorization'] = f"Bearer {data['access_token']}"
    return client

@pytest.fixture(scope="function")
def inactive_user(test_session):
    user = User()
    user.name = USER_NAME
    user.email = USER_EMAIL
    user.role = Role.User
    user.password = hash_password(USER_PASSWORD)
    user.updated_at = datetime.now(timezone.utc)
    user.is_active = False
    test_session.add(user)
    test_session.commit()
    test_session.refresh(user)
    return user

@pytest.fixture(scope="function")
def user(test_session):
    user = User()
    user.name = USER_NAME
    user.email = USER_EMAIL
    user.role = Role.User
    user.password = hash_password(USER_PASSWORD)
    user.updated_at = datetime.now(timezone.utc)
    user.verified_at = datetime.now(timezone.utc)
    user.is_active = True
    test_session.add(user)
    test_session.commit()
    test_session.refresh(user)
    return user

@pytest.fixture(scope="function")
def unverified_user(test_session):
    user = User()
    user.name = USER_NAME
    user.email = USER_EMAIL
    user.role = Role.User
    user.password = hash_password(USER_PASSWORD)
    user.updated_at = datetime.now(timezone.utc)
    user.is_active = True
    test_session.add(user)
    test_session.commit()
    test_session.refresh(user)
    return user