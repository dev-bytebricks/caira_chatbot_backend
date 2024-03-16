from fastapi import FastAPI
from .common import settings
from app.routes import user, auth

def create_application():
    application = FastAPI()
    application.include_router(user.user_router)
    application.include_router(user.user_router_protected)
    application.include_router(auth.auth_router)
    return application

app = create_application()

@app.get("/")
async def root():
    mysettings = settings.get_settings()
    return {"message": "Hi, I am Bytebricks. Awesome - Your setup is done & working." + f" {mysettings.DATABASE_URI}"}