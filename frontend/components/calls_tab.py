"""
RepoLens — Call Flows Tab Component
"""
from __future__ import annotations
import streamlit as st
from backend.analyzers.analysis_engine import AnalysisResult
from config.settings import MAX_CALL_EDGES


def render_call_flows(result: AnalysisResult) -> None:
    chains     = result.chains
    call_edges = result.call_edges

    if not chains:
        st.info("No call chains detected for this repository.")
        return

    # ── Call chains ───────────────────────────────────────────────────
    st.markdown(
        '<div style="font-size:9px;letter-spacing:2px;color:#505070;'
        'margin-bottom:12px">CALL CHAINS</div>',
        unsafe_allow_html=True,
    )

    for chain in chains:
        with st.expander(f"⬡  {chain.name}  —  trigger: {chain.trigger}", expanded=True):
            for i, step in enumerate(chain.steps, 1):
                file_lbl = (
                    step.file.rsplit("/", 1)[-1]
                    if step.file not in ("network", "routing")
                    else step.file
                )
                cls_html = (
                    f'<span style="color:#4b9eff;font-size:10px;margin-left:4px">[{step.cls}]</span>'
                    if step.cls else ""
                )
                file_html = (
                    f'<span style="color:#505070;font-size:10px;margin-left:6px">· {file_lbl}</span>'
                    if file_lbl not in ("network", "routing") else ""
                )
                st.markdown(f"""
                <div style="display:flex;align-items:flex-start;gap:9px;padding:6px 0;
                            border-bottom:1px dashed #1a1a2e">
                  <div style="width:19px;height:19px;border-radius:50%;
                              background:#17172a;border:1px solid #22223a;
                              display:grid;place-items:center;font-size:9px;
                              color:#505070;flex-shrink:0;margin-top:1px">{i}</div>
                  <div>
                    <div>
                      <span style="color:#a67cff;font-weight:600;font-size:11px">{step.fn}</span>
                      {cls_html}{file_html}
                    </div>
                    <div style="color:#505070;font-size:10px;margin-top:2px">{step.desc}</div>
                  </div>
                </div>""", unsafe_allow_html=True)

    # ── Call graph edges ──────────────────────────────────────────────
    if call_edges:
        st.markdown("---")
        st.markdown(
            f'<div style="font-size:9px;letter-spacing:2px;color:#505070;margin-bottom:10px">'
            f'CALL GRAPH EDGES — {len(call_edges)} total · showing {min(len(call_edges), MAX_CALL_EDGES)}</div>',
            unsafe_allow_html=True,
        )
        # Show in a 3-column grid
        rows_per_col = (min(len(call_edges), MAX_CALL_EDGES) + 2) // 3
        cols         = st.columns(3)
        for idx, edge in enumerate(call_edges[:MAX_CALL_EDGES]):
            with cols[idx % 3]:
                file_short = edge.file.rsplit("/", 1)[-1]
                st.markdown(f"""
                <div style="display:flex;align-items:center;gap:5px;padding:5px 9px;
                            background:#111120;border:1px solid #1a1a2e;border-radius:6px;
                            font-size:10px;margin-bottom:4px">
                  <span style="color:#a67cff;flex:1;overflow:hidden;
                               text-overflow:ellipsis;white-space:nowrap">{edge.caller}</span>
                  <span style="color:#2a2a45">→</span>
                  <span style="color:#00e87a;flex:1;overflow:hidden;
                               text-overflow:ellipsis;white-space:nowrap">{edge.callee}</span>
                  <span style="color:#505070;font-size:9px;flex-shrink:0;
                               max-width:70px;overflow:hidden;text-overflow:ellipsis;
                               white-space:nowrap">{file_short}</span>
                </div>""", unsafe_allow_html=True)
