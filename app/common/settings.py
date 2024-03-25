from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from urllib.parse import quote_plus
from dotenv import find_dotenv, load_dotenv

load_dotenv(override=True)

class Settings(BaseSettings):

    # App
    APP_NAME: str
    DEBUG: bool

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

    # Azure Storage Config
    AZURE_STORAGE_ACCOUNT_KEY: str
    AZURE_STORAGE_ACCOUNT_NAME: str
    AZURE_STORAGE_CONTAINER_NAME: str
    AZURE_STORAGE_CONNECTION_STRING: str

    # OpenAI Config
    OPENAI_API_KEY: str

    # Pinecone Config
    PINECONE_API_KEY: str
    PINECONE_ENV: str
    PINECONE_CONSUMER_INDEX: str
    PINECONE_KNOWLEDGE_BASE_INDEX: str

    # ZEP Config
    ZEP_API_URL: str

    # Pydantic Settings
    model_config = SettingsConfigDict(extra= "ignore", env_file= find_dotenv(".env"), case_sensitive=True)

@lru_cache()
def get_settings() -> Settings:
    return Settings()
