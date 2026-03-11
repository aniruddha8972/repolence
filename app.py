"""
RepoEngineer — Main Streamlit Application
Run with: streamlit run app.py
"""
from __future__ import annotations

import logging
import sys
import os

import streamlit as st

sys.path.insert(0, os.path.dirname(__file__))

from config.settings import EXAMPLE_REPOS
from backend.analyzers.analysis_engine import run_analysis, ProgressUpdate
from frontend.styles.theme import GLOBAL_CSS
from frontend.components.overview_tab  import render_overview
from frontend.components.arch_tab      import render_architecture
from frontend.components.filetree_tab  import render_file_tree
from frontend.components.calls_tab     import render_call_flows
from frontend.components.reqresp_tab   import render_req_resp
from frontend.components.imports_tab   import render_imports
from frontend.components.diagram_tab   import render_diagram

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(name)s  %(message)s")

# ═══════════════════════════════════════════════════════════════════════
#  PAGE CONFIG
# ═══════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title = "RepoEngineer — Deep Architecture Analyzer",
    page_icon  = "⬡",
    layout     = "wide",
    initial_sidebar_state = "collapsed",
)
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════
#  NAV
# ═══════════════════════════════════════════════════════════════════════
nav_l, nav_r = st.columns([3, 1])
with nav_l:
    st.markdown("""
    <div style="display:flex;align-items:center;gap:10px;padding:6px 0 10px">
      <div style="width:30px;height:30px;border-radius:7px;
                  background:linear-gradient(135deg,#00e87a,#4b9eff);
                  display:grid;place-items:center;font-size:13px;flex-shrink:0">⬡</div>
      <span style="font-family:'Outfit',sans-serif;font-weight:900;font-size:20px;color:#dde0f5">
        Repo<span style="color:#00e87a">Engineer</span>
      </span>
    </div>""", unsafe_allow_html=True)
with nav_r:
    st.markdown("""
    <div style="display:flex;justify-content:flex-end;gap:8px;padding-top:12px">
      <span style="font-size:9px;letter-spacing:1.5px;color:#00e87a;
                   border:1px solid rgba(0,232,122,.25);border-radius:3px;
                   padding:3px 8px;background:rgba(0,232,122,.05)">DEEP ANALYSIS</span>
      <span style="font-size:9px;letter-spacing:1.5px;color:#505070;
                   border:1px solid #22223a;border-radius:3px;padding:3px 8px">
                   60 FILES · NO API KEY</span>
    </div>""", unsafe_allow_html=True)

