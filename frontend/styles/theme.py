"""
RepoLens — Streamlit CSS Theme
Injects custom dark-theme styling that overrides Streamlit defaults.
"""

GLOBAL_CSS = """
<style>
/* ── Google Fonts ─────────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=Outfit:wght@500;600;700;800;900&display=swap');

/* ── Root variables ──────────────────────────────────────────── */
:root {
  --bg:       #06060d;
  --c1:       #0d0d1a;
  --c2:       #111120;
  --c3:       #17172a;
  --b1:       #1a1a2e;
  --b2:       #22223a;
  --b3:       #2c2c4a;
  --green:    #00e87a;
  --blue:     #4b9eff;
  --orange:   #ff8f3c;
  --purple:   #a67cff;
  --red:      #ff4d6a;
  --yellow:   #ffd166;
  --text:     #dde0f5;
  --muted:    #505070;
  --dim:      #2a2a45;
}

/* ── Streamlit app background ────────────────────────────────── */
.stApp {
  background: var(--bg) !important;
  font-family: 'JetBrains Mono', monospace !important;
}

/* ── Hide Streamlit branding ─────────────────────────────────── */
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }

/* ── Main content area ───────────────────────────────────────── */
.block-container {
  padding-top: 1.5rem !important;
  padding-bottom: 2rem !important;
  max-width: 1300px !important;
}

/* ── All text ────────────────────────────────────────────────── */
.stApp, .stMarkdown, .stText, p, span, div, li {
  color: var(--text) !important;
  font-family: 'JetBrains Mono', monospace !important;
}

h1, h2, h3, h4 {
  font-family: 'Outfit', sans-serif !important;
  color: var(--text) !important;
}

/* ── Tabs ────────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
  background: var(--c1) !important;
  border: 1px solid var(--b1) !important;
  border-radius: 10px !important;
  padding: 4px !important;
  gap: 3px !important;
}
.stTabs [data-baseweb="tab"] {
  background: transparent !important;
  border-radius: 7px !important;
  color: var(--muted) !important;
  font-family: 'JetBrains Mono', monospace !important;
  font-size: 11px !important;
  letter-spacing: 0.5px !important;
  border: none !important;
  padding: 8px 12px !important;
}
.stTabs [aria-selected="true"] {
  background: var(--c3) !important;
  color: var(--green) !important;
  border: 1px solid var(--b2) !important;
}
.stTabs [data-baseweb="tab-highlight"] { display: none !important; }
.stTabs [data-baseweb="tab-border"]    { display: none !important; }

/* ── Input box ───────────────────────────────────────────────── */
.stTextInput input {
  background: var(--c1) !important;
  border: 1px solid var(--b2) !important;
  border-radius: 8px !important;
  color: var(--text) !important;
  font-family: 'JetBrains Mono', monospace !important;
  font-size: 13px !important;
  caret-color: var(--green) !important;
}
.stTextInput input:focus {
  border-color: var(--green) !important;
  box-shadow: 0 0 0 1px rgba(0,232,122,0.15) !important;
}

/* ── Buttons ─────────────────────────────────────────────────── */
.stButton > button {
  background: var(--green) !important;
  color: #000 !important;
  border: none !important;
  border-radius: 8px !important;
  font-family: 'Outfit', sans-serif !important;
  font-weight: 700 !important;
  font-size: 13px !important;
  padding: 10px 22px !important;
  transition: all 0.15s !important;
}
.stButton > button:hover {
  background: #1fffa0 !important;
  transform: translateY(-1px) !important;
}
.stButton > button[kind="secondary"] {
  background: var(--c1) !important;
  color: var(--text) !important;
  border: 1px solid var(--b2) !important;
}

/* ── Metrics ─────────────────────────────────────────────────── */
[data-testid="stMetric"] {
  background: var(--c1) !important;
  border: 1px solid var(--b1) !important;
  border-radius: 10px !important;
  padding: 14px 16px !important;
}
[data-testid="stMetricLabel"] {
  color: var(--muted) !important;
  font-size: 10px !important;
  letter-spacing: 1.5px !important;
}
[data-testid="stMetricValue"] {
  color: var(--green) !important;
  font-family: 'Outfit', sans-serif !important;
  font-weight: 700 !important;
}

/* ── Expanders ───────────────────────────────────────────────── */
.streamlit-expanderHeader {
  background: var(--c1) !important;
  border: 1px solid var(--b1) !important;
  border-radius: 8px !important;
  color: var(--text) !important;
  font-size: 12px !important;
}
.streamlit-expanderContent {
  background: var(--c2) !important;
  border: 1px solid var(--b1) !important;
  border-top: none !important;
  border-radius: 0 0 8px 8px !important;
}

/* ── Selectbox ───────────────────────────────────────────────── */
.stSelectbox [data-baseweb="select"] > div {
  background: var(--c1) !important;
  border: 1px solid var(--b2) !important;
  border-radius: 8px !important;
  color: var(--text) !important;
}

/* ── Progress bar ────────────────────────────────────────────── */
.stProgress > div > div {
  background: linear-gradient(90deg, var(--green), var(--blue)) !important;
  border-radius: 4px !important;
}
.stProgress > div {
  background: var(--b1) !important;
  border-radius: 4px !important;
}

/* ── Alerts ──────────────────────────────────────────────────── */
.stAlert {
  background: var(--c1) !important;
  border: 1px solid var(--b2) !important;
  border-radius: 8px !important;
}

/* ── Divider ─────────────────────────────────────────────────── */
hr { border-color: var(--b1) !important; }

/* ── Scrollbar ───────────────────────────────────────────────── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--b3); border-radius: 3px; }

/* ── Sidebar ─────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
  background: var(--c1) !important;
  border-right: 1px solid var(--b1) !important;
}
[data-testid="stSidebar"] * { color: var(--text) !important; }
</style>
"""


