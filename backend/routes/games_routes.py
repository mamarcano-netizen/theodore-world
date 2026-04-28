from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db
import models, auth

router = APIRouter(prefix="/api/games", tags=["games"])

BADGE_RULES = {
    "emotion": [
        (5,  "emotion_5",  "Emotion Explorer — 5 correct!"),
        (15, "emotion_15", "Emotion Expert — 15 correct!"),
        (30, "emotion_30", "Emotion Master — 30 correct!"),
    ],
    "memory": [
        (1,  "memory_1",  "Memory Starter — First match!"),
        (5,  "memory_5",  "Memory Pro — 5 games!"),
        (10, "memory_10", "Memory Champion — 10 games!"),
    ],
    "quiz": [
        (3,  "quiz_3",  "Quiz Curious — 3 questions!"),
        (10, "quiz_10", "Quiz Whiz — 10 questions!"),
        (25, "quiz_25", "Quiz Master — 25 questions!"),
    ],
    "social": [
        (3,  "social_3",  "Social Star — 3 scenarios!"),
        (10, "social_10", "Social Champion — 10 scenarios!"),
        (25, "social_25", "Social Hero — 25 scenarios!"),
    ],
    "wordscramble": [
        (5,  "word_5",  "Word Wizard — 5 words!"),
        (15, "word_15", "Word Pro — 15 words!"),
        (30, "word_30", "Word Master — 30 words!"),
    ],
    "pattern": [
        (3,  "pattern_3",  "Pattern Finder — 3 solved!"),
        (10, "pattern_10", "Pattern Pro — 10 solved!"),
        (25, "pattern_25", "Pattern Master — 25 solved!"),
    ],
}


class ScoreRequest(BaseModel):
    game_type: str   # "emotion" | "memory" | "quiz"
    score:     int


@router.post("/score")
def record_score(
    req: ScoreRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    db.add(models.GameScore(user_id=current_user.id, game_type=req.game_type, score=req.score))
    db.commit()

    # Total score across all sessions for this game type
    total = db.query(models.GameScore).filter_by(
        user_id=current_user.id, game_type=req.game_type
    ).count()

    # Award badges
    new_badges = []
    for threshold, badge_type, label in BADGE_RULES.get(req.game_type, []):
        if total >= threshold:
            existing = db.query(models.Badge).filter_by(
                user_id=current_user.id, badge_type=badge_type
            ).first()
            if not existing:
                b = models.Badge(user_id=current_user.id, badge_type=badge_type, label=label)
                db.add(b)
                new_badges.append(label)

    db.commit()
    return {"recorded": True, "total_sessions": total, "new_badges": new_badges}


@router.get("/leaderboard/{game_type}")
def leaderboard(game_type: str, db: Session = Depends(get_db)):
    scores = (
        db.query(models.GameScore)
        .filter_by(game_type=game_type)
        .order_by(models.GameScore.score.desc())
        .limit(10)
        .all()
    )
    return [
        {"user": s.user.name, "score": s.score, "date": s.created_at.isoformat()}
        for s in scores
    ]


@router.get("/my-progress")
def my_progress(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    result = {}
    for game_type in ("emotion", "memory", "quiz", "social", "wordscramble", "pattern"):
        scores = db.query(models.GameScore).filter_by(
            user_id=current_user.id, game_type=game_type
        ).all()
        if scores:
            result[game_type] = {
                "sessions":  len(scores),
                "best":      max(s.score for s in scores),
                "last":      scores[-1].score,
            }
        else:
            result[game_type] = {"sessions": 0, "best": 0, "last": 0}
    return result
