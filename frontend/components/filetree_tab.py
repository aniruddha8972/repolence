"""
RepoLens — File Tree Tab Component
FIX: No emoji in expander labels (Streamlit arrow icon corrupts emoji on mobile).
FIX: All content properly contained with overflow handling.
"""
from __future__ import annotations
import html as html_lib
import streamlit as st
from backend.analyzers.analysis_engine import AnalysisResult


def render_file_tree(result: AnalysisResult) -> None:
    all_files    = result.all_files
    analyzed_set = set(result.analyzed_files.keys())

    st.markdown(
        f'<div style="font-size:9px;letter-spacing:2px;color:#505070;margin-bottom:14px">'
        f'REPOSITORY FILE TREE &nbsp;—&nbsp; '
        f'<span style="color:#dde0f5">{len(all_files)}</span> total &nbsp;·&nbsp; '
        f'<span style="color:#00e87a">{len(analyzed_set)}</span> analyzed</div>',
        unsafe_allow_html=True,
    )

    dirs: dict[str, list[str]] = {}
    for f in all_files:
        parts = f.split("/")
        d     = parts[0] if len(parts) > 1 else "(root)"
        dirs.setdefault(d, []).append(f)

    ext_icon = {
        "py": "🐍", "js": "📜", "ts": "📘", "tsx": "📘", "jsx": "📜",
        "go": "🐹", "rs": "🦀", "java": "☕", "rb": "💎", "php": "🐘",
        "json": "📋", "md": "📝", "yml": "⚙", "yaml": "⚙",
        "sh": "🔧", "toml": "⚙", "txt": "📄",
    }

    for dir_name, files in sorted(dirs.items())[:30]:
        analyzed_in_dir = sum(1 for f in files if f in analyzed_set)

        # KEY FIX: Plain text label only — no emoji, no special chars
        # Streamlit's expand arrow SVG overlaps emoji characters on mobile
        exp_label = f"{dir_name}/  [{len(files)} files{', ' + str(analyzed_in_dir) + ' analyzed' if analyzed_in_dir else ''}]"

        with st.expander(exp_label, expanded=(dir_name in ("(root)", "src", "app", "lib"))):

            # Safe place for folder icon — inside content area
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:8px;'
                f'padding:6px 0 10px;border-bottom:1px solid #1a1a2e;margin-bottom:6px">'
                f'<span style="font-size:15px">📂</span>'
                f'<span style="color:#4b9eff;font-size:12px;font-weight:600">'
                f'{html_lib.escape(dir_name)}/</span>'
                f'<span style="color:#505070;font-size:10px">{len(files)} files'
                f'{", " + str(analyzed_in_dir) + " analyzed" if analyzed_in_dir else ""}'
                f'</span></div>',
                unsafe_allow_html=True,
            )

            rows_html = ""
            for f in sorted(files)[:25]:
                ext    = f.rsplit(".", 1)[-1].lower() if "." in f else ""
                icon   = ext_icon.get(ext, "📄")
                fname  = html_lib.escape(f.rsplit("/", 1)[-1])
                is_ana = f in analyzed_set
                color  = "#00e87a" if is_ana else "#dde0f5"
                status = (
                    '<span style="font-size:9px;color:#00e87a;flex-shrink:0">✓</span>'
                    if is_ana else '<span></span>'
                )
                ext_badge = (
                    f'<span style="font-size:9px;padding:1px 5px;border-radius:3px;'
                    f'background:#17172a;color:#505070;flex-shrink:0">{ext.upper()}</span>'
                    if ext else ""
                )
                rows_html += (
                    f'<div style="display:flex;align-items:center;gap:7px;padding:5px 0;'
                    f'border-bottom:1px dashed #17172a;min-width:0;">'
                    f'<span style="flex-shrink:0">{icon}</span>'
                    f'<span style="flex:1;overflow:hidden;text-overflow:ellipsis;'
                    f'white-space:nowrap;color:{color};min-width:0;">{fname}</span>'
                    f'{ext_badge}{status}'
                    f'</div>'
                )

            if len(files) > 25:
                rows_html += (
                    f'<div style="font-size:10px;color:#505070;padding:6px 0">'
                    f'... {len(files) - 25} more files</div>'
                )

            st.markdown(
                f'<div style="font-family:JetBrains Mono,monospace;">{rows_html}</div>',
                unsafe_allow_html=True,
            )
