"""
RepoLens — Architecture Tab Component
"""
from __future__ import annotations
import streamlit as st
from backend.analyzers.analysis_engine import AnalysisResult
from frontend.styles.theme import node_badge
from config.settings import ARCH_LAYERS


def render_architecture(result: AnalysisResult) -> None:
    arch  = result.arch
    stack = result.stack

    # Header info
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(
            f'<div style="font-family:Outfit,sans-serif;font-weight:700;font-size:18px;'
            f'margin-bottom:4px">System Architecture</div>'
            f'<div style="font-size:11px;color:#505070">'
            f'Language: <span style="color:#00e87a">{stack.language}</span>'
            f'{" · Framework: <span style=color:#00e87a>" + stack.framework + "</span>" if stack.framework else ""}'
            f' · <span style="color:#00e87a">{result.n_files_analyzed}</span> files analyzed'
            f'</div>',
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f'<div style="text-align:right;font-size:10px;color:#505070;margin-top:8px">'
            f'{result.n_functions} functions · {result.n_classes} classes</div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # ── Layered architecture diagram ─────────────────────────────────
    for layer in arch.layers:
        cfg    = ARCH_LAYERS.get(layer.key, ARCH_LAYERS["ext"])
        color  = cfg["color"]
        bg     = cfg["bg"]
        border = cfg["border"]

        node_count = len(layer.nodes)
        if node_count == 0 and layer.key == "ext":
            continue  # skip ext if truly empty

        # Build node badges HTML
        nodes_html = (
            "".join(node_badge(n.label, layer.key) for n in layer.nodes)
            if layer.nodes
            else f'<span style="font-size:11px;color:#2a2a45;font-style:italic">'
                 f'— Nothing detected in analyzed files</span>'
        )

        st.markdown(f"""
        <div style="display:flex;min-height:70px;margin-bottom:3px">
          <div style="writing-mode:vertical-rl;transform:rotate(180deg);
                      width:34px;font-size:8px;letter-spacing:3px;
                      display:flex;align-items:center;justify-content:center;
                      flex-shrink:0;border-radius:7px 0 0 7px;padding:8px 0;
                      font-weight:700;font-family:'Outfit',sans-serif;
                      background:{bg};color:{color};
                      border:1px solid {border};border-right:none">
            {layer.label}
          </div>
          <div style="flex:1;padding:11px 15px;border-radius:0 7px 7px 0;
                      border:1px solid {border};background:{bg}">
            <div style="font-size:9px;color:#505070;margin-bottom:9px">
              {layer.desc}
              <span style="color:#2a2a45;margin-left:8px">· {node_count} nodes</span>
            </div>
            <div style="display:flex;flex-wrap:wrap">{nodes_html}</div>
          </div>
        </div>""", unsafe_allow_html=True)

    # ── Flow edges ────────────────────────────────────────────────────
    if arch.flows:
        st.markdown(
            '<div style="font-size:9px;letter-spacing:2px;color:#505070;'
            'margin:16px 0 9px;padding-bottom:7px;border-bottom:1px solid #1a1a2e">'
            'CONTROL &amp; DATA FLOWS</div>',
            unsafe_allow_html=True,
        )
        for flow in arch.flows:
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:10px;padding:8px 14px;
                        background:#111120;border:1px solid #1a1a2e;border-radius:7px;
                        margin-bottom:6px;font-size:11px;flex-wrap:wrap">
              <span style="color:#00e87a;font-weight:600">{flow.src}</span>
              <span style="color:#a67cff">→</span>
              <span style="color:#ff8f3c;font-weight:600">{flow.dst}</span>
              <span style="color:#2a2a45;font-size:9px;font-style:italic">{flow.desc}</span>
            </div>""", unsafe_allow_html=True)
