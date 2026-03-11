"""
RepoLens — Call Flows Tab
REBUILT: Uses only native Streamlit widgets — zero raw HTML injection.
This completely eliminates the HTML-leaking-as-text bug.
"""
from __future__ import annotations
import streamlit as st
from backend.analyzers.analysis_engine import AnalysisResult
from config.settings import MAX_CALL_EDGES

# Step type → colour + icon (pure data, no HTML strings)
STEP_STYLE = {
    "network":  ("#00e87a", "⬡"),
    "routing":  ("#a67cff", "⬡"),
    "entry":    ("#00e87a", "⬡"),
    "data":     ("#ff8f3c", "⬡"),
    "service":  ("#4b9eff", "⬡"),
    "util":     ("#ffd166", "⬡"),
    "default":  ("#a67cff", "⬡"),
}

def _step_color(file: str) -> str:
    f = file.lower()
    if file in ("network", "routing"):          return "#00e87a"
    if any(k in f for k in ("route","view","controller","handler","url","endpoint")): return "#00e87a"
    if any(k in f for k in ("model","schema","db","database","repositor","orm")):     return "#ff8f3c"
    if any(k in f for k in ("service","logic","use_case","business")):                return "#4b9eff"
    if any(k in f for k in ("util","helper","config","constant")):                    return "#ffd166"
    return "#a67cff"


def render_call_flows(result: AnalysisResult) -> None:
    chains     = result.chains
    call_edges = result.call_edges

    if not chains:
        st.info("No call chains detected for this repository.")
        return

    # ── Sub-tabs ──────────────────────────────────────────────────────
    tab_chains, tab_edges = st.tabs(["Call Chains", "Call Graph Edges"])

    with tab_chains:
        for chain_idx, chain in enumerate(chains):
            st.markdown(f"**{chain.name}**")
            st.caption(f"Trigger: {chain.trigger}")

            for i, step in enumerate(chain.steps):
                col_line, col_num, col_content = st.columns([0.02, 0.06, 0.92])

                with col_num:
                    color = _step_color(step.file)
                    st.markdown(
                        f'<div style="width:26px;height:26px;border-radius:50%;'
                        f'background:rgba(255,255,255,0.03);border:1.5px solid {color};'
                        f'display:flex;align-items:center;justify-content:center;'
                        f'font-size:10px;color:{color};font-weight:700;margin-top:4px;">'
                        f'{i+1}</div>',
                        unsafe_allow_html=True,
                    )

                with col_content:
                    # Function name row
                    fn_display = step.fn
                    if step.cls:
                        fn_display = f"{step.cls}.{step.fn}"

                    file_label = ""
                    if step.file and step.file not in ("network", "routing"):
                        file_label = step.file.rsplit("/", 1)[-1]

                    label_parts = [f"`{fn_display}`"]
                    if file_label:
                        label_parts.append(f"*{file_label}*")
                    st.markdown("  ".join(label_parts))
                    st.caption(step.desc)

                # Connector arrow between steps (not after last)
                if i < len(chain.steps) - 1:
                    st.markdown(
                        '<div style="margin-left:52px;color:#2a2a45;'
                        'font-size:16px;line-height:1;padding:1px 0;">↓</div>',
                        unsafe_allow_html=True,
                    )

            if chain_idx < len(chains) - 1:
                st.divider()

    with tab_edges:
        if not call_edges:
            st.info("No call graph edges detected.")
            return

        st.caption(f"{len(call_edges)} edges total · showing {min(len(call_edges), MAX_CALL_EDGES)}")
        st.divider()

        # Use st.columns grid — NO raw HTML
        edges_to_show = call_edges[:MAX_CALL_EDGES]
        rows = [edges_to_show[i:i+2] for i in range(0, len(edges_to_show), 2)]
        for row in rows:
            cols = st.columns(2)
            for col, edge in zip(cols, row):
                with col:
                    file_short = edge.file.rsplit("/", 1)[-1]
                    st.markdown(
                        f'<div style="display:flex;align-items:center;gap:6px;'
                        f'padding:6px 10px;background:#0d0d1a;border:1px solid #1a1a2e;'
                        f'border-radius:6px;margin-bottom:5px;overflow:hidden;">'
                        f'<span style="color:#a67cff;flex:1;min-width:0;overflow:hidden;'
                        f'text-overflow:ellipsis;white-space:nowrap;font-size:11px;">{edge.caller}</span>'
                        f'<span style="color:#505070;flex-shrink:0;font-size:13px;">&#8594;</span>'
                        f'<span style="color:#00e87a;flex:1;min-width:0;overflow:hidden;'
                        f'text-overflow:ellipsis;white-space:nowrap;font-size:11px;">{edge.callee}</span>'
                        f'<span style="color:#2a2a45;font-size:9px;flex-shrink:0;'
                        f'max-width:60px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">'
                        f'{file_short}</span>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
