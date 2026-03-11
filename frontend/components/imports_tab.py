"""
RepoLens — Imports Tab Component
"""
from __future__ import annotations
import streamlit as st
from backend.analyzers.analysis_engine import AnalysisResult


def render_imports(result: AnalysisResult) -> None:
    imports = result.imports

    ext_imports = [i for i in imports if not i.local]
    loc_imports = [i for i in imports if i.local]

    # Count external packages
    pkg_count: dict[str, int] = {}
    for imp in ext_imports:
        pkg = (
            "/".join(imp.name.split("/")[:2]) if imp.name.startswith("@")
            else imp.name.split("/")[0]
        )
        pkg_count[pkg] = pkg_count.get(pkg, 0) + 1
    sorted_pkgs = sorted(pkg_count.items(), key=lambda x: -x[1])

    loc_uniq = list(dict.fromkeys(i.name for i in loc_imports))

    # ── Two-column package lists ──────────────────────────────────────
    ext_col, loc_col = st.columns(2)

    with ext_col:
        st.markdown(
            f'<div style="font-size:9px;letter-spacing:2px;color:#505070;margin-bottom:10px">'
            f'EXTERNAL PACKAGES — {len(sorted_pkgs)} unique</div>',
            unsafe_allow_html=True,
        )
        if sorted_pkgs:
            rows = ""
            for name, count in sorted_pkgs[:40]:
                rows += f"""
                <div style="display:flex;align-items:center;gap:7px;padding:5px 9px;
                            background:#111120;border:1px solid #1a1a2e;border-radius:6px;
                            font-size:11px;margin-bottom:4px">
                  <div style="width:5px;height:5px;border-radius:50%;background:#4b9eff;flex-shrink:0"></div>
                  <span style="flex:1;overflow:hidden;text-overflow:ellipsis;
                               white-space:nowrap;color:#dde0f5">{name}</span>
                  <span style="font-size:9px;color:#505070">{count}×</span>
                </div>"""
            st.markdown(rows, unsafe_allow_html=True)
        else:
            st.markdown('<div style="color:#505070;font-style:italic;font-size:11px">No external imports found</div>', unsafe_allow_html=True)

    with loc_col:
        st.markdown(
            f'<div style="font-size:9px;letter-spacing:2px;color:#505070;margin-bottom:10px">'
            f'LOCAL IMPORTS — {len(loc_uniq)} unique</div>',
            unsafe_allow_html=True,
        )
        if loc_uniq:
            rows = ""
            for name in loc_uniq[:40]:
                rows += f"""
                <div style="display:flex;align-items:center;gap:7px;padding:5px 9px;
                            background:#111120;border:1px solid #1a1a2e;border-radius:6px;
                            font-size:11px;margin-bottom:4px">
                  <div style="width:5px;height:5px;border-radius:50%;background:#00e87a;flex-shrink:0"></div>
                  <span style="flex:1;overflow:hidden;text-overflow:ellipsis;
                               white-space:nowrap;color:#dde0f5">{name}</span>
                </div>"""
            st.markdown(rows, unsafe_allow_html=True)
        else:
            st.markdown('<div style="color:#505070;font-style:italic;font-size:11px">No local imports found</div>', unsafe_allow_html=True)

    # ── Per-file import map ───────────────────────────────────────────
    st.markdown("---")
    st.markdown(
        f'<div style="font-size:9px;letter-spacing:2px;color:#505070;margin-bottom:10px">'
        f'IMPORT MAP — PER FILE</div>',
        unsafe_allow_html=True,
    )

    by_file: dict[str, list] = {}
    for imp in imports:
        by_file.setdefault(imp.file, []).append(imp)

    for file, imps in list(by_file.items())[:16]:
        badges = "".join(
            f'<span style="font-size:10px;padding:2px 7px;border-radius:3px;border:1px solid;margin:2px;'
            f'{"border-color:rgba(75,158,255,.2);color:#4b9eff;background:rgba(75,158,255,.05)" if not i.local else "border-color:rgba(0,232,122,.2);color:#00e87a;background:rgba(0,232,122,.05)"}">'
            f'{i.name}</span>'
            for i in imps[:18]
        )
        st.markdown(f"""
        <div style="margin-bottom:11px;padding-bottom:11px;border-bottom:1px solid #1a1a2e">
          <div style="font-size:11px;color:#dde0f5;margin-bottom:6px">📄 {file}</div>
          <div style="display:flex;flex-wrap:wrap;gap:3px">{badges}</div>
        </div>""", unsafe_allow_html=True)
