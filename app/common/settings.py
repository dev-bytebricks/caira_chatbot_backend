from functools import lru_cache
import json
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from urllib.parse import quote_plus
from dotenv import find_dotenv, load_dotenv

load_dotenv(override=True)

class Settings(BaseSettings):
    CONSUMER_FILE_CHARACTERS_LIMIT:int

    # App
    APP_NAME: str
    DEBUG: bool

    # Stripe Config
    STRIPE_PUBLIC_KEY: str
    STRIPE_SECRET_KEY: str
    STRIPE_WEBHOOK_SECRET: str

    # User Usage Limits
    FREE_PLAN_FILE_UPLOAD_LIMIT: int = 5
    FREE_PLAN_MSG_LIMIT: int
    PREMIUM_PLANS_FILE_UPLOAD_LIMIT: int = 15

    # MySQL Database Config
    MYSQL_HOST: str
    MYSQL_USER: str
    MYSQL_PASSWORD: str
    MYSQL_PORT: int
    MYSQL_DB: str
    
    @property
    def DATABASE_URI(self) -> str:
        return f"mysql+pymysql://{self.MYSQL_USER}:{quote_plus(self.MYSQL_PASSWORD)}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DB}"

    # Other Config
    FRONTEND_HOST: str

    # Token Config
    JWT_ACCESS_SECRET: str
    JWT_REFRESH_SECRET: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_MINUTES: int
    ALGORITHM: str

    # Mail Server Config
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_PORT: int
    MAIL_SERVER: str
    MAIL_STARTTLS: bool
    MAIL_SSL_TLS: bool
    MAIL_DEBUG: bool
    MAIL_FROM: str
    MAIL_FROM_NAME: str
    MAIL_USE_CREDENTIALS: bool

    @property
    def MAIL_TEMPLATE_FOLDER(self) -> str:
        return Path(__file__).parent.parent / "templates"
    
    # OpenAI Config
    OPENAI_API_KEY: str
    OPENAI_CHAT_PRIMARY_MODEL_NAME: str
    OPENAI_CHAT_SECONDARY_MODEL_NAME: str
    EMBEDDINGS_MODEL_NAME: str

    # Pinecone Config
    PINECONE_API_KEY: str
    PINECONE_CONSUMER_INDEX: str
    PINECONE_KNOWLEDGE_BASE_INDEX: str

    # ZEP Config
    ZEP_API_URL: str

    # Google Cloud Service Account JSON
    # GOOGLE_SERVICE_ACCOUNT_JSON: str
    # CONSUMER_FILE_CHARACTERS_LIMIT: int

    # @property
    # def GOOGLE_SERVICE_ACCOUNT_CREDS(self) -> str:
    #     return json.loads(self.GOOGLE_SERVICE_ACCOUNT_JSON)
    
    
    # Pydantic Settings
    model_config = SettingsConfigDict(extra= "ignore", env_file= find_dotenv(".env"), case_sensitive=True)

@lru_cache()
def get_settings() -> Settings:
    return Settings()
