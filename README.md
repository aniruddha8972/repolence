# ⬡ RepoLens — Deep Architecture Analyzer

A production-ready Streamlit app that analyzes any public GitHub repository and maps its full architecture — classes, functions, routes, imports, and call chains — with no API keys required.

---

## 🗂 Project Structure

```
repolens/
├── app.py                          # Streamlit entry point
├── requirements.txt
├── .env.example
├── .streamlit/
│   └── config.toml                 # Streamlit theme & server config
│
├── config/
│   ├── __init__.py
│   └── settings.py                 # All constants & configuration
│
├── backend/
│   ├── __init__.py
│   ├── utils/
│   │   ├── github_client.py        # GitHub API + raw file fetching
│   │   └── file_selector.py        # Smart file scoring & selection
│   ├── parsers/
│   │   └── code_parser.py          # JS/TS/Python/Go/Rust parsers
│   └── analyzers/
│       ├── stack_detector.py       # Language / framework detection
│       ├── arch_builder.py         # Architecture model + call chains
│       └── analysis_engine.py      # Top-level orchestrator
│
├── frontend/
│   ├── styles/
│   │   └── theme.py                # CSS injection + HTML helpers
│   └── components/
│       ├── overview_tab.py
│       ├── arch_tab.py
│       ├── calls_tab.py
│       ├── reqresp_tab.py
│       ├── imports_tab.py
│       └── filetree_tab.py
│
└── tests/
    └── test_parsers.py             # Unit tests (pytest)
```

---

## 🚀 Quick Start

### 1. Clone & install
```bash
git clone https://github.com/yourname/repolens
cd repolens
pip install -r requirements.txt
```

### 2. (Optional) Add GitHub token
```bash
cp .env.example .env
# Edit .env and add GITHUB_TOKEN=ghp_xxxx
```

### 3. Run
```bash
streamlit run app.py
```

Open **http://localhost:8501** in your browser.

---

## ☁ Deploy to Streamlit Cloud

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Click **New app** → select your repo → set **Main file path** to `app.py`
4. (Optional) Add `GITHUB_TOKEN` in **Secrets** settings
5. Click **Deploy**

---

## 🔬 What It Analyzes

| Feature | Details |
|---|---|
| **Files** | Up to 60 source files, smart-scored by importance |
| **Languages** | JS, TS, JSX, TSX, Python, Go, Rust, Ruby, PHP, Java, C#, Swift, Kotlin |
| **Frameworks** | Express, Fastify, Koa, Next.js, NestJS, Flask, FastAPI, Django, Gin, and more |
| **Classes** | Full class hierarchy with methods, parent detection |
| **Functions** | All function/def/func declarations with file attribution |
| **Routes** | Express, Flask, FastAPI, Django, NestJS decorators, Gin |
| **Call Graph** | Function-to-function call edge detection |
| **Imports** | ES6, CommonJS, Python, Go, Rust — local + external |
| **Stack** | Language, framework, database, ORM, tools, auth method |

---

## ⚡ GitHub Rate Limits

| Scenario | Limit |
|---|---|
| No token | 60 requests/hour |
| With token | 5,000 requests/hour |
| Per analysis | ~5–15 requests |

Add your token via the sidebar or `.env` file.

---

## 🧪 Running Tests

```bash
pip install pytest
python -m pytest tests/ -v
```

---

## 📝 License

MIT
