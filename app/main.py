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

# uncomment this to create the tables whne not  using alembic migration
# models.Base.metadata.create_all(bind=engine)

origins = ["*"]

app = FastAPI()


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


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user.router)
app.include_router(post.router)
app.include_router(auth.router)
app.include_router(vote.router)


@app.get("/")
def read_root():
    """Redirect root URL to API documentation."""
    return RedirectResponse(url="/docs")
