from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from database import get_db
import models, auth
from routes.claude_routes import check_content_safe

router = APIRouter(prefix="/api/posts", tags=["posts"])


def post_to_dict(p: models.Post, current_user_id: Optional[int] = None) -> dict:
    liked = any(l.user_id == current_user_id for l in p.likes) if current_user_id else False
    return {
        "id":         p.id,
        "author":     p.author.name,
        "author_id":  p.author_id,
        "color":      p.author.color,
        "initials":   "".join(w[0].upper() for w in p.author.name.split()[:2]),
        "content":    p.content,
        "tag":        p.tag,
        "is_flagged": p.is_flagged,
        "likes":      len(p.likes),
        "liked":      liked,
        "reply_count": len(p.replies),
        "replies":    [{"author": r.author.name, "content": r.content, "created_at": r.created_at.isoformat()} for r in p.replies],
        "created_at": p.created_at.isoformat(),
    }


class CreatePostRequest(BaseModel):
    content: str
    tag:     str = "Question"


class CreateReplyRequest(BaseModel):
    content: str


@router.get("")
def get_posts(
    skip: int = 0,
    limit: int = 50,
    tag: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(auth.get_optional_user),
):
    q = db.query(models.Post).filter(models.Post.is_flagged == False)
    if tag:
        q = q.filter(models.Post.tag == tag)
    posts = q.order_by(models.Post.created_at.desc()).offset(skip).limit(limit).all()
    uid = current_user.id if current_user else None
    return [post_to_dict(p, uid) for p in posts]


@router.post("", status_code=201)
def create_post(
    req: CreatePostRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    safe, reason = check_content_safe(req.content.strip())
    if not safe:
        raise HTTPException(status_code=400, detail=f"Post not allowed: {reason}")

    post = models.Post(author_id=current_user.id, content=req.content.strip(), tag=req.tag)
    db.add(post)
    db.commit()
    db.refresh(post)

    # Badge: first post
    existing = db.query(models.Badge).filter_by(user_id=current_user.id, badge_type="first_post").first()
    if not existing:
        db.add(models.Badge(user_id=current_user.id, badge_type="first_post", label="First Post!"))
        db.commit()

    return post_to_dict(post, current_user.id)


@router.post("/{post_id}/like")
def toggle_like(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    post = db.query(models.Post).filter_by(id=post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    existing = db.query(models.Like).filter_by(post_id=post_id, user_id=current_user.id).first()
    if existing:
        db.delete(existing)
        db.commit()
        return {"liked": False, "likes": len(post.likes) - 1}
    else:
        db.add(models.Like(post_id=post_id, user_id=current_user.id))
        db.commit()
        db.refresh(post)
        return {"liked": True, "likes": len(post.likes)}


@router.post("/{post_id}/replies", status_code=201)
def add_reply(
    post_id: int,
    req: CreateReplyRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    post = db.query(models.Post).filter_by(id=post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    reply = models.Reply(post_id=post_id, author_id=current_user.id, content=req.content.strip())
    db.add(reply)
    db.commit()
    db.refresh(reply)
    return {"author": current_user.name, "content": reply.content, "created_at": reply.created_at.isoformat()}


@router.post("/{post_id}/flag")
def flag_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    post = db.query(models.Post).filter_by(id=post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    post.is_flagged = True
    post.flag_reason = f"Flagged by user {current_user.id}"
    db.commit()
    return {"flagged": True}
