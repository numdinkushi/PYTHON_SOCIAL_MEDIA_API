from typing import List
from fastapi import FastAPI, status, HTTPException, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from .database import engine, get_db
from . import models
from .schemas import PostCreate, PostResponse, UserCreate, UserResponse
from .utils import hash_password
from .routers import user, post, auth, vote
from .config import settings
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

# uncomment this to create the tables whne not  using alembic migration
# models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Add CORS middleware BEFORE startup event to ensure it processes all responses
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Run database migrations on startup."""
    import os
    from alembic.config import Config
    from alembic import command

    # Get the project root directory (where alembic.ini is located)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    alembic_ini_path = os.path.join(project_root, "alembic.ini")

    try:
        alembic_cfg = Config(alembic_ini_path)
        command.upgrade(alembic_cfg, "head")
        print("Database migrations completed successfully")
    except Exception as e:
        # Log error but don't crash the app
        print(f"Migration error: {e}")
        import traceback
        traceback.print_exc()


# Add exception handler to ensure CORS headers on all errors
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Ensure CORS headers are added even on unhandled exceptions."""
    # Let FastAPI handle HTTPExceptions normally (they'll get CORS from middleware)
    if isinstance(exc, (HTTPException, StarletteHTTPException)):
        raise exc
    # For other exceptions, create a response with CORS headers
    response = JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )
    # Explicitly add CORS headers to error responses
    response.headers["access-control-allow-origin"] = "*"
    response.headers["access-control-allow-methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
    response.headers["access-control-allow-headers"] = "*"
    return response

app.include_router(user.router)
app.include_router(post.router)
app.include_router(auth.router)
app.include_router(vote.router)


@app.get("/")
def read_root():
    """Redirect root URL to API documentation."""
    return RedirectResponse(url="/docs")
