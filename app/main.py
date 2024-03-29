import logging
from fastapi import FastAPI
from .common import settings
from app.routes import auth, user, user_chat, user_document, admin_config, admin_knowledge_base

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(name)s - %(funcName)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

def create_application():
    application = FastAPI()
    application.include_router(user.user_router)
    application.include_router(user.user_router_protected)
    application.include_router(user_chat.user_chat_router_protected)
    application.include_router(user_document.user_document_router_protected)
    application.include_router(auth.auth_router)
    application.include_router(admin_config.admin_config_router_protected)
    application.include_router(admin_knowledge_base.admin_knowledge_base_router_protected)
    return application

app = create_application()

@app.get("/")
async def root():
    mysettings = settings.get_settings()
    return {"message": "Caira V2 is live."}