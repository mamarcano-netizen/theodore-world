from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from database import get_db
import models, auth

router = APIRouter(prefix="/api/auth", tags=["auth"])

AVATAR_COLORS = [
    "#C3A9F5","#6EC6F5","#6FDEBC","#FF8FAB",
    "#FFD166","#FF6B6B","#FFB347","#7B5EA7",
]


class RegisterRequest(BaseModel):
    name:     str
    email:    EmailStr
    password: str
    role:     str = "Community Member"
    bio:      str = ""
    location: str = ""


class LoginRequest(BaseModel):
    email:    EmailStr
    password: str


def user_to_dict(u: models.User, db: Session) -> dict:
    badge_list = [{"type": b.badge_type, "label": b.label} for b in u.badges]
    return {
        "id":         u.id,
        "name":       u.name,
        "email":      u.email,
        "role":       u.role,
        "bio":        u.bio,
        "location":   u.location,
        "color":      u.color,
        "is_verified": u.is_verified,
        "is_admin":   u.is_admin,
        "badges":     badge_list,
        "created_at": u.created_at.isoformat(),
    }


@router.post("/register", status_code=201)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.email == req.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    import hashlib
    color_index = int(hashlib.md5(req.email.encode()).hexdigest(), 16) % len(AVATAR_COLORS)

    user = models.User(
        name          = req.name.strip(),
        email         = req.email.lower(),
        password_hash = auth.hash_password(req.password),
        role          = req.role,
        bio           = req.bio,
        location      = req.location,
        color         = AVATAR_COLORS[color_index],
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Welcome badge
    db.add(models.Badge(user_id=user.id, badge_type="welcome", label="Welcome to the Community!"))
    db.commit()

    token = auth.create_token(user.id)
    return {"token": token, "user": user_to_dict(user, db)}


@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == req.email.lower()).first()
    if not user or not auth.verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = auth.create_token(user.id)
    return {"token": token, "user": user_to_dict(user, db)}


@router.get("/me")
def me(current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    return user_to_dict(current_user, db)
