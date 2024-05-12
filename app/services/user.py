from datetime import datetime, timezone
import logging
import uuid
from fastapi import HTTPException, status
from app.common.security import delete_refresh_tokens_from_db, get_user_from_db, hash_password, is_password_strong_enough, verify_password
from app.common import getzep, azurecloud
from app.models.user import AdminConfig, User, Role
from app.services import email
from app.utils.email_context import FORGOT_PASSWORD, USER_VERIFY_ACCOUNT

logger = logging.getLogger(__name__)

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
        raise HTTPException(status_code=400, detail="Email already exists.")

    if not is_password_strong_enough(data.password):
        raise HTTPException(status_code=400, detail="Please provide a strong password.")

    # raise http exception if user is already registered in zep
    await _check_user_in_zep(data.email)

    user = User()
    user.name = data.name
    user.email = data.email
    user.password = hash_password(data.password)
    user.role = data.role
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
        logger.exception(verify_exec)
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

    await _add_user_to_zep(user)

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
        logger.exception(verify_exec)
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

async def _check_user_in_zep(user_id):
    if await getzep.check_user_exists(user_id):
        logger.error("User with this email already exists in Zep.")
        raise HTTPException(status_code=400, detail="User with this email already exists in Zep.")

    if len(await getzep.get_all_sessions_of_user(user_id)) > 0:
        logger.error(f'Zep session already registered for user')
        raise HTTPException(status_code=400, detail="Zep session already registered for user.")
    
async def _add_user_to_zep(user):
    if not await getzep.check_user_exists(user.email):
        await getzep.add_new_user(user.email, "emailid", user.name)
    else:
        logger.error("User with this email already exists in Zep.")
        raise HTTPException(status_code=400, detail="User with this email already exists in Zep.")

    user_all_sessions = await getzep.get_all_sessions_of_user(user.email)
    if len(user_all_sessions) == 0:
        await getzep.add_session(user_id=user.email, sessionid=uuid.uuid4().hex)
        user_all_sessions = await getzep.get_all_sessions_of_user(user.email)
    else:
        logger.error(f'Zep session already registered for user, session: {user_all_sessions}')
        raise HTTPException(status_code=400, detail="Zep session already registered for user.")
    
async def fetch_app_info(session):
    admin_config = session.query(AdminConfig).first()
    if admin_config is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="App info not found in database.")
    return admin_config

async def generate_pubsub_client_token(user: User):
    if user.role == Role.Admin:
        token = await azurecloud.get_pubsub_client_token_admin(user.email)
    else:
        token = await azurecloud.get_pubsub_client_token(user.email)
    return {"token": token}