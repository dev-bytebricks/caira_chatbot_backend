import logging
from fastapi_mail import FastMail, MessageSchema, MessageType, ConnectionConfig
from fastapi.background import BackgroundTasks
from app.common.settings import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

config = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    MAIL_DEBUG=settings.MAIL_DEBUG,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    TEMPLATE_FOLDER=settings.MAIL_TEMPLATE_FOLDER,
    USE_CREDENTIALS=settings.MAIL_USE_CREDENTIALS,
)

fm = FastMail(config)

async def send_email(recipients: list, subject: str, context: dict, template_name: str,
                     background_tasks: BackgroundTasks):
    message = MessageSchema(
        subject=subject,
        recipients=recipients,
        template_body=context,
        subtype=MessageType.html
    )
    background_tasks.add_task(fm.send_message, message, template_name=template_name)