"""
RepoLens — Architecture Diagram Tab
Visual flow diagram using Plotly: shows files as nodes grouped by layer,
with arrows for data/control flow between them.
"""
from __future__ import annotations
import html as html_lib
import streamlit as st
import plotly.graph_objects as go

from backend.analyzers.analysis_engine import AnalysisResult
from config.settings import ARCH_LAYERS


# ── Layer layout config ────────────────────────────────────────────────────
# Each layer gets a vertical band. We lay them left→right.
LAYER_ORDER = ["entry", "ctrl", "service", "data", "util", "ext"]
LAYER_X = {k: i for i, k in enumerate(LAYER_ORDER)}

LAYER_COLORS = {
    "entry":   "#00e87a",
    "ctrl":    "#a67cff",
    "service": "#4b9eff",
    "data":    "#ff8f3c",
    "util":    "#ffd166",
    "ext":     "#888888",
}

BG_COLOR  = "#06060d"
CARD_BG   = "#0d0d1a"
GRID_COL  = "#1a1a2e"
TEXT_COL  = "#dde0f5"
MUTED_COL = "#505070"


def _build_node_positions(arch_layers) -> tuple[dict, dict, dict]:
    """
    Returns:
      node_pos  : {node_label: (x, y)}
      node_layer: {node_label: layer_key}
      node_file : {node_label: detail_str}
    """
    node_pos: dict[str, tuple[float, float]] = {}
    node_layer: dict[str, str] = {}
    node_file: dict[str, str] = {}

    for layer in arch_layers:
        lx = LAYER_X.get(layer.key, 0)
        nodes = layer.nodes
        n = len(nodes)
        if n == 0:
            continue
        # Space nodes vertically within their band
        for j, nd in enumerate(nodes):
            y = (j - (n - 1) / 2) * 1.2   # centre around 0, spacing 1.2
            node_pos[nd.label]   = (float(lx), float(y))
            node_layer[nd.label] = layer.key
            node_file[nd.label]  = nd.detail or ""

    return node_pos, node_layer, node_file


def _flow_edges(arch_layers):
    """Return list of (src_label, dst_label) for inter-layer flow arrows."""
    edges = []
    prev_nodes = None
    for layer in arch_layers:
        if not layer.nodes:
            continue
        if prev_nodes:
            # Connect last node of prev layer to first node of this layer
            edges.append((prev_nodes[-1].label, layer.nodes[0].label))
        prev_nodes = layer.nodes
    return edges


