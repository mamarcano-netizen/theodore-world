"""
claude_routes.py — All Claude AI-powered endpoints for Theodore's World.

Endpoints:
  POST /api/claude/chat          — Ask Theodore chatbot (kid-friendly / parent mode)
  POST /api/claude/parent-chat   — Private parent support chat
  POST /api/claude/moderate      — Auto-moderate a post before it goes live
  POST /api/claude/quiz          — Generate new quiz questions
  POST /api/claude/learning-path — Personalized learning path based on user profile
  POST /api/claude/story         — Story companion reflection after reading
"""

import os
import json
import re
import requests
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from auth import get_current_user, get_optional_user
import models

router = APIRouter(prefix="/api/claude", tags=["claude"])

MODEL = "claude-sonnet-4-6"
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"


def claude(system: str, messages: list, max_tokens: int = 800) -> str:
    """Call Anthropic API directly via requests — no SDK dependency."""
    key = os.getenv("ANTHROPIC_API_KEY")
    if not key or key.startswith("your-"):
        raise HTTPException(status_code=503, detail="Claude AI not configured")

    headers = {
        "x-api-key": key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    body = {
        "model": MODEL,
        "max_tokens": max_tokens,
        "system": system,
        "messages": messages,
    }
    try:
        resp = requests.post(ANTHROPIC_URL, headers=headers, json=body, timeout=60)
        resp.raise_for_status()
        return resp.json()["content"][0]["text"]
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Claude connection error: {str(e)}")


def parse_json(text: str):
    """Parse JSON from Claude's response, handling markdown code blocks."""
    # Strip markdown code fences if present
    clean = re.sub(r"```(?:json)?\s*", "", text).strip().rstrip("`").strip()
    return json.loads(clean)


# ─── Theodore Chatbot ────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message:    str
    mode:       str = "child"   # "child" or "parent"
    history:    list = []       # list of {role, content} for multi-turn


@router.post("/chat")
def theodore_chat(req: ChatRequest, current_user: Optional[models.User] = Depends(get_optional_user)):
    if req.mode == "child":
        system = """You are Theodore, a friendly, warm, and gentle character from Theodore's World —
a website that helps families understand autism. You speak in simple, encouraging, and positive language
suitable for children ages 5-12. You explain things about autism, feelings, and friendship in ways kids
can understand. You never say anything scary or negative. Use simple words and short sentences.
IMPORTANT: Never use markdown formatting. No asterisks, no hashtags, no bullet points, no bold, no headers.
Write in plain conversational sentences only, exactly as you would speak out loud to a child. Always be kind and supportive."""
    else:
        system = """You are Theodore's Guide, a warm and knowledgeable assistant for parents and caregivers
on Theodore's World — a platform for understanding autism. You provide accurate, compassionate,
evidence-based information about autism spectrum disorder. You help parents navigate challenges,
find resources, and feel supported. Speak like a supportive friend who also knows a lot about autism.
Reference real strategies from occupational therapy, ABA, speech therapy, and family support when relevant."""

    messages = req.history[-10:] + [{"role": "user", "content": req.message}]
    return {"reply": claude(system, messages, max_tokens=600)}


# ─── Content Moderation ──────────────────────────────────────────────────────

class ModerateRequest(BaseModel):
    content: str


@router.post("/moderate")
def moderate_content(req: ModerateRequest, current_user: models.User = Depends(get_current_user)):
    system = """You are a content moderation assistant for Theodore's World, a family-friendly
autism support community. Your job is to review posts before they go live.

Respond ONLY with valid JSON in this exact format:
{"safe": true, "reason": "", "severity": "none"}

Flag content that contains: hate speech, harassment, explicit content, dangerous medical advice,
spam, or anything inappropriate for children and vulnerable families.
Do NOT flag: venting about autism challenges, emotional posts, criticism of institutions,
strong language used respectfully, or sensitive personal stories shared in good faith."""

    try:
        text = claude(system, [{"role": "user", "content": f"Review this post:\n\n{req.content}"}], max_tokens=150)
        result = parse_json(text)
    except Exception:
        result = {"safe": True, "reason": "", "severity": "none"}
    return result


# ─── Quiz Generator ──────────────────────────────────────────────────────────

class QuizRequest(BaseModel):
    topic:    str = "autism"
    count:    int = 5
    level:    str = "beginner"   # "beginner" | "intermediate" | "advanced"


@router.post("/quiz")
def generate_quiz(req: QuizRequest, current_user: models.User = Depends(get_current_user)):
    system = """You are an educational content creator for Theodore's World, an autism awareness platform.
Respond ONLY with a valid JSON array, no markdown:
[{"question":"...","options":["A","B","C","D"],"correct":0,"explanation":"..."}]"""

    prompt = f"Create {req.count} {req.level}-level quiz questions about: {req.topic}. Be accurate and compassionate."

    try:
        text = claude(system, [{"role": "user", "content": prompt}], max_tokens=2000)
        questions = parse_json(text)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to generate quiz questions")
    return {"questions": questions}


# ─── Personalized Learning Path ───────────────────────────────────────────────

class LearningPathRequest(BaseModel):
    relationship:  str   # "parent", "child", "educator", "sibling", "curious"
    experience:    str   # "new", "some", "experienced"
    interests:     list  # e.g. ["games", "stories", "community"]
    age_group:     str = "adult"  # "child", "teen", "adult"


@router.post("/learning-path")
def learning_path(req: LearningPathRequest, current_user: models.User = Depends(get_current_user)):
    system = """You are a learning guide for Theodore's World. Create a personalized 4-step path.
Respond ONLY with valid JSON, no markdown:
{"greeting":"...","steps":[{"step":1,"section":"...","action":"...","why":"..."}]}"""

    prompt = f"Profile: relationship={req.relationship}, experience={req.experience}, interests={req.interests}, age={req.age_group}"

    try:
        text = claude(system, [{"role": "user", "content": prompt}], max_tokens=800)
        path = parse_json(text)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to generate learning path")
    return path


# ─── Story Companion ─────────────────────────────────────────────────────────

class StoryRequest(BaseModel):
    story_section: str   # which part of the story they just read
    reflection:    str   # user's own thoughts/question


@router.post("/story")
def story_companion(req: StoryRequest, current_user: models.User = Depends(get_current_user)):
    system = """You are a gentle story companion for Theodore's World. Engage the user in warm,
thoughtful reflection after reading. Keep responses short (2-4 sentences) and age-appropriate."""

    prompt = f'They read: "{req.story_section}". Their thought: "{req.reflection}". Respond warmly.'
    return {"reply": claude(system, [{"role": "user", "content": prompt}], max_tokens=300)}


# ─── Parent Support Chat ──────────────────────────────────────────────────────

class ParentChatRequest(BaseModel):
    message:  str
    history:  list = []


@router.post("/parent-chat")
def parent_support(req: ParentChatRequest, current_user: Optional[models.User] = Depends(get_optional_user)):
    system = """You are a compassionate support companion for parents of children with autism on
Theodore's World. Provide emotional validation, evidence-based autism info, practical strategies
from OT/speech therapy/ABA, and help with IEPs and school systems. Always acknowledge feelings first.
Never diagnose or replace professional medical advice."""

    messages = req.history[-10:] + [{"role": "user", "content": req.message}]
    return {"reply": claude(system, messages, max_tokens=800)}
