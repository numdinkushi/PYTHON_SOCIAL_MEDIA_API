# database.py
import re
import time
from urllib.parse import quote_plus
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
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

    # Detect Render PostgreSQL URLs (both internal and external)
    # Internal URLs: dpg-xxx-a (short hostname) - NOT recommended, causes SSL issues
    # External URLs: dpg-xxx-a.oregon-postgres.render.com (full domain) - RECOMMENDED
    is_render_db = re.search(r"dpg-[a-z0-9]+-[a-z]", url.lower()) is not None

    if is_render_db:
        # Convert postgres:// to postgresql:// (SQLAlchemy 2.x requirement)
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)

        # Convert postgresql:// to postgresql+psycopg2://
        if url.startswith("postgresql://") and not url.startswith("postgresql+psycopg2://"):
            url = url.replace("postgresql://", "postgresql+psycopg2://", 1)

        # Remove any existing sslmode
        url = re.sub(r"[?&]sslmode=[^&]*", "", url).rstrip("?&")

        # Always require SSL for Render PostgreSQL (recommended by Render)
        # External URLs require SSL, Internal URLs also benefit from SSL mode
        separator = "&" if "?" in url else "?"
        url += f"{separator}sslmode=require"

    return url


SQLALCHEMY_DATABASE_URL = build_database_url()


# ------------------------------------------------------------------
# 2. Connection arguments for Render PostgreSQL
# ------------------------------------------------------------------
connect_args = {}
# Detect Render PostgreSQL URLs (both internal and external)
is_render_db = re.search(r"dpg-[a-z0-9]+-[a-z]",
                         SQLALCHEMY_DATABASE_URL.lower()) is not None

if is_render_db:
    # Always use SSL for Render PostgreSQL (recommended by Render)
    # External URLs require SSL, Internal URLs benefit from it too
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
is_render = re.search(r"dpg-[a-z0-9]+-[a-z]",
                      SQLALCHEMY_DATABASE_URL.lower()) is not None
pool_size = 3 if is_render else 5  # Smaller pool for Render stability
max_overflow = 5 if is_render else 10  # Fewer overflow connections for Render
# Shorter recycle for Render (2 min)
pool_recycle_time = 120 if is_render else 300

# Create engine with retry logic for Render (handles database startup delays)


def create_engine_with_retry(url, connect_args, pool_size, max_overflow, pool_recycle_time, max_retries=10):
    """Create database engine with retry logic for Render PostgreSQL."""
    for attempt in range(max_retries):
        try:
            engine = create_engine(
                url,
                connect_args=connect_args,
                poolclass=QueuePool,
                pool_size=pool_size,
                max_overflow=max_overflow,
                # Verify connections before using (critical for Render)
                pool_pre_ping=True,
                # Recycle connections to prevent stale SSL connections
                pool_recycle=pool_recycle_time,
                pool_reset_on_return='commit',
                echo=False,
            )
            # Test the connection
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print(f"Database connected successfully on attempt {attempt + 1}")
            return engine
        except OperationalError as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                print(
                    f"Database connection attempt {attempt + 1} failed, retrying in {wait_time} seconds...")
                print(f"Error: {e}")
                time.sleep(wait_time)
            else:
                print(
                    f"Failed to connect to database after {max_retries} attempts")
                raise
    return None


# Use retry logic for Render databases
if is_render:
    engine = create_engine_with_retry(
        SQLALCHEMY_DATABASE_URL,
        connect_args,
        pool_size,
        max_overflow,
        pool_recycle_time
    )
else:
    # No retry needed for local databases
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args=connect_args,
        poolclass=QueuePool,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_pre_ping=True,
        pool_recycle=pool_recycle_time,
        pool_reset_on_return='commit',
        echo=False,
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
