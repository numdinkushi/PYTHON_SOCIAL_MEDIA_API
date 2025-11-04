
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings

if settings.database_url:
    SQLALCHEMY_DATABASE_URL = settings.database_url
else:
    SQLALCHEMY_DATABASE_URL = f"postgresql://{settings.database_user}:{settings.database_password}@{settings.database_host}:{settings.database_port}/{settings.database_name}"

# Add SSL mode for Render PostgreSQL connections
# Use postgresql+psycopg2:// scheme and append ?sslmode=require for Render databases
connect_args = {}
if "render.com" in SQLALCHEMY_DATABASE_URL:
    # Force use of psycopg2-binary for Render databases
    if SQLALCHEMY_DATABASE_URL.startswith("postgresql://"):
        SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace(
            "postgresql://", "postgresql+psycopg2://", 1)
    # Append SSL mode to connection string
    if "sslmode" not in SQLALCHEMY_DATABASE_URL:
        separator = "&" if "?" in SQLALCHEMY_DATABASE_URL else "?"
        SQLALCHEMY_DATABASE_URL = f"{SQLALCHEMY_DATABASE_URL}{separator}sslmode=require"

# Enable pool_pre_ping to handle stale connections
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
