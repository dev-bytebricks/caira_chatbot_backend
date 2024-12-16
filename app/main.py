from fastapi import FastAPI
from .common import logging_config

logging_config.setup_logging()

from app.routes import auth, user, user_chat, user_document, admin_config, admin_knowledge_base, payment, stripe
from app.common.settings import get_settings
from fastapi.middleware.cors import CORSMiddleware
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

settings = get_settings()

# List of allowed origins (i.e., the frontend URLs that you want to allow to connect to your API)
origins = [
    "http://localhost:3000",  # Adjust the port if your React app runs on a different port
    settings.FRONTEND_HOST,  # The default port for FastAPI, if you want to allow it
    "*" # Add any other origins you want to allow
]
def create_application():
    application = FastAPI() # Disable docs for production  #openapi_url="", docs_url=None, redoc_url=None
    application.include_router(user.user_router)
    application.include_router(payment.payments_router_protected)
    application.include_router(stripe.stripe_router)
    application.include_router(user.user_router_protected)
    application.include_router(user_chat.user_chat_router_protected)
    application.include_router(user_document.user_document_router_protected)
    application.include_router(auth.auth_router)
    application.include_router(admin_config.admin_config_router_protected)
    application.include_router(admin_knowledge_base.admin_knowledge_base_router_protected)
    return application

app = create_application()

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allows specified origins to make requests
    allow_credentials=True,  # Allows cookies to be included in cross-origin HTTP requests
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

@app.get("/")
async def root():
    return {"message": "Caira V2 is live"}

FastAPIInstrumentor.instrument_app(app)