st.markdown('<hr style="border-color:#1a1a2e;margin:0 0 20px">', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ═══════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("### Settings")
    github_token = st.text_input(
        "GitHub Token (optional)",
        type="password",
        help="Raises rate limit from 60 to 5,000 req/hr.",
        placeholder="ghp_xxxxxxxxxxxx",
    )
    st.markdown("---")
    st.markdown("**About RepoEngineer**")
    st.markdown("""
Fetches up to **60 source files** from any public GitHub repo
and runs deep analysis to extract:
- Classes, methods & inheritance
- Functions & call graph
- HTTP routes & middleware
- Imports & package map
- Architecture layer model
    """)
    st.markdown("---")
    st.markdown("**Rate Limits**")
    st.markdown("""
- No token: **60 req / hr**
- With token: **5,000 req / hr**
- Per analysis: ~5–15 requests
    """)

# ═══════════════════════════════════════════════════════════════════════
#  HERO
# ═══════════════════════════════════════════════════════════════════════
h_l, h_r = st.columns([3, 2])
with h_l:
    st.markdown("""
    <h1 style="font-family:'Outfit',sans-serif;font-weight:900;
               font-size:clamp(28px,3.5vw,52px);line-height:1.0;
               letter-spacing:-2px;margin-bottom:12px">
      Real Architecture.<br>
      <span style="background:linear-gradient(90deg,#00e87a,#4b9eff);
                   -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                   background-clip:text">Not Guesswork.</span>
    </h1>
    <p style="color:#505070;font-size:12px;line-height:1.9;max-width:500px">
      Drop a public GitHub URL — RepoEngineer fetches up to 60 source files, parses every
      class, function, import, route &amp; decorator, then maps a true layered architecture
      with interactive diagrams. Works for JS/TS, Python, Go, Rust &amp; more.
    </p>""", unsafe_allow_html=True)
with h_r:
    fc = st.columns(2)
    for col, (val, lbl) in zip(fc * 2, [("60", "FILES DEEP"), ("CLASS", "AWARE"), ("LIVE", "GITHUB"), ("0", "API KEYS")]):
        with col:
            st.markdown(f"""
            <div style="background:#0d0d1a;border:1px solid #1a1a2e;border-radius:9px;
                        padding:11px 13px;margin-bottom:7px">
              <div style="font-family:'Outfit',sans-serif;font-weight:800;
                          font-size:18px;color:#00e87a">{val}</div>
              <div style="font-size:9px;color:#505070;letter-spacing:1.5px;margin-top:2px">{lbl}</div>
            </div>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════
#  INPUT
# ═══════════════════════════════════════════════════════════════════════
st.markdown("")
in_col, btn_col = st.columns([5, 1])
with in_col:
    repo_url = st.text_input(
        "GitHub Repository URL",
        placeholder="https://github.com/owner/repository",
        label_visibility="collapsed",
    )
with btn_col:
    analyze_clicked = st.button("Analyze →", use_container_width=True)

# Example buttons — plain text labels to avoid Streamlit button rendering issues
st.markdown(
    '<div style="font-size:9px;color:#505070;letter-spacing:1px;margin-bottom:6px">'
    'TRY THESE REPOS:</div>',
    unsafe_allow_html=True,
)
ex_cols = st.columns(len(EXAMPLE_REPOS))
for col, (label, url) in zip(ex_cols, EXAMPLE_REPOS):
    with col:
        if st.button(label, key=f"ex_{label}", help=url):
            st.session_state["_prefill"] = url
            st.rerun()

if "_prefill" in st.session_state:
    repo_url = st.session_state.pop("_prefill")

st.markdown('<hr style="border-color:#1a1a2e;margin:16px 0">', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════
#  ANALYSIS
# ═══════════════════════════════════════════════════════════════════════
def _parse_url(url: str):
    import re
    m = re.search(r"github\.com/([^/\s]+)/([^/\s?#]+)", url.strip())
    if not m:
        return None, None
    return m.group(1), m.group(2).removesuffix(".git")


if analyze_clicked or ("result" in st.session_state and not analyze_clicked):

    if analyze_clicked:
        if not repo_url or not repo_url.strip():
            st.error("Please enter a GitHub repository URL.")
            st.stop()
        owner, repo = _parse_url(repo_url)
        if not owner:
            st.error("Invalid URL — expected: https://github.com/owner/repository")
            st.stop()

        # Progress UI
        prog_bar  = st.progress(0)
        status_tx = st.empty()
        step_tx   = st.empty()

        STEP_LABELS = [
            "Repo Info", "File Tree", "Fetch Files",
            "Deep Parse", "Build Graph", "Done",
        ]

        def on_progress(update: ProgressUpdate) -> None:
            prog_bar.progress(update.pct / 100)
            status_tx.markdown(
                f'<div style="font-size:11px;color:#dde0f5">{update.message}</div>',
                unsafe_allow_html=True,
            )
            # Plain text step indicators — no emoji in labels to avoid rendering issues
            steps_html = "".join(
                f'<span style="font-size:9px;padding:3px 9px;border-radius:20px;border:1px solid;'
                f'{"border-color:rgba(255,143,60,.4);color:#ff8f3c;background:rgba(255,143,60,.07)" if i == update.step else "border-color:rgba(0,232,122,.3);color:#00e87a;background:rgba(0,232,122,.06)" if i < update.step else "border-color:#1a1a2e;color:#505070"}">'
                f'{STEP_LABELS[i]}</span>'
                for i in range(6)
            )
            step_tx.markdown(
                f'<div style="display:flex;flex-wrap:wrap;gap:5px;margin-top:8px">{steps_html}</div>',
                unsafe_allow_html=True,
            )

        try:
            result = run_analysis(owner=owner, repo=repo,
                                  token=github_token or "", on_progress=on_progress)
            st.session_state["result"] = result
        except RuntimeError as exc:
            prog_bar.empty(); status_tx.empty(); step_tx.empty()
            st.error(f"{exc}")
            st.stop()
        except Exception as exc:
            prog_bar.empty(); status_tx.empty(); step_tx.empty()
            st.error(f"Unexpected error: {exc}")
            st.stop()

        prog_bar.empty(); status_tx.empty(); step_tx.empty()

    result = st.session_state.get("result")
    if not result:
        st.stop()

    meta  = result.meta
    stack = result.stack

    # Repo bar
    fw_pill = (
        f'<span style="font-size:10px;padding:3px 9px;border:1px solid #22223a;'
        f'border-radius:20px;color:#505070">framework <b style="color:#dde0f5">'
        f'{stack.framework}</b></span>'
        if stack.framework else ""
    )
    st.markdown(f"""
    <div style="display:flex;align-items:center;flex-wrap:wrap;gap:10px;
                background:#0d0d1a;border:1px solid #1a1a2e;border-radius:12px;
                padding:13px 17px;margin-bottom:16px">
      <div style="font-family:'Outfit',sans-serif;font-weight:700;font-size:15px;
                  flex:1;min-width:150px">
        <a href="https://github.com/{meta.owner}/{meta.repo}" target="_blank"
           style="color:#00e87a;text-decoration:none">
          {meta.owner}/{meta.repo}
        </a>
      </div>
      <span style="font-size:10px;padding:3px 9px;border:1px solid #22223a;border-radius:20px;color:#505070">stars <b style="color:#dde0f5">{meta.stars:,}</b></span>
      <span style="font-size:10px;padding:3px 9px;border:1px solid #22223a;border-radius:20px;color:#505070">forks <b style="color:#dde0f5">{meta.forks:,}</b></span>
      <span style="font-size:10px;padding:3px 9px;border:1px solid #22223a;border-radius:20px;color:#505070">lang <b style="color:#dde0f5">{stack.language or meta.language}</b></span>
      {fw_pill}
      <span style="font-size:10px;padding:3px 9px;border:1px solid #22223a;border-radius:20px;color:#505070">files <b style="color:#dde0f5">{len(result.all_files)}</b></span>
      <span style="font-size:10px;padding:3px 9px;border:1px solid rgba(0,232,122,.3);border-radius:20px;color:#00e87a">analyzed <b>{result.n_files_analyzed}</b></span>
      <span style="font-size:10px;padding:3px 9px;border:1px solid #22223a;border-radius:20px;color:#505070">fns <b style="color:#dde0f5">{result.n_functions}</b></span>
      <span style="font-size:10px;padding:3px 9px;border:1px solid #22223a;border-radius:20px;color:#505070">cls <b style="color:#dde0f5">{result.n_classes}</b></span>
      <span style="font-size:10px;padding:3px 9px;border:1px solid #22223a;border-radius:20px;color:#505070">routes <b style="color:#dde0f5">{result.n_routes}</b></span>
    </div>""", unsafe_allow_html=True)

    # Tabs — plain text labels only (no emoji) to prevent mobile rendering corruption
    (tab_ov, tab_diag, tab_arch, tab_files,
     tab_calls, tab_rr, tab_imp) = st.tabs([
        "Overview", "Diagrams", "Architecture",
        "File Tree", "Call Flows", "Req / Resp", "Imports",
    ])

    with tab_ov:
        render_overview(result)
    with tab_diag:
        render_diagram(result)
    with tab_arch:
        render_architecture(result)
    with tab_files:
        render_file_tree(result)
    with tab_calls:
        render_call_flows(result)
    with tab_rr:
        render_req_resp(result)
    with tab_imp:
        render_imports(result)
