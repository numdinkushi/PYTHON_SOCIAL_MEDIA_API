from typing import List
from fastapi import APIRouter, status, HTTPException, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models
from ..schemas import UserCreate, UserResponse
from ..utils import hash_password
from .oauth2 import get_current_user

router = APIRouter(
    prefix="/users",
    tags=["users"]
)


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    try:
        # Check if user already exists
        existing_user = db.query(models.User).filter(
            models.User.email == user.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists"
            )

        # Hash the password
        hashed_password = hash_password(user.password)

        new_user = models.User(email=user.email, password=hashed_password)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )


@router.get("/", response_model=List[UserResponse])
def get_users(db: Session = Depends(get_db)):
    users = db.query(models.User).all()
    return users


@router.get("/logged-in-user", response_model=UserResponse)
def get_logged_in_user(current_user: int = Depends(get_current_user)):
    return current_user


@router.get('/{id}', response_model=UserResponse)
def get_user(id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id: {id} not found",
        )
    return user