def build_arch_figure(result: AnalysisResult) -> go.Figure:
    arch   = result.arch
    chains = result.chains

    node_pos, node_layer, node_file = _build_node_positions(arch.layers)

    # ── Build Plotly traces ───────────────────────────────────────────
    traces = []

    # 1. Layer background bands
    for layer in arch.layers:
        lx = LAYER_X.get(layer.key, 0)
        cfg = ARCH_LAYERS.get(layer.key, {})
        color = cfg.get("color", "#888")
        traces.append(go.Scatter(
            x=[lx - 0.45, lx - 0.45, lx + 0.45, lx + 0.45, lx - 0.45],
            y=[-4.5, 4.5, 4.5, -4.5, -4.5],
            fill="toself",
            fillcolor=f"rgba({_hex_to_rgb(color)},0.04)",
            line=dict(color=f"rgba({_hex_to_rgb(color)},0.18)", width=1),
            mode="lines",
            hoverinfo="skip",
            showlegend=False,
        ))
        # Layer title at top
        traces.append(go.Scatter(
            x=[lx], y=[4.7],
            mode="text",
            text=[layer.label],
            textfont=dict(size=8, color=color, family="JetBrains Mono"),
            hoverinfo="skip",
            showlegend=False,
        ))

    # 2. Flow arrows between layers
    flow_edges = _flow_edges(arch.layers)
    for src, dst in flow_edges:
        if src not in node_pos or dst not in node_pos:
            continue
        sx, sy = node_pos[src]
        dx, dy = node_pos[dst]
        traces.append(go.Scatter(
            x=[sx + 0.46, dx - 0.46],
            y=[sy, dy],
            mode="lines",
            line=dict(color="rgba(166,124,255,0.35)", width=1.5, dash="dot"),
            hoverinfo="skip",
            showlegend=False,
        ))
        # Arrowhead
        traces.append(go.Scatter(
            x=[dx - 0.46], y=[dy],
            mode="markers",
            marker=dict(symbol="triangle-right", size=8, color="#a67cff"),
            hoverinfo="skip",
            showlegend=False,
        ))

    # 3. Call chain edges (from first chain, in a different colour)
    if chains and len(chains) > 0:
        chain = chains[0]
        for i in range(len(chain.steps) - 1):
            a = chain.steps[i].fn
            b = chain.steps[i + 1].fn
            if a in node_pos and b in node_pos:
                ax, ay = node_pos[a]
                bx, by = node_pos[b]
                traces.append(go.Scatter(
                    x=[ax, bx], y=[ay, by],
                    mode="lines",
                    line=dict(color="rgba(0,232,122,0.25)", width=1, dash="dash"),
                    hoverinfo="skip",
                    showlegend=False,
                ))

    # 4. Node scatter (all nodes as styled markers + labels)
    for label, (x, y) in node_pos.items():
        layer_key = node_layer.get(label, "ext")
        color     = LAYER_COLORS.get(layer_key, "#888")
        detail    = node_file.get(label, "")
        hover_txt = f"<b>{label}</b><br><span style='color:#888'>{detail}</span>"

        # Outer glow circle
        traces.append(go.Scatter(
            x=[x], y=[y],
            mode="markers",
            marker=dict(
                size=28,
                color=f"rgba({_hex_to_rgb(color)},0.10)",
                line=dict(color=f"rgba({_hex_to_rgb(color)},0.35)", width=1.5),
            ),
            hoverinfo="skip",
            showlegend=False,
        ))
        # Inner dot
        traces.append(go.Scatter(
            x=[x], y=[y],
            mode="markers+text",
            marker=dict(size=10, color=color),
            text=[_truncate(label, 12)],
            textposition="bottom center",
            textfont=dict(size=9, color=TEXT_COL, family="JetBrains Mono"),
            hovertext=hover_txt,
            hoverinfo="text",
            hoverlabel=dict(
                bgcolor=CARD_BG,
                bordercolor=color,
                font=dict(size=11, color=TEXT_COL, family="JetBrains Mono"),
            ),
            showlegend=False,
        ))

    # 5. Legend
    for layer_key, color in LAYER_COLORS.items():
        cfg = ARCH_LAYERS.get(layer_key, {})
        traces.append(go.Scatter(
            x=[None], y=[None],
            mode="markers",
            marker=dict(size=10, color=color),
            name=cfg.get("label", layer_key),
            showlegend=True,
        ))

    fig = go.Figure(data=traces)
    fig.update_layout(
        paper_bgcolor=BG_COLOR,
        plot_bgcolor=BG_COLOR,
        height=600,
        margin=dict(l=20, r=20, t=30, b=20),
        xaxis=dict(
            showgrid=False, zeroline=False, showticklabels=False,
            range=[-0.7, len(LAYER_ORDER) - 0.3],
        ),
        yaxis=dict(
            showgrid=False, zeroline=False, showticklabels=False,
            range=[-5.2, 5.2],
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom", y=1.01,
            xanchor="left",   x=0,
            font=dict(size=10, color=TEXT_COL, family="JetBrains Mono"),
            bgcolor="rgba(0,0,0,0)",
        ),
        hoverdistance=20,
        hovermode="closest",
    )
    return fig


