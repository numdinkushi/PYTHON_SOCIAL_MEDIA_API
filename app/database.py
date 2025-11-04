# database.py
import re
from urllib.parse import quote_plus
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings


# ------------------------------------------------------------------
# 1. Build the bullet-proof DATABASE URL
# ------------------------------------------------------------------
def build_database_url():
    # Prefer explicit DATABASE_URL (e.g. from Render env var)
    if settings.database_url:
        url = settings.database_url
    else:
        # Build from individual vars (fallback)
        pwd = quote_plus(settings.database_password)  # URL-encode password
        url = (
            f"postgresql+psycopg2://"
            f"{settings.database_user}:{pwd}@"
            f"{settings.database_host}:{settings.database_port}/"
            f"{settings.database_name}"
        )

    # ------------------------------------------------------------------
    # 2. Force SSL for Render (free tier ONLY accepts sslmode=require)
    # ------------------------------------------------------------------
    if "render.com" in url.lower():
        # Convert postgresql:// to postgresql+psycopg2:// for Render
        if url.startswith("postgresql://") and not url.startswith("postgresql+psycopg2://"):
            url = url.replace("postgresql://", "postgresql+psycopg2://", 1)

        # Strip any existing sslmode
        url = re.sub(r"[?&]sslmode=[^&]*", "", url).rstrip("?&")

        # Append exactly once
        separator = "&" if "?" in url else "?"
        url += f"{separator}sslmode=require"

    return url


SQLALCHEMY_DATABASE_URL = build_database_url()


# ------------------------------------------------------------------
# 3. TCP keep-alives (survive Render’s 15-min sleep)
# ------------------------------------------------------------------
connect_args = {}
if "render.com" in SQLALCHEMY_DATABASE_URL.lower():
    connect_args = {
        "keepalives": 1,
        "keepalives_idle": 30,      # seconds
        "keepalives_interval": 10,
        "keepalives_count": 5,
    }


# ------------------------------------------------------------------
# 4. Create the engine — production-grade
# ------------------------------------------------------------------
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,      # Detect dead connections instantly
    pool_recycle=300,        # Refresh every 5 min
    pool_size=5,
    max_overflow=10,
    echo=False,              # Set True only for local debugging
)


# ------------------------------------------------------------------
# 5. Session & Base
# ------------------------------------------------------------------
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ------------------------------------------------------------------
# 6. Dependency for FastAPI routes
# ------------------------------------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
