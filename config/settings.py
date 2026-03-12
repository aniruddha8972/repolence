"""
RepoEngineer — Centralized Configuration
"""
from __future__ import annotations

# ── GitHub API ────────────────────────────────────────────────────────────────
GH_API_BASE  = "https://api.github.com"
GH_RAW_BASE  = "https://raw.githubusercontent.com"
GH_API_HDRS  = {"Accept": "application/vnd.github.v3+json"}

# ── Analysis Limits ───────────────────────────────────────────────────────────
MAX_FILES_TO_FETCH  = 9999    # fetch ALL code files (no cap)
MAX_FILE_SIZE_BYTES = 8_000   # truncate files beyond 8 KB each
FILE_FETCH_TIMEOUT  = 10      # seconds per file request
API_FETCH_TIMEOUT   = 20      # seconds for API (tree) requests
MAX_NODES_PER_LAYER = 999     # show all nodes in arch layers
MAX_CALL_EDGES      = 80      # max call-graph edges displayed
MAX_CLASSES_SHOWN   = 20
MAX_METHODS_PER_CLS = 15
FETCH_WORKERS       = 30      # parallel fetch threads (higher = faster)

# ── Supported Code Extensions ─────────────────────────────────────────────────
CODE_EXTENSIONS = {
    "js", "ts", "jsx", "tsx",
    "py",
    "go",
    "rs",
    "java",
    "rb",
    "php",
    "cs",
    "cpp", "cc", "cxx", "c", "h",
    "swift",
    "kt", "kts",
    "scala",
    "ex", "exs",
    "zig",
}

# ── Files always fetched first ────────────────────────────────────────────────
PRIORITY_MANIFESTS = [
    "package.json", "pyproject.toml", "requirements.txt",
    "setup.py", "setup.cfg", "go.mod", "Cargo.toml",
    "Gemfile", "composer.json", "pom.xml",
    "README.md", "Dockerfile", "docker-compose.yml", ".env.example",
]

# ── Skip patterns ─────────────────────────────────────────────────────────────
SKIP_PATTERNS = [
    r"node_modules",
    r"\.min\.",
    r"[/\\]dist[/\\]",
    r"[/\\]build[/\\]",
    r"[/\\]\.next[/\\]",
    r"[/\\]vendor[/\\]",
    r"__pycache__",
    r"\.pyc$",
    r"\.d\.ts$",
    r"\.snap$",
    r"\.lock$",
    r"package-lock",
    r"yarn\.lock",
    r"\.map$",
    r"[/\\]\.git[/\\]",
    r"coverage[/\\]",
    r"\.egg-info",
    r"[/\\]migrations[/\\].*\.py$",
]

# ── Test file patterns ────────────────────────────────────────────────────────
TEST_PATTERNS = [
    r"test", r"spec", r"mock", r"fixture",
    r"__test__", r"\.test\.", r"\.spec\.",
]

# ── Architecture layer definitions ────────────────────────────────────────────
ARCH_LAYERS = {
    "entry": {
        "label":  "ENTRY / ROUTES",
        "desc":   "Routers, controllers, URL mappings, API entry points",
        "color":  "#00e87a",
        "bg":     "rgba(0,232,122,0.07)",
        "border": "rgba(0,232,122,0.20)",
    },
    "ctrl": {
        "label":  "CONTROLLERS / LOGIC",
        "desc":   "Middleware, business logic, request handlers",
        "color":  "#a67cff",
        "bg":     "rgba(166,124,255,0.07)",
        "border": "rgba(166,124,255,0.20)",
    },
    "service": {
        "label":  "SERVICES",
        "desc":   "Service classes, use-cases, domain logic",
        "color":  "#4b9eff",
        "bg":     "rgba(75,158,255,0.07)",
        "border": "rgba(75,158,255,0.20)",
    },
    "data": {
        "label":  "DATA / MODELS",
        "desc":   "ORM models, repositories, DB queries, schemas",
        "color":  "#ff8f3c",
        "bg":     "rgba(255,143,60,0.07)",
        "border": "rgba(255,143,60,0.20)",
    },
    "util": {
        "label":  "UTILS / CONFIG",
        "desc":   "Helpers, config, constants, shared utilities",
        "color":  "#ffd166",
        "bg":     "rgba(255,209,102,0.07)",
        "border": "rgba(255,209,102,0.20)",
    },
    "ext": {
        "label":  "EXTERNAL DEPS",
        "desc":   "npm/pip packages, third-party APIs, SDKs",
        "color":  "#888",
        "bg":     "rgba(80,80,120,0.07)",
        "border": "rgba(80,80,120,0.20)",
    },
}

# ── Example repos ─────────────────────────────────────────────────────────────
EXAMPLE_REPOS = [
    ("expressjs/express",    "https://github.com/expressjs/express"),
    ("pallets/flask",        "https://github.com/pallets/flask"),
    ("django/django",        "https://github.com/django/django"),
    ("fastapi/fastapi",      "https://github.com/fastapi/fastapi"),
    ("axios/axios",          "https://github.com/axios/axios"),
    ("fastify/fastify",      "https://github.com/fastify/fastify"),
    ("koajs/koa",            "https://github.com/koajs/koa"),
]

# ── UI Theme ──────────────────────────────────────────────────────────────────
THEME = {
    "bg":     "#06060d",
    "card":   "#0d0d1a",
    "border": "#1a1a2e",
    "green":  "#00e87a",
    "blue":   "#4b9eff",
    "orange": "#ff8f3c",
    "purple": "#a67cff",
    "red":    "#ff4d6a",
    "yellow": "#ffd166",
    "muted":  "#505070",
    "text":   "#dde0f5",
}