def build_import_flow_figure(result: AnalysisResult) -> go.Figure:
    """
    Sankey-style diagram: source files → external packages.
    Shows which files import which packages.
    """
    imports = result.imports
    ext_imports = [i for i in imports if not i.local]

    # Collect unique files and packages
    files    = list(dict.fromkeys(i.file.rsplit("/", 1)[-1] for i in ext_imports))[:20]
    packages = list(dict.fromkeys(
        "/".join(i.name.split("/")[:2]) if i.name.startswith("@") else i.name.split("/")[0]
        for i in ext_imports
    ))[:20]

    if not files or not packages:
        return None

    file_idx = {f: i for i, f in enumerate(files)}
    pkg_idx  = {p: len(files) + i for i, p in enumerate(packages)}

    sources, targets, values = [], [], []
    edge_seen: dict[tuple, int] = {}
    for imp in ext_imports:
        f = imp.file.rsplit("/", 1)[-1]
        p = "/".join(imp.name.split("/")[:2]) if imp.name.startswith("@") else imp.name.split("/")[0]
        if f not in file_idx or p not in pkg_idx:
            continue
        key = (file_idx[f], pkg_idx[p])
        edge_seen[key] = edge_seen.get(key, 0) + 1

    for (s, t), v in edge_seen.items():
        sources.append(s)
        targets.append(t)
        values.append(v)

    if not sources:
        return None

    # Colour nodes
    file_colors = ["rgba(0,232,122,0.7)"] * len(files)
    pkg_colors  = ["rgba(75,158,255,0.7)"] * len(packages)

    fig = go.Figure(go.Sankey(
        arrangement="snap",
        node=dict(
            pad=18,
            thickness=16,
            line=dict(color=CARD_BG, width=0.5),
            label=files + packages,
            color=file_colors + pkg_colors,
            hovertemplate="<b>%{label}</b><br>%{value} imports<extra></extra>",
        ),
        link=dict(
            source=sources,
            target=targets,
            value=values,
            color="rgba(166,124,255,0.15)",
            hovertemplate="<b>%{source.label}</b> → <b>%{target.label}</b><br>%{value} import(s)<extra></extra>",
        ),
        textfont=dict(color=TEXT_COL, size=10, family="JetBrains Mono"),
    ))
    fig.update_layout(
        paper_bgcolor=BG_COLOR,
        height=500,
        margin=dict(l=10, r=10, t=10, b=10),
        font=dict(color=TEXT_COL, family="JetBrains Mono"),
    )
    return fig


def build_call_graph_figure(result: AnalysisResult) -> go.Figure:
    """
    Force-directed-style scatter plot of the call graph.
    Nodes = functions, edges = calls.
    """
    edges      = result.call_edges[:80]
    functions  = result.functions[:60]
    if not edges or not functions:
        return None

    # Assign each function a position in a circular layout
    import math
    fn_set   = list(dict.fromkeys([e.caller for e in edges] + [e.callee for e in edges]))
    n        = len(fn_set)
    fn_pos   = {}
    for i, fn in enumerate(fn_set):
        angle     = 2 * math.pi * i / max(n, 1)
        # Use two rings for readability
        r         = 3.0 if i % 2 == 0 else 1.8
        fn_pos[fn] = (r * math.cos(angle), r * math.sin(angle))

    # Count in-degree (how many functions call this one)
    in_degree: dict[str, int] = {}
    for e in edges:
        in_degree[e.callee] = in_degree.get(e.callee, 0) + 1

    traces = []

    # Edge lines
    for e in edges:
        if e.caller not in fn_pos or e.callee not in fn_pos:
            continue
        x0, y0 = fn_pos[e.caller]
        x1, y1 = fn_pos[e.callee]
        traces.append(go.Scatter(
            x=[x0, x1, None], y=[y0, y1, None],
            mode="lines",
            line=dict(color="rgba(166,124,255,0.2)", width=1),
            hoverinfo="skip",
            showlegend=False,
        ))

    # Node markers
    node_x = [fn_pos[fn][0] for fn in fn_set if fn in fn_pos]
    node_y = [fn_pos[fn][1] for fn in fn_set if fn in fn_pos]
    node_text = [_truncate(fn, 14) for fn in fn_set if fn in fn_pos]
    node_size = [10 + in_degree.get(fn, 0) * 4 for fn in fn_set if fn in fn_pos]
    node_color = [
        "#00e87a" if in_degree.get(fn, 0) >= 3
        else "#a67cff" if in_degree.get(fn, 0) >= 1
        else "#505070"
        for fn in fn_set if fn in fn_pos
    ]

    traces.append(go.Scatter(
        x=node_x, y=node_y,
        mode="markers+text",
        marker=dict(size=node_size, color=node_color,
                    line=dict(color=BG_COLOR, width=1.5)),
        text=node_text,
        textposition="top center",
        textfont=dict(size=8, color=TEXT_COL, family="JetBrains Mono"),
        hovertext=[f"<b>{fn}</b><br>called by {in_degree.get(fn,0)} fn(s)" for fn in fn_set if fn in fn_pos],
        hoverinfo="text",
        hoverlabel=dict(bgcolor=CARD_BG, bordercolor="#a67cff",
                        font=dict(size=11, color=TEXT_COL)),
        showlegend=False,
    ))

    fig = go.Figure(data=traces)
    fig.update_layout(
        paper_bgcolor=BG_COLOR,
        plot_bgcolor=BG_COLOR,
        height=520,
        margin=dict(l=20, r=20, t=20, b=20),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        hovermode="closest",
    )
    return fig


