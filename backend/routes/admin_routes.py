import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
import models, auth

router = APIRouter(prefix="/api/admin", tags=["admin"])


class BootstrapRequest(BaseModel):
    email: str

@router.post("/bootstrap")
def bootstrap_admin(req: BootstrapRequest, db: Session = Depends(get_db)):
    """One-time: promotes a user to admin if no admins exist yet."""
    existing_admin = db.query(models.User).filter_by(is_admin=True).first()
    if existing_admin:
        raise HTTPException(status_code=403, detail="An admin already exists.")
    user = db.query(models.User).filter(models.User.email == req.email.lower()).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"No user found with email {req.email}")
    user.is_admin = True
    db.commit()
    return {"success": True, "admin": user.name, "email": user.email}


def require_admin(current_user: models.User = Depends(auth.get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


@router.get("/stats")
def site_stats(db: Session = Depends(get_db), _=Depends(require_admin)):
    return {
        "users":         db.query(func.count(models.User.id)).scalar(),
        "posts":         db.query(func.count(models.Post.id)).scalar(),
        "flagged_posts": db.query(func.count(models.Post.id)).filter(models.Post.is_flagged == True).scalar(),
        "game_scores":   db.query(func.count(models.GameScore.id)).scalar(),
        "badges":        db.query(func.count(models.Badge.id)).scalar(),
        "replies":       db.query(func.count(models.Reply.id)).scalar(),
    }


@router.get("/flagged")
def flagged_posts(db: Session = Depends(get_db), _=Depends(require_admin)):
    posts = db.query(models.Post).filter(models.Post.is_flagged == True).order_by(models.Post.created_at.desc()).all()
    return [
        {
            "id":          p.id,
            "author":      p.author.name,
            "content":     p.content,
            "tag":         p.tag,
            "flag_reason": p.flag_reason,
            "created_at":  p.created_at.isoformat(),
        }
        for p in posts
    ]


@router.post("/posts/{post_id}/unflag")
def unflag_post(post_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    post = db.query(models.Post).filter_by(id=post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    post.is_flagged = False
    post.flag_reason = ""
    db.commit()
    return {"unflagged": True}


@router.delete("/posts/{post_id}")
def delete_post(post_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    post = db.query(models.Post).filter_by(id=post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    db.delete(post)
    db.commit()
    return {"deleted": True}


@router.get("/users")
def list_all_users(db: Session = Depends(get_db), _=Depends(require_admin)):
    users = db.query(models.User).order_by(models.User.created_at.desc()).all()
    return [
        {
            "id":         u.id,
            "name":       u.name,
            "email":      u.email,
            "role":       u.role,
            "is_admin":   u.is_admin,
            "is_verified": u.is_verified,
            "post_count": len(u.posts),
            "joined":     u.created_at.isoformat(),
        }
        for u in users
    ]


@router.post("/users/{user_id}/make-admin")
def toggle_admin(user_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(require_admin)):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot change your own admin status")
    user = db.query(models.User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_admin = not user.is_admin
    db.commit()
    return {"is_admin": user.is_admin, "name": user.name}
