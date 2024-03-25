from fastapi import FastAPI
from .common import settings
from app.routes import auth, user, user_chat, user_document, admin

def create_application():
    application = FastAPI()
    application.include_router(user.user_router)
    application.include_router(user.user_router_protected)
    application.include_router(user_chat.user_chat_router_protected)
    application.include_router(user_document.user_document_router_protected)
    application.include_router(auth.auth_router)
    application.include_router(admin.admin_router_protected)
    return application

app = create_application()

@app.get("/")
async def root():
    mysettings = settings.get_settings()
    return {"message": "Hi, I am Bytebricks. Awesome - Your setup is done & working." + f" {mysettings.DATABASE_URI}"}