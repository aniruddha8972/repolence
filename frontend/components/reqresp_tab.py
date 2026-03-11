"""
RepoLens — Req/Resp Tab Component
"""
from __future__ import annotations
import streamlit as st
from backend.analyzers.analysis_engine import AnalysisResult
from frontend.styles.theme import method_badge


def render_req_resp(result: AnalysisResult) -> None:
    routes     = result.routes
    middleware = result.middleware
    stack      = result.stack

    # ── Route panels ─────────────────────────────────────────────────
    in_col, out_col = st.columns(2)

    def _route_rows(label: str) -> str:
        if not routes:
            return '<div style="color:#505070;font-size:11px;padding:20px 0;text-align:center;font-style:italic">No HTTP routes detected — this may be a library, CLI, or data-processing module.</div>'
        rows = ""
        for r in routes[:28]:
            badge  = method_badge(r.method)
            handler_txt = f" → {r.handler}" if r.handler else ""
            extra  = " · body expected" if label == "inbound" and r.method in ("POST", "PUT", "PATCH") else ""
            rows += f"""
            <div style="display:flex;align-items:flex-start;gap:7px;padding:5px 0;
                        border-bottom:1px solid #1a1a2e;font-size:11px">
              {badge}
              <div>
                <div style="color:#dde0f5;word-break:break-all">{r.path}</div>
                <div style="color:#505070;font-size:10px">{r.file.rsplit('/', 1)[-1]}{handler_txt}{extra}</div>
              </div>
            </div>"""
        return rows

    with in_col:
        st.markdown(f"""
        <div style="background:#0d0d1a;border:1px solid #1a1a2e;border-top:2px solid #00e87a;
                    border-radius:11px;overflow:hidden">
          <div style="padding:9px 15px;border-bottom:1px solid #1a1a2e;font-size:9px;
                      letter-spacing:2px;color:#00e87a">↑ INBOUND — {len(routes)} ROUTES</div>
          <div style="padding:11px 15px">{_route_rows('inbound')}</div>
        </div>""", unsafe_allow_html=True)

    with out_col:
        st.markdown(f"""
        <div style="background:#0d0d1a;border:1px solid #1a1a2e;border-top:2px solid #ff8f3c;
                    border-radius:11px;overflow:hidden">
          <div style="padding:9px 15px;border-bottom:1px solid #1a1a2e;font-size:9px;
                      letter-spacing:2px;color:#ff8f3c">↓ OUTBOUND / RESPONSE</div>
          <div style="padding:11px 15px">{_route_rows('outbound')}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("")

    # ── Info cards ────────────────────────────────────────────────────
    c1, c2, c3 = st.columns(3)
    info_cards = [
        (c1, "MIDDLEWARE STACK",
         "".join(f'<span style="display:inline-block;font-size:10px;padding:2px 7px;margin:2px;'
                 f'border:1px solid #22223a;border-radius:4px;color:#505070">{m}</span>'
                 for m in middleware) if middleware else "None detected"),
        (c2, "AUTHENTICATION",    stack.auth or "None detected"),
        (c3, "PROTOCOL / TRANSPORT", stack.protocol),
    ]
    for col, title, body in info_cards:
        with col:
            st.markdown(f"""
            <div style="background:#0d0d1a;border:1px solid #1a1a2e;border-radius:9px;padding:12px">
              <div style="font-size:9px;letter-spacing:2px;color:#505070;margin-bottom:7px">{title}</div>
              <div style="font-size:11px;line-height:1.9;color:#dde0f5">{body}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("")
    c4, c5, c6 = st.columns(3)
    route_files = list(dict.fromkeys(r.file.rsplit("/", 1)[-1] for r in routes))
    more_cards = [
        (c4, "ERROR HANDLING",   stack.error_handling),
        (c5, "UNIQUE ROUTES",    str(len(routes))),
        (c6, "ROUTE FILES",      ", ".join(route_files[:5]) or "N/A"),
    ]
    for col, title, body in more_cards:
        with col:
            st.markdown(f"""
            <div style="background:#0d0d1a;border:1px solid #1a1a2e;border-radius:9px;padding:12px">
              <div style="font-size:9px;letter-spacing:2px;color:#505070;margin-bottom:7px">{title}</div>
              <div style="font-size:11px;line-height:1.9;color:#dde0f5">{body}</div>
            </div>""", unsafe_allow_html=True)
