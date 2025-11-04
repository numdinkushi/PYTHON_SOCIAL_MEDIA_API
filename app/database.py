import re
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings

# Step 1: Build base connection string
if settings.database_url:
    SQLALCHEMY_DATABASE_URL = settings.database_url
else:
    SQLALCHEMY_DATABASE_URL = (
        f"postgresql+psycopg2://{settings.database_user}:{settings.database_password}"
        f"@{settings.database_host}:{settings.database_port}/{settings.database_name}"
    )

# Step 2: Force SSL for Render PostgreSQL
connect_args = {}

if "render.com" in SQLALCHEMY_DATABASE_URL:
    # Remove duplicate sslmode if present
    SQLALCHEMY_DATABASE_URL = re.sub(r"[?&]sslmode=[^&]*", "", SQLALCHEMY_DATABASE_URL)
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.rstrip("?&")

    # Explicitly append sslmode=require if not already there
    if "?" in SQLALCHEMY_DATABASE_URL:
        SQLALCHEMY_DATABASE_URL += "&sslmode=require"
    else:
        SQLALCHEMY_DATABASE_URL += "?sslmode=require"

    # Optionally tune TCP keepalive settings (recommended on Render)
    connect_args = {
        "keepalives": 1,
        "keepalives_idle": 30,
        "keepalives_interval": 10,
        "keepalives_count": 5,
    }

# Step 3: Create engine with resilience settings
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,    # Detect and refresh stale connections
    pool_recycle=300,      # Reconnect every 5 minutes
    pool_size=5,
    max_overflow=10,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
