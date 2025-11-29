# database.py
import re
from urllib.parse import quote_plus
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from .config import settings


# ------------------------------------------------------------------
# 1. Build the DATABASE URL with proper encoding
# ------------------------------------------------------------------
def build_database_url():
    """Build database URL with proper SSL configuration for Render."""
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

    # Force psycopg2-binary and SSL for Render
    if "render.com" in url.lower():
        # Convert postgresql:// to postgresql+psycopg2://
        if url.startswith("postgresql://") and not url.startswith("postgresql+psycopg2://"):
            url = url.replace("postgresql://", "postgresql+psycopg2://", 1)

        # Remove any existing sslmode
        url = re.sub(r"[?&]sslmode=[^&]*", "", url).rstrip("?&")

        # Use require mode for Render (Render PostgreSQL requires SSL)
        separator = "&" if "?" in url else "?"
        url += f"{separator}sslmode=require"

    return url


SQLALCHEMY_DATABASE_URL = build_database_url()


# ------------------------------------------------------------------
# 2. Connection arguments for Render PostgreSQL
# ------------------------------------------------------------------
connect_args = {}
if "render.com" in SQLALCHEMY_DATABASE_URL.lower():
    # Use connect_args for SSL (psycopg2-binary reads from here)
    # Note: sslmode in URL is also set, but connect_args takes precedence
    connect_args = {
        "sslmode": "require",        # Required for Render PostgreSQL
        "keepalives": 1,             # Enable TCP keepalives
        "keepalives_idle": 30,       # Start keepalives after 30s idle
        "keepalives_interval": 10,   # Send keepalive every 10s
        "keepalives_count": 5,       # Fail after 5 missed keepalives
        "connect_timeout": 30,       # Increased connection timeout for Render
    }


# ------------------------------------------------------------------
# 3. Create engine with robust connection pooling
# ------------------------------------------------------------------
# Configure pool settings based on environment
is_render = "render.com" in SQLALCHEMY_DATABASE_URL.lower()
pool_size = 3 if is_render else 5  # Smaller pool for Render stability
max_overflow = 5 if is_render else 10  # Fewer overflow connections for Render
# Shorter recycle for Render (2 min)
pool_recycle_time = 120 if is_render else 300

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args=connect_args,
    poolclass=QueuePool,
    pool_size=pool_size,
    max_overflow=max_overflow,
    # Verify connections before using (critical for Render)
    pool_pre_ping=True,
    # Recycle connections to prevent stale SSL connections
    pool_recycle=pool_recycle_time,
    pool_reset_on_return='commit',   # Reset connection state on return
    echo=False,                      # Set True for SQL query logging
)


# ------------------------------------------------------------------
# 4. Connection event listeners (optional, for debugging)
# ------------------------------------------------------------------
# Uncomment if you need to debug connections:
# @event.listens_for(engine, "connect")
# def receive_connect(dbapi_conn, connection_record):
#     """Log when a connection is established."""
#     print(f"Database connection established: {dbapi_conn}")


# ------------------------------------------------------------------
# 5. Session & Base
# ------------------------------------------------------------------
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ------------------------------------------------------------------
# 6. Dependency for FastAPI routes with error handling
# ------------------------------------------------------------------
def get_db():
    """Database dependency with proper error handling."""
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
