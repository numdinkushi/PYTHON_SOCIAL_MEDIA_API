
import re

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings

if settings.database_url:
    SQLALCHEMY_DATABASE_URL = settings.database_url
else:
    SQLALCHEMY_DATABASE_URL = f"postgresql://{settings.database_user}:{settings.database_password}@{settings.database_host}:{settings.database_port}/{settings.database_name}"

# Add SSL mode for Render PostgreSQL connections
# Force use of psycopg2-binary and configure SSL via connect_args
connect_args = {}
if "render.com" in SQLALCHEMY_DATABASE_URL:
    # Force use of psycopg2-binary for Render databases
    if SQLALCHEMY_DATABASE_URL.startswith("postgresql://"):
        SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace(
            "postgresql://", "postgresql+psycopg2://", 1)
    # Remove any existing sslmode from URL (we'll use connect_args)
    if "sslmode" in SQLALCHEMY_DATABASE_URL:
        SQLALCHEMY_DATABASE_URL = re.sub(
            r'[?&]sslmode=[^&]*', '', SQLALCHEMY_DATABASE_URL)
        SQLALCHEMY_DATABASE_URL = re.sub(r'\?+', '?', SQLALCHEMY_DATABASE_URL)
        SQLALCHEMY_DATABASE_URL = re.sub(r'&+', '&', SQLALCHEMY_DATABASE_URL)
        SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.rstrip('?&')
    # Use connect_args for SSL configuration (required for psycopg2-binary)
    connect_args = {
        "sslmode": "require",
        "keepalives": 1,
        "keepalives_idle": 60,
        "keepalives_interval": 10,
        "keepalives_count": 10
    }

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
