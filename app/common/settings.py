from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from urllib.parse import quote_plus
from dotenv import find_dotenv

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
        return f"mysql+pymysql://{self.MYSQL_USER}:%s@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DB}" % quote_plus(self.MYSQL_PASSWORD)

    # Other Configs
    FRONTEND_HOST: str

    # Token Configs
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

    # Pydantic Settings
    model_config = SettingsConfigDict(extra= "ignore", env_file= find_dotenv(".env"), case_sensitive=True)

@lru_cache()
def get_settings() -> Settings:
    return Settings()
