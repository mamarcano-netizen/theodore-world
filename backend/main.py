"""
main.py — Theodore's World Backend
FastAPI + SQLite + Claude AI

HOW TO RUN (development):
  cd backend
  pip install -r requirements.txt
  uvicorn main:app --reload --port 8000

API docs available at: http://localhost:8000/docs
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv

load_dotenv()

from database import engine, Base
import models  # noqa — registers all models

# Create all tables
Base.metadata.create_all(bind=engine)

from routes import auth_routes, posts_routes, users_routes, games_routes, videos_routes, claude_routes, tts_routes, admin_routes

app = FastAPI(
    title="Theodore's World API",
    description="Backend for Theodore's World — autism education platform",
    version="2.0.0",
)

# CORS — allow frontend to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://theodore-world.com",
        "https://www.theodore-world.com",
        "http://localhost:8000",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all route groups
app.include_router(auth_routes.router)
app.include_router(posts_routes.router)
app.include_router(users_routes.router)
app.include_router(games_routes.router)
app.include_router(videos_routes.router)
app.include_router(claude_routes.router)
app.include_router(tts_routes.router)
app.include_router(admin_routes.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "version": "2.0.0"}


# Serve frontend static files (when deployed together)
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

    @app.get("/")
    def serve_index():
        return FileResponse(os.path.join(frontend_dir, "index.html"))
