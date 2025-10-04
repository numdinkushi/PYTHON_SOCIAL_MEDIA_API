from typing import List
from fastapi import FastAPI, status, HTTPException, Depends
from sqlalchemy.orm import Session
from .database import engine, get_db
from . import models
from .schemas import PostCreate, PostResponse, UserCreate, UserResponse
from .utils import hash_password
from .routers import user, post, auth
from .config import settings


models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(user.router)
app.include_router(post.router)
app.include_router(auth.router)


@app.get("/")
def read_root():
    return {"message": "Hello, user !Kushi"}