# ── Main render ───────────────────────────────────────────────────────────────
def render_diagram(result: AnalysisResult) -> None:

    # ── Tab sub-selector ──────────────────────────────────────────────
    d1, d2, d3 = st.tabs([
        "Architecture Map",
        "Import Flow (Sankey)",
        "Call Graph",
    ])

    # ── 1. Architecture Map ───────────────────────────────────────────
    with d1:
        st.markdown(
            '<div style="font-size:9px;letter-spacing:2px;color:#505070;margin-bottom:6px">'
            'LAYERED ARCHITECTURE — hover nodes for details</div>',
            unsafe_allow_html=True,
        )

        # Legend pills
        legend_html = ""
        for lk, color in LAYER_COLORS.items():
            cfg = ARCH_LAYERS.get(lk, {})
            legend_html += (
                f'<span style="display:inline-flex;align-items:center;gap:5px;'
                f'padding:3px 10px;border-radius:20px;border:1px solid rgba({_hex_to_rgb(color)},0.3);'
                f'color:{color};background:rgba({_hex_to_rgb(color)},0.07);'
                f'font-size:9px;margin:2px;">'
                f'<span style="width:6px;height:6px;border-radius:50%;'
                f'background:{color};display:inline-block;"></span>'
                f'{cfg.get("label", lk)}</span>'
            )
        st.markdown(
            f'<div style="display:flex;flex-wrap:wrap;gap:4px;margin-bottom:12px">'
            f'{legend_html}</div>',
            unsafe_allow_html=True,
        )

        fig_arch = build_arch_figure(result)
        st.plotly_chart(fig_arch, use_container_width=True, config={"displayModeBar": False})

        # Layer summary table
        st.markdown(
            '<div style="font-size:9px;letter-spacing:2px;color:#505070;'
            'margin:16px 0 8px">LAYER BREAKDOWN</div>',
            unsafe_allow_html=True,
        )
        layer_cols = st.columns(len(LAYER_ORDER))
        for col, layer in zip(layer_cols, result.arch.layers):
            cfg   = ARCH_LAYERS.get(layer.key, {})
            color = cfg.get("color", "#888")
            with col:
                st.markdown(
                    f'<div style="background:#0d0d1a;border:1px solid rgba({_hex_to_rgb(color)},0.25);'
                    f'border-top:2px solid {color};border-radius:8px;padding:10px;text-align:center">'
                    f'<div style="font-family:Outfit,sans-serif;font-weight:700;font-size:22px;'
                    f'color:{color}">{len(layer.nodes)}</div>'
                    f'<div style="font-size:9px;color:#505070;letter-spacing:1px;margin-top:2px">'
                    f'{layer.label}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

        # Node detail table
        st.markdown(
            '<div style="font-size:9px;letter-spacing:2px;color:#505070;'
            'margin:16px 0 8px">ALL NODES</div>',
            unsafe_allow_html=True,
        )
        for layer in result.arch.layers:
            if not layer.nodes:
                continue
            cfg   = ARCH_LAYERS.get(layer.key, {})
            color = cfg.get("color", "#888")
            node_pills = "".join(
                f'<span style="display:inline-flex;align-items:center;gap:4px;'
                f'padding:3px 9px;border-radius:4px;border:1px solid rgba({_hex_to_rgb(color)},0.3);'
                f'color:{color};background:rgba({_hex_to_rgb(color)},0.07);'
                f'font-size:10px;margin:3px;cursor:default;" title="{html_lib.escape(nd.detail or "")}">'
                f'<span style="width:5px;height:5px;border-radius:50%;background:{color};'
                f'display:inline-block;flex-shrink:0;"></span>'
                f'{html_lib.escape(nd.label)}</span>'
                for nd in layer.nodes
            )
            st.markdown(
                f'<div style="margin-bottom:10px;">'
                f'<div style="font-size:9px;color:#505070;letter-spacing:1px;margin-bottom:5px">'
                f'{layer.label} ({len(layer.nodes)})</div>'
                f'<div style="display:flex;flex-wrap:wrap;">{node_pills}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    # ── 2. Import Flow Sankey ─────────────────────────────────────────
    with d2:
        st.markdown(
            '<div style="font-size:9px;letter-spacing:2px;color:#505070;margin-bottom:6px">'
            'IMPORT FLOW — source files (green) to external packages (blue)</div>',
            unsafe_allow_html=True,
        )
        fig_sankey = build_import_flow_figure(result)
        if fig_sankey:
            st.plotly_chart(fig_sankey, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("Not enough import data to build the flow diagram.")

        # Summary stats
        imports    = result.imports
        ext_imp    = [i for i in imports if not i.local]
        loc_imp    = [i for i in imports if i.local]
        pkg_counts: dict[str, int] = {}
        for imp in ext_imp:
            pkg = "/".join(imp.name.split("/")[:2]) if imp.name.startswith("@") else imp.name.split("/")[0]
            pkg_counts[pkg] = pkg_counts.get(pkg, 0) + 1
        top5 = sorted(pkg_counts.items(), key=lambda x: -x[1])[:5]

        if top5:
            st.markdown(
                '<div style="font-size:9px;letter-spacing:2px;color:#505070;'
                'margin:14px 0 8px">TOP IMPORTED PACKAGES</div>',
                unsafe_allow_html=True,
            )
            bar_cols = st.columns(len(top5))
            for col, (pkg, cnt) in zip(bar_cols, top5):
                with col:
                    st.markdown(
                        f'<div style="background:#0d0d1a;border:1px solid #1a1a2e;'
                        f'border-radius:8px;padding:10px;text-align:center;">'
                        f'<div style="font-family:Outfit,sans-serif;font-weight:700;'
                        f'font-size:20px;color:#4b9eff">{cnt}</div>'
                        f'<div style="font-size:9px;color:#505070;margin-top:2px;'
                        f'overflow:hidden;text-overflow:ellipsis;white-space:nowrap">'
                        f'{html_lib.escape(pkg)}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

    # ── 3. Call Graph ─────────────────────────────────────────────────
    with d3:
        st.markdown(
            '<div style="font-size:9px;letter-spacing:2px;color:#505070;margin-bottom:6px">'
            'FUNCTION CALL GRAPH — node size = how often it is called · '
            'green = hotspot · purple = called · grey = leaf</div>',
            unsafe_allow_html=True,
        )
        fig_cg = build_call_graph_figure(result)
        if fig_cg:
            st.plotly_chart(fig_cg, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("Not enough call-graph data to render.")

        if result.call_edges:
            # Top callers table
            caller_cnt: dict[str, int] = {}
            for e in result.call_edges:
                caller_cnt[e.caller] = caller_cnt.get(e.caller, 0) + 1
            top_callers = sorted(caller_cnt.items(), key=lambda x: -x[1])[:10]

            st.markdown(
                '<div style="font-size:9px;letter-spacing:2px;color:#505070;'
                'margin:14px 0 8px">TOP CALLERS (most outbound calls)</div>',
                unsafe_allow_html=True,
            )
            rows_html = "".join(
                f'<div style="display:flex;align-items:center;gap:10px;padding:6px 10px;'
                f'background:#0d0d1a;border:1px solid #1a1a2e;border-radius:6px;margin-bottom:4px">'
                f'<span style="color:#a67cff;font-weight:600;flex:1;overflow:hidden;'
                f'text-overflow:ellipsis;white-space:nowrap">{html_lib.escape(fn)}</span>'
                f'<span style="color:#00e87a;font-weight:700;font-size:13px;flex-shrink:0">{cnt}</span>'
                f'<span style="color:#505070;font-size:9px;flex-shrink:0">calls</span>'
                f'</div>'
                for fn, cnt in top_callers
            )
            st.markdown(rows_html, unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────
def _hex_to_rgb(hex_color: str) -> str:
    """Convert #rrggbb to 'r,g,b' string for rgba() CSS."""
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"{r},{g},{b}"


def _truncate(s: str, n: int) -> str:
    return s if len(s) <= n else s[:n - 1] + "…"
