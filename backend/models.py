from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from database import Base


def now():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id           = Column(Integer, primary_key=True, index=True)
    name         = Column(String(100), nullable=False)
    email        = Column(String(200), unique=True, index=True, nullable=False)
    password_hash = Column(String(200), nullable=False)
    role         = Column(String(100), default="Community Member")
    bio          = Column(Text, default="")
    location     = Column(String(100), default="")
    color        = Column(String(20), default="#C3A9F5")
    is_verified  = Column(Boolean, default=False)   # verified educator/doctor badge
    is_admin     = Column(Boolean, default=False)
    created_at   = Column(DateTime, default=now)

    posts        = relationship("Post", back_populates="author", cascade="all, delete-orphan")
    replies      = relationship("Reply", back_populates="author", cascade="all, delete-orphan")
    likes        = relationship("Like", back_populates="user", cascade="all, delete-orphan")
    game_scores  = relationship("GameScore", back_populates="user", cascade="all, delete-orphan")
    badges       = relationship("Badge", back_populates="user", cascade="all, delete-orphan")
    videos       = relationship("Video", back_populates="author", cascade="all, delete-orphan")
    connections  = relationship("Connection", foreign_keys="Connection.user_id", back_populates="user", cascade="all, delete-orphan")


class Post(Base):
    __tablename__ = "posts"

    id           = Column(Integer, primary_key=True, index=True)
    author_id    = Column(Integer, ForeignKey("users.id"), nullable=False)
    content      = Column(Text, nullable=False)
    tag          = Column(String(50), default="Question")
    is_flagged   = Column(Boolean, default=False)
    flag_reason  = Column(Text, default="")
    created_at   = Column(DateTime, default=now)

    author       = relationship("User", back_populates="posts")
    replies      = relationship("Reply", back_populates="post", cascade="all, delete-orphan")
    likes        = relationship("Like", back_populates="post", cascade="all, delete-orphan")


class Reply(Base):
    __tablename__ = "replies"

    id           = Column(Integer, primary_key=True, index=True)
    post_id      = Column(Integer, ForeignKey("posts.id"), nullable=False)
    author_id    = Column(Integer, ForeignKey("users.id"), nullable=False)
    content      = Column(Text, nullable=False)
    is_flagged   = Column(Boolean, default=False)
    created_at   = Column(DateTime, default=now)

    post         = relationship("Post", back_populates="replies")
    author       = relationship("User", back_populates="replies")


class Like(Base):
    __tablename__ = "likes"

    id           = Column(Integer, primary_key=True, index=True)
    post_id      = Column(Integer, ForeignKey("posts.id"), nullable=False)
    user_id      = Column(Integer, ForeignKey("users.id"), nullable=False)

    post         = relationship("Post", back_populates="likes")
    user         = relationship("User", back_populates="likes")


class Connection(Base):
    __tablename__ = "connections"

    id               = Column(Integer, primary_key=True, index=True)
    user_id          = Column(Integer, ForeignKey("users.id"), nullable=False)
    connected_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    user             = relationship("User", foreign_keys=[user_id], back_populates="connections")


class GameScore(Base):
    __tablename__ = "game_scores"

    id           = Column(Integer, primary_key=True, index=True)
    user_id      = Column(Integer, ForeignKey("users.id"), nullable=False)
    game_type    = Column(String(50), nullable=False)   # "emotion", "memory", "quiz"
    score        = Column(Integer, default=0)
    created_at   = Column(DateTime, default=now)

    user         = relationship("User", back_populates="game_scores")


class Badge(Base):
    __tablename__ = "badges"

    id           = Column(Integer, primary_key=True, index=True)
    user_id      = Column(Integer, ForeignKey("users.id"), nullable=False)
    badge_type   = Column(String(100), nullable=False)
    label        = Column(String(200), default="")
    earned_at    = Column(DateTime, default=now)

    user         = relationship("User", back_populates="badges")


class Video(Base):
    __tablename__ = "videos"

    id           = Column(Integer, primary_key=True, index=True)
    title        = Column(String(200), nullable=False)
    author_id    = Column(Integer, ForeignKey("users.id"), nullable=False)
    yt_id        = Column(String(20), nullable=False)
    category     = Column(String(50), default="Resource")
    description  = Column(Text, default="")
    is_flagged   = Column(Boolean, default=False)
    created_at   = Column(DateTime, default=now)

    author       = relationship("User", back_populates="videos")


class QuizQuestion(Base):
    """AI-generated quiz questions stored for reuse."""
    __tablename__ = "quiz_questions"

    id           = Column(Integer, primary_key=True, index=True)
    topic        = Column(String(100), default="autism")
    question     = Column(Text, nullable=False)
    options      = Column(JSON, nullable=False)   # list of 4 strings
    correct      = Column(Integer, nullable=False) # index 0-3
    explanation  = Column(Text, default="")
    created_at   = Column(DateTime, default=now)
