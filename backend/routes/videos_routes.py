import re
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from database import get_db
import models, auth

router = APIRouter(prefix="/api/videos", tags=["videos"])

YT_PATTERN = re.compile(r"(?:v=|youtu\.be/|embed/)([a-zA-Z0-9_-]{11})")


def video_to_dict(v: models.Video) -> dict:
    return {
        "id":          v.id,
        "title":       v.title,
        "author":      v.author.name,
        "author_color": v.author.color,
        "yt_id":       v.yt_id,
        "category":    v.category,
        "description": v.description,
        "created_at":  v.created_at.isoformat(),
    }


class CreateVideoRequest(BaseModel):
    title:       str
    url:         str
    category:    str = "Resource"
    description: str = ""


@router.get("")
def get_videos(category: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(models.Video).filter_by(is_flagged=False)
    if category:
        q = q.filter_by(category=category)
    videos = q.order_by(models.Video.created_at.desc()).all()
    return [video_to_dict(v) for v in videos]


@router.post("", status_code=201)
def submit_video(
    req: CreateVideoRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    m = YT_PATTERN.search(req.url)
    yt_id = m.group(1) if m else req.url
    if len(yt_id) != 11:
        raise HTTPException(status_code=400, detail="Invalid YouTube URL")

    video = models.Video(
        title       = req.title.strip(),
        author_id   = current_user.id,
        yt_id       = yt_id,
        category    = req.category,
        description = req.description.strip(),
    )
    db.add(video)
    db.commit()
    db.refresh(video)
    return video_to_dict(video)
