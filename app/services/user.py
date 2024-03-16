from datetime import datetime, timezone
import logging
from fastapi import HTTPException, status
from app.common.security import delete_refresh_tokens_from_db, get_user_from_db, hash_password, is_password_strong_enough, verify_password
from app.models.user import User
from app.services import email
from app.utils.email_context import FORGOT_PASSWORD, USER_VERIFY_ACCOUNT

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

async def create_user_account(data, session, background_tasks):

    user_exist = session.query(User).filter(User.email == data.email).first()

    if user_exist:
        raise HTTPException(status_code=400, detail="Email is already exists.")

    if not is_password_strong_enough(data.password):
        raise HTTPException(status_code=400, detail="Please provide a strong password.")

    user = User()
    user.name = data.name
    user.email = data.email
    user.password = hash_password(data.password)
    user.is_active = False
    user.updated_at = datetime.now(timezone.utc)
    session.add(user)
    session.commit()
    session.refresh(user)

    # Account Verification Email
    await email.send_account_verification_email(user, background_tasks=background_tasks)
    return user

async def activate_user_account(data, session, background_tasks):
    
    user = session.query(User).filter(User.email == data.email).first()

    # check if user has registered
    if not user:
        raise HTTPException(status_code=400, detail="This link is not valid.")
    
    # form user token
    user_token = user.get_context_string(context=USER_VERIFY_ACCOUNT)

    # compare tokens (checks if token points to the intended account)
    try:
        token_valid = verify_password(user_token, data.token)
    except Exception as verify_exec:
        logging.exception(verify_exec)
        token_valid = False
    if not token_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                            detail="This link either expired or not valid.")
    
    user.is_active = True
    user.updated_at = datetime.now(timezone.utc)
    user.verified_at = datetime.now(timezone.utc)
    session.add(user)
    session.commit()
    session.refresh(user)

    # Activation Confirmation Email
    await email.send_account_activation_confirmation_email(user, background_tasks)

async def email_forgot_password_link(data, session, background_tasks):
    user = await get_user_from_db(data.email, session)
    
    _verify_user(user)
    
    await email.send_password_reset_email(user, background_tasks)

async def reset_user_password(data, session):
    user = await get_user_from_db(data.email, session)
    
    _verify_user(user)
    
    # form user token
    user_token = user.get_context_string(context=FORGOT_PASSWORD)
    
    # compare tokens (checks if token points to the intended account)
    try:
        token_valid = verify_password(user_token, data.token)
    except Exception as verify_exec:
        logging.exception(verify_exec)
        token_valid = False
    if not token_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                            detail="Invalid window.")
    
    user.password = hash_password(data.password)
    user.updated_at = datetime.now(timezone.utc)
    session.add(user)
    session.commit()

async def logout_user(username, session):
    await delete_refresh_tokens_from_db(username, session)