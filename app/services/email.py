from fastapi import BackgroundTasks
from app.common.settings import get_settings
from app.models.user import User
from app.common.email import send_email
from app.utils.email_context import USER_VERIFY_ACCOUNT, FORGOT_PASSWORD, USER_DELETE_ACCOUNT
from app.common.security import hash_password

settings = get_settings()

async def send_admin_new_user_email(user: User, background_tasks: BackgroundTasks):
    data = {
        'app_name': settings.APP_NAME,
        "name": user.name,
        "email": user.email,
    }
    subject = f"Nuevo usuario registrado | Ilexia"
    await send_email(
        recipients=["soporte@iadevinvestiments.com"],
        subject=subject,
        template_name="user/admin-new-user.html",
        context=data,
        background_tasks=background_tasks
    )

async def send_account_verification_email(user: User, background_tasks: BackgroundTasks):
    string_context = user.get_context_string(context=USER_VERIFY_ACCOUNT)
    token = hash_password(string_context)
    activate_url = f"{settings.FRONTEND_HOST}/auth/account-verify?token={token}&email={user.email}"
    data = {
        'app_name': settings.APP_NAME,
        "name": user.name,
        'activate_url': activate_url,
        'site_url': 'https://ilexia.ai/'
    }
    subject = f"Welcome, I’m {settings.APP_NAME} | Ilexia"
    await send_email(
        recipients=[user.email],
        subject=subject,
        template_name="user/account-verification.html",
        context=data,
        background_tasks=background_tasks
    )

async def send_delete_verification_email(user: User, background_tasks: BackgroundTasks):
    string_context = user.get_context_string(context= USER_DELETE_ACCOUNT)
    token = hash_password(string_context)
    delete_url = f"{settings.FRONTEND_HOST}/auth/delete-verify?token={token}&email={user.email}"
    data = {
        'app_name': settings.APP_NAME,
        "name": user.name,
        'delete_url': delete_url,
        'site_url': 'https://ilexia.ai/'
    }
    subject = f"Ilexia - Account Deletion Request"
    await send_email(
        recipients=[user.email],
        subject=subject,
        template_name="user/delete-verification.html",
        context=data,
        background_tasks=background_tasks
    )
    
async def send_account_activation_confirmation_email(user: User, background_tasks: BackgroundTasks):
    data = {
        'app_name': settings.APP_NAME,
        "name": user.name,
        'login_url': f'{settings.FRONTEND_HOST}'
    }
    subject = f"Welcome, I’m {settings.APP_NAME} | Ilexia"
    await send_email(
        recipients=[user.email],
        subject=subject,
        template_name="user/account-verification-confirmation.html",
        context=data,
        background_tasks=background_tasks
    )
    
async def send_password_reset_email(user: User, background_tasks: BackgroundTasks):
    string_context = user.get_context_string(context=FORGOT_PASSWORD)
    token = hash_password(string_context)
    reset_url = f"{settings.FRONTEND_HOST}/auth/reset-password?token={token}&email={user.email}"
    data = {
        'app_name': settings.APP_NAME,
        "name": user.name,
        'activate_url': reset_url,
    }
    subject = f"Reset Password - {settings.APP_NAME}"
    await send_email(
        recipients=[user.email],
        subject=subject,
        template_name="user/password-reset.html",
        context=data,
        background_tasks=background_tasks
    )

async def send_subscription_cancellation_email(user: User, background_tasks: BackgroundTasks):
    data = {
        "name": user.name,
    }
    subject = f"Cancellation Confirmation | Ilexia"
    await send_email(
        recipients=[user.email],
        subject=subject,
        template_name="user/subscription-cancellation.html",
        context=data,
        background_tasks=background_tasks
    )