/**
 * api.js — Theodore's World frontend API client
 * Replaces all localStorage data calls with real backend API calls.
 * Loaded before the main site script.
 */

const API_BASE = "http://localhost:8000";  // Change to your deployed backend URL

// ─── Auth Token ──────────────────────────────────────────────────────────────
const TW = {
  getToken:   ()    => localStorage.getItem("tw_token"),
  setToken:   (t)   => localStorage.setItem("tw_token", t),
  clearToken: ()    => localStorage.removeItem("tw_token"),
  getUser:    ()    => JSON.parse(localStorage.getItem("tw_user") || "null"),
  setUser:    (u)   => localStorage.setItem("tw_user", JSON.stringify(u)),
  clearUser:  ()    => localStorage.removeItem("tw_user"),
};

// ─── Base Fetch Helper ────────────────────────────────────────────────────────
async function apiFetch(path, options = {}) {
  const token = TW.getToken();
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });

  if (res.status === 401) {
    TW.clearToken(); TW.clearUser();
    window.location.reload();
    return null;
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(err.detail || "Request failed");
  }

  return res.json();
}

// ─── Auth API ─────────────────────────────────────────────────────────────────
const AuthAPI = {
  register: (data)  => apiFetch("/api/auth/register", { method: "POST", body: JSON.stringify(data) }),
  login:    (data)  => apiFetch("/api/auth/login",    { method: "POST", body: JSON.stringify(data) }),
  me:       ()      => apiFetch("/api/auth/me"),
};

// ─── Posts API ────────────────────────────────────────────────────────────────
const PostsAPI = {
  list:       (params = {})       => apiFetch("/api/posts?" + new URLSearchParams(params)),
  create:     (content, tag)      => apiFetch("/api/posts", { method: "POST", body: JSON.stringify({ content, tag }) }),
  like:       (id)                => apiFetch(`/api/posts/${id}/like`, { method: "POST" }),
  reply:      (id, content)       => apiFetch(`/api/posts/${id}/replies`, { method: "POST", body: JSON.stringify({ content }) }),
  flag:       (id)                => apiFetch(`/api/posts/${id}/flag`, { method: "POST" }),
};

// ─── Users API ────────────────────────────────────────────────────────────────
const UsersAPI = {
  list:       ()       => apiFetch("/api/users"),
  get:        (id)     => apiFetch(`/api/users/${id}`),
  connect:    (id)     => apiFetch(`/api/users/${id}/connect`, { method: "POST" }),
  myConns:    ()       => apiFetch("/api/users/me/connections"),
  updateMe:   (data)   => apiFetch("/api/users/me", { method: "PATCH", body: JSON.stringify(data) }),
};

// ─── Games API ────────────────────────────────────────────────────────────────
const GamesAPI = {
  recordScore:  (game_type, score) => apiFetch("/api/games/score", { method: "POST", body: JSON.stringify({ game_type, score }) }),
  leaderboard:  (game_type)        => apiFetch(`/api/games/leaderboard/${game_type}`),
  myProgress:   ()                 => apiFetch("/api/games/my-progress"),
};

// ─── Videos API ───────────────────────────────────────────────────────────────
const VideosAPI = {
  list:   (category) => apiFetch("/api/videos" + (category ? `?category=${category}` : "")),
  submit: (data)     => apiFetch("/api/videos", { method: "POST", body: JSON.stringify(data) }),
};

// ─── Claude AI API ────────────────────────────────────────────────────────────
const ClaudeAPI = {
  chat:         (message, mode, history) => apiFetch("/api/claude/chat",        { method: "POST", body: JSON.stringify({ message, mode, history }) }),
  parentChat:   (message, history)       => apiFetch("/api/claude/parent-chat", { method: "POST", body: JSON.stringify({ message, history }) }),
  moderate:     (content)               => apiFetch("/api/claude/moderate",     { method: "POST", body: JSON.stringify({ content }) }),
  generateQuiz: (topic, count, level)   => apiFetch("/api/claude/quiz",         { method: "POST", body: JSON.stringify({ topic, count, level }) }),
  learningPath: (profile)               => apiFetch("/api/claude/learning-path",{ method: "POST", body: JSON.stringify(profile) }),
  storyCompanion: (section, reflection) => apiFetch("/api/claude/story",        { method: "POST", body: JSON.stringify({ story_section: section, reflection }) }),
};

// ─── Search (client-side over fetched data) ──────────────────────────────────
const Search = {
  async query(term) {
    if (!term || term.length < 2) return { posts: [], users: [] };
    const [posts, users] = await Promise.all([
      PostsAPI.list({ limit: 100 }),
      UsersAPI.list(),
    ]);
    const t = term.toLowerCase();
    return {
      posts: posts.filter(p => p.content.toLowerCase().includes(t) || p.tag.toLowerCase().includes(t)),
      users: users.filter(u => u.name.toLowerCase().includes(t) || u.role.toLowerCase().includes(t)),
    };
  }
};

// ─── Toast helper (reuse site's existing toast if available) ──────────────────
function twToast(msg) {
  if (typeof toast === "function") { toast(msg); return; }
  const el = document.createElement("div");
  el.style.cssText = "position:fixed;bottom:24px;left:50%;transform:translateX(-50%);background:#1a2456;color:white;padding:12px 24px;border-radius:50px;font-weight:700;z-index:9999;font-family:Nunito,sans-serif;";
  el.textContent = msg;
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 3000);
}

console.log("Theodore's World API client loaded.");