def node_badge(label: str, layer: str) -> str:
    """Return an inline HTML badge styled for an architecture node."""
    colors = {
        "entry":   ("#00e87a", "rgba(0,232,122,0.08)",   "rgba(0,232,122,0.3)"),
        "ctrl":    ("#a67cff", "rgba(166,124,255,0.08)", "rgba(166,124,255,0.3)"),
        "service": ("#4b9eff", "rgba(75,158,255,0.08)",  "rgba(75,158,255,0.3)"),
        "data":    ("#ff8f3c", "rgba(255,143,60,0.08)",  "rgba(255,143,60,0.3)"),
        "util":    ("#ffd166", "rgba(255,209,102,0.08)", "rgba(255,209,102,0.3)"),
        "ext":     ("#888",    "rgba(80,80,120,0.08)",   "rgba(80,80,120,0.3)"),
    }
    color, bg, border = colors.get(layer, colors["ctrl"])
    return (
        f'<span style="display:inline-flex;align-items:center;gap:5px;'
        f'padding:4px 10px;border-radius:5px;font-size:11px;border:1px solid {border};'
        f'color:{color};background:{bg};margin:3px;white-space:nowrap;cursor:default;">'
        f'<span style="width:5px;height:5px;border-radius:50%;background:{color};'
        f'flex-shrink:0;display:inline-block"></span>'
        f'{label}</span>'
    )


def method_badge(http_method: str) -> str:
    """Return a coloured HTTP method badge."""
    colors = {
        "GET":    ("#00e87a", "rgba(0,232,122,0.1)"),
        "POST":   ("#a67cff", "rgba(166,124,255,0.1)"),
        "PUT":    ("#ff8f3c", "rgba(255,143,60,0.1)"),
        "DELETE": ("#ff4d6a", "rgba(255,77,106,0.1)"),
        "PATCH":  ("#4b9eff", "rgba(75,158,255,0.1)"),
        "USE":    ("#888",    "rgba(80,80,120,0.1)"),
        "URL":    ("#00d4ff", "rgba(0,212,255,0.07)"),
        "HANDLE": ("#00d4ff", "rgba(0,212,255,0.07)"),
    }
    color, bg = colors.get(http_method.upper(), ("#888", "rgba(80,80,120,0.1)"))
    return (
        f'<span style="font-size:9px;font-weight:700;letter-spacing:0.5px;'
        f'padding:2px 6px;border-radius:3px;color:{color};background:{bg};'
        f'flex-shrink:0;margin-top:1px;">{http_method}</span>'
    )


def tag_html(label: str, color: str = "green") -> str:
    """Small coloured tag badge."""
    c_map = {
        "green":  ("#00e87a", "rgba(0,232,122,0.06)",   "rgba(0,232,122,0.25)"),
        "blue":   ("#4b9eff", "rgba(75,158,255,0.06)",  "rgba(75,158,255,0.25)"),
        "purple": ("#a67cff", "rgba(166,124,255,0.06)", "rgba(166,124,255,0.25)"),
        "yellow": ("#ffd166", "rgba(255,209,102,0.06)", "rgba(255,209,102,0.25)"),
        "orange": ("#ff8f3c", "rgba(255,143,60,0.06)",  "rgba(255,143,60,0.25)"),
    }
    tc, bg, border = c_map.get(color, c_map["green"])
    return (
        f'<span style="font-size:9px;padding:3px 8px;border-radius:3px;'
        f'border:1px solid {border};color:{tc};background:{bg};'
        f'letter-spacing:0.4px;margin:2px;">{label}</span>'
    )


def card_html(title: str, accent: str, body: str) -> str:
    """Return a styled card HTML block."""
    return f"""
    <div style="background:#0d0d1a;border:1px solid #1a1a2e;border-radius:11px;
                overflow:hidden;margin-bottom:13px;">
      <div style="display:flex;align-items:center;justify-content:space-between;
                  padding:9px 15px;border-bottom:1px solid #1a1a2e;
                  font-size:9px;letter-spacing:2px;color:#505070;">
        <span>{title}</span>
        <span style="color:#00e87a">{accent}</span>
      </div>
      <div style="padding:13px 15px;">{body}</div>
    </div>"""
