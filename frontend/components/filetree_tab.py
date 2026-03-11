"""
RepoLens — File Tree Tab
REBUILT: No st.expander at all — uses pure HTML <details>/<summary> accordion.
This completely eliminates the Streamlit arrow-icon bleed bug on mobile.
"""
from __future__ import annotations
import html as hl
import streamlit as st
from backend.analyzers.analysis_engine import AnalysisResult


EXT_ICON = {
    "py": "🐍", "js": "📜", "ts": "📘", "tsx": "📘", "jsx": "📜",
    "go": "🐹", "rs": "🦀", "java": "☕", "rb": "💎", "php": "🐘",
    "json": "📋", "md": "📝", "yml": "⚙", "yaml": "⚙",
    "sh": "🔧", "toml": "⚙", "txt": "📄", "env": "⚙",
}

# Inject <details> styling once
DETAILS_CSS = """
<style>
details.rl-dir {
  background: #0d0d1a;
  border: 1px solid #1a1a2e;
  border-radius: 8px;
  margin-bottom: 6px;
  overflow: hidden;
}
details.rl-dir summary {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  cursor: pointer;
  font-size: 12px;
  color: #dde0f5;
  list-style: none;
  user-select: none;
}
details.rl-dir summary::-webkit-details-marker { display: none; }
details.rl-dir summary::marker { display: none; }
details.rl-dir[open] summary { border-bottom: 1px solid #1a1a2e; }
details.rl-dir summary .rl-arrow {
  color: #505070;
  font-size: 10px;
  transition: transform 0.15s;
  flex-shrink: 0;
  display: inline-block;
}
details.rl-dir[open] summary .rl-arrow { transform: rotate(90deg); }
details.rl-dir summary .rl-dname { color: #4b9eff; font-weight: 600; flex: 1; }
details.rl-dir summary .rl-meta  { color: #505070; font-size: 10px; flex-shrink: 0; }
details.rl-dir .rl-body { padding: 6px 14px 10px; }
.rl-file-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 5px 0;
  border-bottom: 1px dashed #17172a;
  font-size: 11px;
  min-width: 0;
}
.rl-file-row:last-child { border-bottom: none; }
.rl-fname { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; min-width: 0; }
.rl-ext   { font-size: 9px; padding: 1px 5px; border-radius: 3px;
            background: #17172a; color: #505070; flex-shrink: 0; }
.rl-chk   { font-size: 10px; color: #00e87a; flex-shrink: 0; }
</style>
"""


def render_file_tree(result: AnalysisResult) -> None:
    all_files    = result.all_files
    analyzed_set = set(result.analyzed_files.keys())

    # Header
    st.markdown(
        f'<div style="font-size:9px;letter-spacing:2px;color:#505070;margin-bottom:12px">'
        f'REPOSITORY FILE TREE &nbsp;—&nbsp; '
        f'<span style="color:#dde0f5">{len(all_files)}</span> total &nbsp;·&nbsp; '
        f'<span style="color:#00e87a">{len(analyzed_set)}</span> analyzed</div>',
        unsafe_allow_html=True,
    )

    # Build directory map
    dirs: dict[str, list[str]] = {}
    for f in all_files:
        parts = f.split("/")
        d = parts[0] if len(parts) > 1 else "(root)"
        dirs.setdefault(d, []).append(f)

    # Inject CSS once
    st.markdown(DETAILS_CSS, unsafe_allow_html=True)

    # Render each directory as a native <details> block
    AUTO_OPEN = {"(root)", "src", "app", "lib", "backend", "frontend"}

    for dir_name in sorted(dirs.keys())[:30]:
        files           = dirs[dir_name]
        analyzed_in_dir = sum(1 for f in files if f in analyzed_set)
        is_open         = dir_name in AUTO_OPEN
        open_attr       = "open" if is_open else ""

        meta_txt = f"{len(files)} files"
        if analyzed_in_dir:
            meta_txt += f" · {analyzed_in_dir} analyzed"

        # File rows HTML
        rows_html = ""
        for f in sorted(files)[:25]:
            ext    = f.rsplit(".", 1)[-1].lower() if "." in f else ""
            icon   = EXT_ICON.get(ext, "📄")
            fname  = hl.escape(f.rsplit("/", 1)[-1])
            is_ana = f in analyzed_set
            color  = "#00e87a" if is_ana else "#dde0f5"
            chk    = '<span class="rl-chk">✓</span>' if is_ana else ""
            ext_b  = f'<span class="rl-ext">{ext.upper()}</span>' if ext else ""
            rows_html += (
                f'<div class="rl-file-row">'
                f'<span style="flex-shrink:0">{icon}</span>'
                f'<span class="rl-fname" style="color:{color}">{fname}</span>'
                f'{ext_b}{chk}'
                f'</div>'
            )

        if len(files) > 25:
            rows_html += (
                f'<div style="font-size:10px;color:#505070;padding:6px 0">'
                f'… {len(files) - 25} more files</div>'
            )

        dir_safe = hl.escape(dir_name)
        st.markdown(f"""
<details class="rl-dir" {open_attr}>
  <summary>
    <span class="rl-arrow">&#9654;</span>
    <span style="flex-shrink:0">📂</span>
    <span class="rl-dname">{dir_safe}/</span>
    <span class="rl-meta">{meta_txt}</span>
  </summary>
  <div class="rl-body">{rows_html}</div>
</details>""", unsafe_allow_html=True)
