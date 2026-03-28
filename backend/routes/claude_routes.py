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
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
import anthropic
from auth import get_current_user, get_optional_user
import models

router = APIRouter(prefix="/api/claude", tags=["claude"])

def get_client():
    key = os.getenv("ANTHROPIC_API_KEY")
    if not key or key.startswith("your-"):
        raise HTTPException(status_code=503, detail="Claude AI not configured")
    return anthropic.Anthropic(api_key=key)

MODEL = "claude-sonnet-4-6"


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
    client = get_client()

    if req.mode == "child":
        system = """You are Theodore, a friendly, warm, and gentle character from Theodore's World —
a website that helps families understand autism. You speak in simple, encouraging, and positive language
suitable for children ages 5-12. You explain things about autism, feelings, and friendship in ways kids
can understand. You never say anything scary or negative. Use simple words, short sentences, and
occasionally use gentle emojis. Always be kind and supportive."""
    else:
        system = """You are Theodore's Guide, a warm and knowledgeable assistant for parents and caregivers
on Theodore's World — a platform for understanding autism. You provide accurate, compassionate,
evidence-based information about autism spectrum disorder. You help parents navigate challenges,
find resources, and feel supported. Speak like a supportive friend who also knows a lot about autism.
Reference real strategies from occupational therapy, ABA, speech therapy, and family support when relevant."""

    messages = req.history[-10:] + [{"role": "user", "content": req.message}]

    response = client.messages.create(
        model=MODEL,
        max_tokens=600,
        system=system,
        messages=messages,
    )
    return {"reply": response.content[0].text}


# ─── Content Moderation ──────────────────────────────────────────────────────

class ModerateRequest(BaseModel):
    content: str


@router.post("/moderate")
def moderate_content(req: ModerateRequest, current_user: models.User = Depends(get_current_user)):
    client = get_client()

    system = """You are a content moderation assistant for Theodore's World, a family-friendly
autism support community. Your job is to review posts before they go live.

Respond ONLY with valid JSON in this exact format:
{
  "safe": true or false,
  "reason": "brief explanation if not safe, empty string if safe",
  "severity": "none" | "low" | "high"
}

Flag content that contains: hate speech, harassment, explicit content, dangerous medical advice,
spam, or anything inappropriate for children and vulnerable families.
Do NOT flag: venting about autism challenges, emotional posts, criticism of institutions,
strong language used respectfully, or sensitive personal stories shared in good faith."""

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",  # Use fast/cheap model for moderation
        max_tokens=150,
        system=system,
        messages=[{"role": "user", "content": f"Review this community post:\n\n{req.content}"}],
    )

    try:
        result = parse_json(response.content[0].text)
    except json.JSONDecodeError:
        result = {"safe": True, "reason": "", "severity": "none"}

    return result


# ─── Quiz Generator ──────────────────────────────────────────────────────────

class QuizRequest(BaseModel):
    topic:    str = "autism"
    count:    int = 5
    level:    str = "beginner"   # "beginner" | "intermediate" | "advanced"


@router.post("/quiz")
def generate_quiz(req: QuizRequest, current_user: models.User = Depends(get_current_user)):
    client = get_client()

    system = """You are an educational content creator for Theodore's World, an autism awareness platform.
Generate quiz questions that are accurate, kind, and educational.

Respond ONLY with valid JSON as an array:
[
  {
    "question": "...",
    "options": ["A", "B", "C", "D"],
    "correct": 0,
    "explanation": "Brief, kind explanation of why this is correct."
  }
]
The "correct" field is the 0-based index of the correct option in the options array."""

    prompt = f"""Create {req.count} {req.level}-level quiz questions about: {req.topic}

For autism-related topics, be accurate and compassionate.
Questions should educate and build understanding, not stereotype."""

    response = client.messages.create(
        model=MODEL,
        max_tokens=2000,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )

    try:
        questions = parse_json(response.content[0].text)
    except json.JSONDecodeError:
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
    client = get_client()

    system = """You are a learning guide for Theodore's World. Based on a user's profile,
create a personalized 4-step learning path through the website's features.

The site has these sections: Home (hero), Our Story (family journey), Autism 101 (educational cards),
Games (emotion recognition, memory matching, breathing exercise), Community (forum posts),
Videos (curated YouTube content), Kids Zone (character profiles, sensory info),
Tips & Resources (parent/school/sensory/social tips).

Respond ONLY with valid JSON:
{
  "greeting": "Short personal welcome message (1-2 sentences)",
  "steps": [
    {
      "step": 1,
      "section": "section name",
      "action": "specific thing to do",
      "why": "why this is right for them"
    }
  ]
}"""

    prompt = f"""Create a learning path for:
- Relationship to autism: {req.relationship}
- Experience level: {req.experience}
- Interested in: {', '.join(req.interests)}
- Age group: {req.age_group}"""

    response = client.messages.create(
        model=MODEL,
        max_tokens=800,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )

    try:
        path = parse_json(response.content[0].text)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Failed to generate learning path")

    return path


# ─── Story Companion ─────────────────────────────────────────────────────────

class StoryRequest(BaseModel):
    story_section: str   # which part of the story they just read
    reflection:    str   # user's own thoughts/question


@router.post("/story")
def story_companion(req: StoryRequest, current_user: models.User = Depends(get_current_user)):
    client = get_client()

    system = """You are a gentle story companion for Theodore's World. After a user reads part of
Theodore's family story about autism, you engage them in thoughtful, warm reflection.
Ask follow-up questions, validate their feelings, and help them connect the story to their own life.
Keep responses short (2-4 sentences), warm, and age-appropriate. Avoid clinical language."""

    prompt = f"""The user just read: "{req.story_section}"
Their reflection: "{req.reflection}"

Respond with a warm, thoughtful reply that deepens their understanding."""

    response = client.messages.create(
        model=MODEL,
        max_tokens=300,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )

    return {"reply": response.content[0].text}


# ─── Parent Support Chat ──────────────────────────────────────────────────────

class ParentChatRequest(BaseModel):
    message:  str
    history:  list = []


@router.post("/parent-chat")
def parent_support(req: ParentChatRequest, current_user: models.User = Depends(get_current_user)):
    client = get_client()

    system = """You are a private, compassionate support companion for parents and caregivers of
children with autism on Theodore's World. This is a safe space where parents can ask questions
they might be embarrassed to ask publicly.

You provide:
- Emotional validation and support
- Evidence-based information about autism
- Practical strategies from OT, speech therapy, ABA
- Help navigating school systems (IEPs, 504 plans)
- Sensory processing guidance
- Sibling relationship advice

Always acknowledge feelings first, then provide information.
If something sounds like a crisis or emergency, gently suggest professional resources.
Never diagnose or replace professional medical advice."""

    messages = req.history[-10:] + [{"role": "user", "content": req.message}]

    response = client.messages.create(
        model=MODEL,
        max_tokens=800,
        system=system,
        messages=messages,
    )

    return {"reply": response.content[0].text}
