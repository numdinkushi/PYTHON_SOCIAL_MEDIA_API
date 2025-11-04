from typing import List
from fastapi import FastAPI, status, HTTPException, Depends
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
    return {"message": "Hello, user !Kushi"}
