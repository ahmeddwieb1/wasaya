from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    # Application
    app_name: str = "Wasaya"
    app_env: str = "development"
    secret_key: str
    frontend_base_url: str = "http://localhost:3000"
    backend_base_url: str = "http://localhost:8000"

    # Database
    database_url: str

    # JWT
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440

    # Cookie
    cookie_secure: bool = False
    cookie_samesite: str = "lax"

    # SMTP
    # smtp_host: str
    # smtp_port: int = 587
    # smtp_username: str
    # smtp_password: str
    # smtp_from_email: str
    # smtp_from_name: str = "Wasaya"
    # -----------------------------------
    # Email settings for development
    smtp_host: str = "localhost"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_use_tls: bool = True
    smtp_from_name: str = "Wasaya"
    smtp_from_email: str = "noreply@wasaya.local"

    class Config:
        env_file = BASE_DIR / ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()