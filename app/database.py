
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings

if settings.database_url:
    SQLALCHEMY_DATABASE_URL = settings.database_url
else:
    SQLALCHEMY_DATABASE_URL = f"postgresql://{settings.database_user}:{settings.database_password}@{settings.database_host}:{settings.database_port}/{settings.database_name}"

# Add SSL mode for Render PostgreSQL connections
# Append ?sslmode=require if connecting to Render database
if "render.com" in SQLALCHEMY_DATABASE_URL and "sslmode" not in SQLALCHEMY_DATABASE_URL:
    separator = "&" if "?" in SQLALCHEMY_DATABASE_URL else "?"
    SQLALCHEMY_DATABASE_URL = f"{SQLALCHEMY_DATABASE_URL}{separator}sslmode=require"

engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
