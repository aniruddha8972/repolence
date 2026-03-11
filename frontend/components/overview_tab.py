"""
RepoLens — Overview Tab Component
"""
from __future__ import annotations
import streamlit as st
from backend.analyzers.analysis_engine import AnalysisResult
from frontend.styles.theme import tag_html, card_html


def render_overview(result: AnalysisResult) -> None:
    meta  = result.meta
    stack = result.stack

    # ── Top metric row ────────────────────────────────────────────────
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("📁 Total Files",  result.file_stats["total"])
    c2.metric("💻 Code Files",   result.file_stats["code"])
    c3.metric("✅ Analyzed",     result.n_files_analyzed)
    c4.metric("⚙ Functions",    result.n_functions)
    c5.metric("🏛 Classes",      result.n_classes)
    c6.metric("🔗 Routes",       result.n_routes)

    st.markdown("")

    left, right = st.columns([3, 2])

    # ── Left column ───────────────────────────────────────────────────
    with left:
        # Description
        desc = (
            meta.description
            or next(
                (l.strip() for l in result.readme.splitlines()
                 if l.strip() and not l.startswith("#") and not l.startswith("!") and len(l) > 30),
                "No description available.",
            )
        )
        tags_html = "".join([
            tag_html(stack.language, "green") if stack.language else "",
            tag_html(stack.framework, "green") if stack.framework else "",
            tag_html(stack.runtime, "blue") if stack.runtime and stack.runtime != stack.language else "",
            *[tag_html(t, "purple") for t in stack.tools[:8]],
        ])
        st.markdown(card_html(
            "PROJECT SUMMARY",
            f"{stack.language}{' · ' + stack.framework if stack.framework else ''}",
            f'<div style="font-size:12px;line-height:1.9;margin-bottom:12px">{desc}</div>'
            f'<div style="display:flex;flex-wrap:wrap;gap:4px">{tags_html}</div>',
        ), unsafe_allow_html=True)

        # Repo stats
        repo_stats = [
            ("⭐", f"{meta.stars:,}",   "Stars"),
            ("🍴", f"{meta.forks:,}",   "Forks"),
            ("🐛", meta.open_issues,    "Open Issues"),
            ("👁", f"{meta.watchers:,}","Watchers"),
        ]
        cols = st.columns(4)
        for col, (icon, val, lbl) in zip(cols, repo_stats):
            col.metric(f"{icon} {lbl}", val)

        if meta.topics:
            topic_html = "".join(tag_html(t, "blue") for t in meta.topics[:10])
            st.markdown(
                f'<div style="display:flex;flex-wrap:wrap;gap:4px;margin-top:8px">{topic_html}</div>',
                unsafe_allow_html=True,
            )

        # Classes
        if result.classes:
            st.markdown("---")
            st.markdown(
                f'<div style="font-size:9px;letter-spacing:2px;color:#505070;margin-bottom:10px">'
                f'CLASSES DETECTED — {len(result.classes)} found</div>',
                unsafe_allow_html=True,
            )
            cls_cols = st.columns(min(3, len(result.classes[:6])))
            for idx, cls in enumerate(result.classes[:6]):
                with cls_cols[idx % len(cls_cols)]:
                    method_lines = "".join(
                        f'<div style="font-size:10px;color:#4b9eff;padding:2px 0;'
                        f'border-bottom:1px dashed #1a1a2e;">⚡ {m}()</div>'
                        for m in cls.methods[:8]
                    ) or '<div style="font-size:10px;color:#2a2a45">No methods detected</div>'
                    parent_line = (
                        f'<div style="font-size:9px;color:#505070;margin-bottom:4px">extends {cls.parent}</div>'
                        if cls.parent else ""
                    )
                    st.markdown(f"""
                    <div style="background:#111120;border:1px solid #1a1a2e;border-radius:8px;overflow:hidden;margin-bottom:8px">
                      <div style="display:flex;align-items:center;gap:7px;padding:8px 12px;
                                  background:#17172a;border-bottom:1px solid #1a1a2e">
                        <span>🏛</span>
                        <span style="color:#a67cff;font-weight:600;flex:1;font-size:11px;
                               overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{cls.name}</span>
                        <span style="font-size:9px;color:#505070">{cls.file.split('/')[-1]}</span>
                      </div>
                      <div style="padding:8px 12px">{parent_line}{method_lines}</div>
                    </div>""", unsafe_allow_html=True)

    # ── Right column ──────────────────────────────────────────────────
    with right:
        # Files list
        file_rows = "".join(
            f'<div style="display:flex;align-items:center;gap:6px;padding:5px 0;'
            f'border-bottom:1px solid #1a1a2e;font-size:11px">'
            f'<span>{"🐍" if f.endswith(".py") else "🐹" if f.endswith(".go") else "🦀" if f.endswith(".rs") else "📋" if f.endswith(".json") else "📝" if f.endswith(".md") else "📄"}</span>'
            f'<span style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{f}</span>'
            f'<span style="font-size:9px;padding:1px 5px;border-radius:3px;background:#17172a;color:#505070">'
            f'{f.rsplit(".", 1)[-1].upper() if "." in f else "FILE"}</span>'
            f'<span style="font-size:9px;color:#00e87a">✓</span>'
            f'</div>'
            for f in list(result.analyzed_files.keys())[:22]
        )
        st.markdown(card_html(
            "ANALYZED FILES",
            str(result.n_files_analyzed),
            file_rows,
        ), unsafe_allow_html=True)

        # NPM scripts
        if result.pkg and result.pkg.get("scripts"):
            script_rows = "".join(
                f'<div style="display:flex;gap:8px;padding:4px 0;border-bottom:1px solid #1a1a2e;font-size:11px">'
                f'<span style="color:#00e87a;width:80px;flex-shrink:0;overflow:hidden;'
                f'text-overflow:ellipsis;white-space:nowrap">{k}</span>'
                f'<span style="color:#505070;flex:1;overflow:hidden;'
                f'text-overflow:ellipsis;white-space:nowrap">{v}</span>'
                f'</div>'
                for k, v in list(result.pkg["scripts"].items())[:10]
            )
            st.markdown(card_html("NPM SCRIPTS", "", script_rows), unsafe_allow_html=True)
