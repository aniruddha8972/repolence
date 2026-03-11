"""
RepoLens — Call Flows Tab Component
FIX: HTML leaking into call steps — caused by Streamlit stripping partial HTML 
     inside expanders. Now builds entire chain as ONE html block per chain.
FIX: Expander labels use plain text only (no emoji) to avoid mobile rendering corruption.
"""
from __future__ import annotations
import html as html_lib
import streamlit as st
from backend.analyzers.analysis_engine import AnalysisResult
from config.settings import MAX_CALL_EDGES


def render_call_flows(result: AnalysisResult) -> None:
    chains     = result.chains
    call_edges = result.call_edges

    if not chains:
        st.info("No call chains detected for this repository.")
        return

    st.markdown(
        '<div style="font-size:9px;letter-spacing:2px;color:#505070;margin-bottom:14px">'
        'CALL CHAINS</div>',
        unsafe_allow_html=True,
    )

    for chain in chains:
        # KEY FIX: plain-text expander label only — no emoji, no HTML
        exp_label = f"{chain.name}  |  trigger: {chain.trigger}"

        with st.expander(exp_label, expanded=True):

            # Build the ENTIRE chain as one HTML block — avoids Streamlit
            # partial-rendering bug where per-step markdown calls leave
            # orphaned </div> tags visible as plain text.
            steps_html = ""
            for i, step in enumerate(chain.steps, 1):
                fn_safe   = html_lib.escape(step.fn)
                cls_safe  = html_lib.escape(step.cls)
                desc_safe = html_lib.escape(step.desc)

                # File label — skip synthetic markers
                if step.file in ("network", "routing", ""):
                    file_part = ""
                else:
                    file_safe = html_lib.escape(step.file.rsplit("/", 1)[-1])
                    file_part = (
                        f'<span style="color:#505070;font-size:10px;margin-left:6px">'
                        f'· {file_safe}</span>'
                    )

                cls_part = (
                    f'<span style="color:#4b9eff;font-size:10px;margin-left:4px">'
                    f'[{cls_safe}]</span>'
                    if cls_safe else ""
                )

                steps_html += f"""
                <div style="display:flex;align-items:flex-start;gap:10px;
                            padding:8px 0;border-bottom:1px dashed #1a1a2e;">
                  <div style="min-width:22px;height:22px;border-radius:50%;
                              background:#17172a;border:1px solid #22223a;
                              display:flex;align-items:center;justify-content:center;
                              font-size:9px;color:#505070;flex-shrink:0;margin-top:1px;">
                    {i}
                  </div>
                  <div style="min-width:0;flex:1;">
                    <div style="display:flex;align-items:baseline;flex-wrap:wrap;gap:2px;">
                      <span style="color:#a67cff;font-weight:600;font-size:12px;">{fn_safe}</span>
                      {cls_part}
                      {file_part}
                    </div>
                    <div style="color:#505070;font-size:10px;margin-top:3px;line-height:1.5;">
                      {desc_safe}
                    </div>
                  </div>
                </div>"""

            # Render entire chain as single markdown call
            st.markdown(
                f'<div style="font-family:JetBrains Mono,monospace;">{steps_html}</div>',
                unsafe_allow_html=True,
            )

    # ── Call graph edges ──────────────────────────────────────────────
    if call_edges:
        st.markdown("---")
        st.markdown(
            f'<div style="font-size:9px;letter-spacing:2px;color:#505070;margin-bottom:10px">'
            f'CALL GRAPH EDGES — {len(call_edges)} total'
            f' · showing {min(len(call_edges), MAX_CALL_EDGES)}</div>',
            unsafe_allow_html=True,
        )

        cols = st.columns(3)
        for idx, edge in enumerate(call_edges[:MAX_CALL_EDGES]):
            with cols[idx % 3]:
                caller    = html_lib.escape(edge.caller)
                callee    = html_lib.escape(edge.callee)
                file_short= html_lib.escape(edge.file.rsplit("/", 1)[-1])
                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:5px;padding:5px 9px;'
                    f'background:#111120;border:1px solid #1a1a2e;border-radius:6px;'
                    f'font-size:10px;margin-bottom:4px;overflow:hidden;">'
                    f'<span style="color:#a67cff;flex:1;overflow:hidden;'
                    f'text-overflow:ellipsis;white-space:nowrap;min-width:0;">{caller}</span>'
                    f'<span style="color:#2a2a45;flex-shrink:0;">&#8594;</span>'
                    f'<span style="color:#00e87a;flex:1;overflow:hidden;'
                    f'text-overflow:ellipsis;white-space:nowrap;min-width:0;">{callee}</span>'
                    f'<span style="color:#505070;font-size:9px;flex-shrink:0;'
                    f'max-width:70px;overflow:hidden;text-overflow:ellipsis;'
                    f'white-space:nowrap;">{file_short}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
