from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status
from app.common.security import get_user_from_db, upsert_refresh_token_in_db, validate_refresh_token, verify_password, create_access_token, create_refresh_token
from app.common.settings import get_settings
from app.models.user import User

settings = get_settings()

def _verify_user(user: User):
    # Verify the email
    # Verify that user account is verified
    # Verify user account is active
    
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, 
                            detail="Email is not registered with us.",
                            headers={"WWW-Authenticate": "Bearer"})
    
    if not user.verified_at:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Your account is not verified. Please check your email inbox to verify your account.",
                            headers={"WWW-Authenticate": "Bearer"})
    
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, 
                            detail="Your account has been dactivated. Please contact support.",
                            headers={"WWW-Authenticate": "Bearer"})

async def get_login_tokens(form_data, session):
    # Authenticate User
    # Generate access_token and refresh_token and ttl
    
    user = await get_user_from_db(form_data.username, session)
    _verify_user(user)

    if not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, 
                            detail="Incorrect email or password.",
                            headers={"WWW-Authenticate": "Bearer"})
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)
    
    refresh_token_expires = timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
    refresh_token = create_refresh_token(data={"sub": user.email}, expires_delta=refresh_token_expires)
    
    await upsert_refresh_token_in_db(refresh_token, refresh_token_expires, user.email, session)

    return {"access_token": access_token, "refresh_token": refresh_token, "expires_at": datetime.now(timezone.utc) + access_token_expires}

async def get_new_access_token(refresh_token, session):
    # Validate refresh token
    # Generate new access_token

    try:
        username = await validate_refresh_token(refresh_token, session)
    except:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Refresh token is not valid. Please login again.")
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": username}, expires_delta=access_token_expires)

    return {"access_token": access_token, "refresh_token": refresh_token, "expires_at": datetime.now(timezone.utc) + access_token_expires}