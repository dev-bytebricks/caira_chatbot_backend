from datetime import datetime, timedelta, timezone
import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from app.common.database import get_session
from app.common.settings import get_settings
from jose import JWTError, jwt
from app.models.user import User, UserToken, Role
from sqlalchemy.orm import Session, joinedload

logger = logging.getLogger(__name__)

SPECIAL_CHARACTERS = ['-', '!', '@', '#', '$', '%', '=', ':', '?', '.', '/', '|', '~', '>']

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

settings = get_settings()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    try:
        if not isinstance(plain_password, str) or not isinstance(hashed_password, str):
            raise ValueError("Password and token must be strings")
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        print(f"Error in verify_password: {e}")
        return False
    
def is_password_strong_enough(password: str) -> bool:
    if len(password) < 8:
        return False

    if not any(char.isupper() for char in password):
        return False

    if not any(char.islower() for char in password):
        return False

    if not any(char.isdigit() for char in password):
        return False

    if not any(char in SPECIAL_CHARACTERS for char in password):
        return False

    return True

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_ACCESS_SECRET, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=7)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_REFRESH_SECRET, algorithm=settings.ALGORITHM)
    return encoded_jwt

async def upsert_refresh_token_in_db(refresh_token, expires_delta: timedelta, user_id: str, session: Session):
    
    # Delete any previous refresh tokens
    await delete_refresh_tokens_from_db(user_id, session)

    user_token = UserToken()
    user_token.user_id = user_id
    user_token.refresh_token = refresh_token
    user_token.expires_at = datetime.now(timezone.utc) + expires_delta
    session.add(user_token)
    session.commit()

async def delete_refresh_tokens_from_db(user_id, session: Session):
    refresh_tokens_db = session.query(UserToken).options(joinedload(UserToken.user))\
        .filter(UserToken.user_id == user_id).all()
    
    for refresh_token_db in refresh_tokens_db:
        session.delete(refresh_token_db)
    
    session.commit()


async def validate_access_token(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Access token is not valid",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_ACCESS_SECRET, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        return username
    except JWTError:
        raise credentials_exception

async def validate_refresh_token(refresh_token: str, session: Session):
    payload = jwt.decode(refresh_token, settings.JWT_REFRESH_SECRET, algorithms=[settings.ALGORITHM])
    username: str = payload.get("sub")
    if username is None:
        raise Exception("Refresh token is not valid")
    
    refresh_token_db = session.query(UserToken).options(joinedload(UserToken.user)).\
        filter(UserToken.refresh_token == refresh_token,
               UserToken.user_id == username,
               UserToken.expires_at > datetime.now(timezone.utc)).first()
    if refresh_token_db is None:
        raise Exception("Refresh token is not valid")

    return username

async def get_current_user(username: str = Depends(validate_access_token), session: Session = Depends(get_session)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    user = await get_user_from_db(username, session)
    if user is None:
        raise credentials_exception
    return user

async def is_admin(username: str = Depends(validate_access_token), session: Session = Depends(get_session)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Unauthorized Access",
        headers={"WWW-Authenticate": "Bearer"},
    )
    user = await get_user_from_db(username, session)
    if user is None:
        raise credentials_exception
    else:
        if user.role != Role.Admin:
            raise credentials_exception

async def get_user_from_db(email: str, session: Session):
    try:
        user = session.query(User).filter(User.email == email).first()
    except Exception as user_exec:
        logger.exception(f"User Not Found, Email: {email} | Database Exception: {user_exec}")
        user = None
    return user
    
