from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from database import get_db
import models, auth

router = APIRouter(prefix="/api/users", tags=["users"])


def user_public(u: models.User) -> dict:
    return {
        "id":         u.id,
        "name":       u.name,
        "role":       u.role,
        "bio":        u.bio,
        "location":   u.location,
        "color":      u.color,
        "is_verified": u.is_verified,
        "badges":     [{"type": b.badge_type, "label": b.label} for b in u.badges],
        "post_count": len(u.posts),
        "joined":     u.created_at.isoformat(),
    }


@router.get("")
def list_users(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    users = db.query(models.User).offset(skip).limit(limit).all()
    return [user_public(u) for u in users]


@router.get("/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user_public(user)


class UpdateProfileRequest(BaseModel):
    name:     Optional[str] = None
    role:     Optional[str] = None
    bio:      Optional[str] = None
    location: Optional[str] = None


@router.patch("/me")
def update_profile(
    req: UpdateProfileRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    if req.name:     current_user.name     = req.name.strip()
    if req.role:     current_user.role     = req.role
    if req.bio is not None:      current_user.bio      = req.bio
    if req.location is not None: current_user.location = req.location
    db.commit()
    return user_public(current_user)


@router.post("/{user_id}/connect")
def toggle_connect(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot connect with yourself")
    target = db.query(models.User).filter_by(id=user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    existing = db.query(models.Connection).filter_by(
        user_id=current_user.id, connected_user_id=user_id
    ).first()

    if existing:
        db.delete(existing)
        db.commit()
        return {"connected": False}
    else:
        db.add(models.Connection(user_id=current_user.id, connected_user_id=user_id))
        db.commit()
        return {"connected": True}


@router.get("/me/connections")
def my_connections(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    conn_ids = [c.connected_user_id for c in current_user.connections]
    users = db.query(models.User).filter(models.User.id.in_(conn_ids)).all()
    return [user_public(u) for u in users]
