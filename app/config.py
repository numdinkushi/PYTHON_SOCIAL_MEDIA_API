from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    database_url: Optional[str] = None
    database_host: str = "localhost"
    database_port: str = "5432"
    database_password: str = ""
    database_name: str = "fastapi_sm"
    database_user: str = "postgres"
    secret_key: str = "your-secret-key-here"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    class Config:
        env_file = ".env"


settings = Settings()
