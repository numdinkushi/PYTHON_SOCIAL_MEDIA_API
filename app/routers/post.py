from typing import List, Optional
from fastapi import APIRouter, status, HTTPException, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models
from ..schemas import PostCreate, PostResponse
from .oauth2 import get_current_user
router = APIRouter(
    prefix="/posts",
    tags=["posts"]
)


@router.get("/", response_model=List[PostResponse])
def get_posts(db: Session = Depends(get_db), current_user: int = Depends(get_current_user),
              limit: int = 10, skip: int = 0, search: Optional[str] = ""):
    print({'limit': limit}, {'skip': skip}, {'search': search})
    query = db.query(models.Post)
    if search:
        query = query.filter(
            models.Post.title.ilike(f"%{search}%") |
            models.Post.content.ilike(f"%{search}%")
        )
    posts = query.limit(limit).offset(skip).all()
    return posts


@router.get("/my-posts", response_model=List[PostResponse])
def get_my_posts(db: Session = Depends(get_db), current_user: int = Depends(get_current_user)):
    posts = db.query(models.Post).filter(
        models.Post.owner_id == current_user.id).all()
    return posts


@router.get("/{id}", response_model=PostResponse)
def get_post(id: int, db: Session = Depends(get_db), current_user: int = Depends(get_current_user)):
    #    print(current_user.dict() if hasattr(current_user, "dict") else current_user.__dict__)
    #    if current_user.id != id:
    #         raise HTTPException(
    #             status_code=status.HTTP_403_FORBIDDEN,
    #             detail="Not authorized to perform requested action",
    #         )
    post = db.query(models.Post).filter(models.Post.id == id).first()
    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post with id: {id} not found",
        )
    return post


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=PostResponse)
def create_post(post: PostCreate, db: Session = Depends(get_db), current_user: int = Depends(get_current_user)):
    try:
        post_data = post.dict()
        post_data['owner_id'] = current_user.id
        new_post = models.Post(**post_data)
        db.add(new_post)
        db.commit()
        db.refresh(new_post)
        return new_post
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create post: {str(e)}"
        )


@router.put("/{id}", response_model=PostResponse)
def update_post(id: int, post: PostCreate, db: Session = Depends(get_db), current_user: int = Depends(get_current_user)):
    post_query = db.query(models.Post).filter(models.Post.id == id)
    updated_post = post_query.first()

    if updated_post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post with id: {id} not found",
        )

    if updated_post.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to perform requested action",
        )
    post_query.update(post.dict(), synchronize_session=False)
    db.commit()
    db.refresh(updated_post)
    return updated_post


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(id: int, db: Session = Depends(get_db), current_user: int = Depends(get_current_user)):
    post = db.query(models.Post).filter(models.Post.id == id).first()
    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post with id: {id} not found",
        )
    if post.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to perform requested action",
        )
    db.delete(post)
    db.commit()
    return post
