"""
RepoLens — File Tree Tab Component
"""
from __future__ import annotations
import streamlit as st
from backend.analyzers.analysis_engine import AnalysisResult


def render_file_tree(result: AnalysisResult) -> None:
    all_files    = result.all_files
    analyzed_set = set(result.analyzed_files.keys())

    st.markdown(
        f'<div style="font-size:9px;letter-spacing:2px;color:#505070;margin-bottom:12px">'
        f'REPOSITORY FILE TREE — {len(all_files)} total files · '
        f'<span style="color:#00e87a">{len(analyzed_set)}</span> analyzed</div>',
        unsafe_allow_html=True,
    )

    # Build directory structure
    dirs: dict[str, list[str]] = {}
    for f in all_files:
        parts = f.split("/")
        d     = parts[0] if len(parts) > 1 else "(root)"
        dirs.setdefault(d, []).append(f)

    ext_icon = {
        "py": "🐍", "js": "📜", "ts": "📘", "go": "🐹",
        "rs": "🦀", "java": "☕", "rb": "💎", "php": "🐘",
        "json": "📋", "md": "📝", "yml": "⚙", "yaml": "⚙",
        "sh": "🔧", "dockerfile": "🐳",
    }

    for dir_name, files in sorted(dirs.items())[:30]:
        analyzed_in_dir = sum(1 for f in files if f in analyzed_set)
        with st.expander(
            f"📂 {dir_name}/  —  {len(files)} files"
            + (f" · {analyzed_in_dir} analyzed" if analyzed_in_dir else ""),
            expanded=(dir_name in ("(root)", "src", "app", "lib")),
        ):
            rows = ""
            for f in sorted(files)[:20]:
                ext     = f.rsplit(".", 1)[-1].lower() if "." in f else ""
                icon    = ext_icon.get(ext, "📄")
                fname   = f.rsplit("/", 1)[-1]
                is_ana  = f in analyzed_set
                color   = "#00e87a" if is_ana else "#dde0f5"
                dot     = "✅" if is_ana else "  "
                rows += f"""
                <div style="display:flex;align-items:center;gap:6px;padding:4px 0;
                            border-bottom:1px dashed #1a1a2e;font-size:11px">
                  <span>{dot}</span>
                  <span>{icon}</span>
                  <span style="flex:1;overflow:hidden;text-overflow:ellipsis;
                               white-space:nowrap;color:{color}">{fname}</span>
                  <span style="font-size:9px;color:#505070">{ext.upper() if ext else ""}</span>
                </div>"""
            if len(files) > 20:
                rows += f'<div style="font-size:10px;color:#505070;padding:4px 0">… {len(files)-20} more files</div>'
            st.markdown(rows, unsafe_allow_html=True)
