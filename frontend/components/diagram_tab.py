"""
RepoLens — Diagrams Tab
Three interactive Plotly diagrams:
  1. Request/Response Flow — the real frontend→router→handler→service→db→response path
  2. Architecture Map      — layered scatter of all detected nodes
  3. Import Sankey         — file → external package flow
"""
from __future__ import annotations
import math
import html as html_lib
import re
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from backend.analyzers.analysis_engine import AnalysisResult
from config.settings import ARCH_LAYERS

# ── Theme ──────────────────────────────────────────────────────────────────
BG      = "#06060d"
CARD    = "#0d0d1a"
BORDER  = "#1a1a2e"
TEXT    = "#dde0f5"
MUTED   = "#505070"
GREEN   = "#00e87a"
BLUE    = "#4b9eff"
PURPLE  = "#a67cff"
ORANGE  = "#ff8f3c"
YELLOW  = "#ffd166"
RED     = "#ff4d6a"

LAYER_COLOR = {
    "entry":   GREEN,
    "ctrl":    PURPLE,
    "service": BLUE,
    "data":    ORANGE,
    "util":    YELLOW,
    "ext":     "#888888",
}

def _rgb(h: str) -> str:
    h = h.lstrip("#")
    if len(h) == 3: h = "".join(c*2 for c in h)
    return f"{int(h[0:2],16)},{int(h[2:4],16)},{int(h[4:6],16)}"

def _trunc(s: str, n: int) -> str:
    return s if len(s) <= n else s[:n-2]+"…"


# ══════════════════════════════════════════════════════════════════════════════
#  1. REQUEST / RESPONSE FLOW DIAGRAM
#     A top-down swimlane: CLIENT → ROUTER → HANDLER → SERVICE → DB → RESPONSE
# ══════════════════════════════════════════════════════════════════════════════

def _build_req_flow(result: AnalysisResult) -> go.Figure:
    """
    Build a clean top-down request/response flow diagram.
    Each swimlane = one architectural zone. Real file/function names are used.
    """
    routes    = result.routes
    functions = result.functions
    classes   = result.classes
    arch      = result.arch
    stack     = result.stack

    # ── Gather real names per zone ────────────────────────────────────
    def nodes_in_layer(key: str) -> list[str]:
        for lyr in arch.layers:
            if lyr.key == key:
                return [n.label for n in lyr.nodes[:5]]
        return []

    entry_nodes   = nodes_in_layer("entry")
    ctrl_nodes    = nodes_in_layer("ctrl")
    service_nodes = nodes_in_layer("service")
    data_nodes    = nodes_in_layer("data")
    ext_nodes     = nodes_in_layer("ext")

    # Route labels
    route_labels = [f"{r.method} {r.path}" for r in routes[:4]]

    # Handler functions (from entry layer files)
    handler_fns = [
        fn.name for fn in functions
        if any(en.lower() in fn.file.lower() for en in entry_nodes)
    ][:4]
    if not handler_fns:
        handler_fns = [fn.name for fn in functions[:4]]

    # Service functions
    service_fns = [
        fn.name for fn in functions
        if any(sn.lower() in fn.file.lower() for sn in service_nodes)
    ][:4]
    if not service_fns:
        service_fns = [fn.name for fn in functions[4:8]]

    # Data functions (CRUD)
    data_fns = [
        fn.name for fn in functions
        if re.search(r"find|get|fetch|save|create|update|delete|query|insert|select",
                     fn.name, re.IGNORECASE)
    ][:4]

    # ── Layout constants ──────────────────────────────────────────────
    # We draw 7 horizontal swim-lanes stacked vertically:
    # CLIENT → ROUTER → HANDLER(S) → SERVICE(S) → DB/MODEL → EXTERNAL → RESPONSE
    LANES = [
        ("CLIENT",       GREEN,  "rgba(0,232,122,0.06)",  0.90),
        ("ROUTER",       PURPLE, "rgba(166,124,255,0.06)",0.72),
        ("HANDLER",      PURPLE, "rgba(166,124,255,0.04)",0.55),
        ("SERVICE",      BLUE,   "rgba(75,158,255,0.06)", 0.37),
        ("DATA / DB",    ORANGE, "rgba(255,143,60,0.06)", 0.20),
        ("RESPONSE",     GREEN,  "rgba(0,232,122,0.06)",  0.04),
    ]

    # Node data per lane: (label, x_pos)
    def _evenly(labels: list[str], y: float, spacing: float = 0.18) -> list[tuple]:
        n    = len(labels)
        xs   = [0.5 + (i - (n-1)/2) * spacing for i in range(n)]
        return [(lbl, x, y) for lbl, x in zip(labels, xs)]

    nodes: list[dict] = []  # {label, x, y, color, lane, detail}

    # CLIENT node
    nodes.append({"label":"Client / Browser","x":0.5,"y":0.90,
                  "color":GREEN,"lane":"CLIENT","detail":"HTTP request origin"})

    # ROUTER nodes
    if route_labels:
        for item in _evenly(route_labels, 0.72, 0.20):
            nodes.append({"label":item[0],"x":item[1],"y":item[2],
                          "color":PURPLE,"lane":"ROUTER","detail":"Route definition"})
    elif entry_nodes:
        for item in _evenly(entry_nodes[:3], 0.72, 0.22):
            nodes.append({"label":item[0],"x":item[1],"y":item[2],
                          "color":PURPLE,"lane":"ROUTER","detail":"Entry module"})

    # HANDLER nodes
    handler_labels = handler_fns or ctrl_nodes[:3] or ["handler"]
    for item in _evenly([_trunc(l,22) for l in handler_labels[:4]], 0.55, 0.22):
        nodes.append({"label":item[0],"x":item[1],"y":item[2],
                      "color":PURPLE,"lane":"HANDLER","detail":"Request handler"})

    # SERVICE nodes
    service_labels = service_fns or service_nodes[:3] or []
    if service_labels:
        for item in _evenly([_trunc(l,22) for l in service_labels[:4]], 0.37, 0.22):
            nodes.append({"label":item[0],"x":item[1],"y":item[2],
                          "color":BLUE,"lane":"SERVICE","detail":"Business logic"})

    # DATA nodes
    data_labels = data_fns or data_nodes[:3] or []
    if data_labels:
        for item in _evenly([_trunc(l,22) for l in data_labels[:4]], 0.20, 0.22):
            nodes.append({"label":item[0],"x":item[1],"y":item[2],
                          "color":ORANGE,"lane":"DATA","detail":"Data access"})

    # RESPONSE node
    nodes.append({"label":"HTTP Response","x":0.5,"y":0.04,
                  "color":GREEN,"lane":"RESPONSE","detail":"JSON / HTML response"})

    # ── Build edges (request path down, response path up) ─────────────
    edges = []  # (x0, y0, x1, y1, color, dashed)

    def _nodes_in_lane(lane: str):
        return [n for n in nodes if n["lane"] == lane]

    lane_order = ["CLIENT","ROUTER","HANDLER","SERVICE","DATA","RESPONSE"]
    # Request: CLIENT → first ROUTER → first HANDLER → first SERVICE → first DATA → RESPONSE
    prev = None
    for lane in lane_order:
        lane_nodes = _nodes_in_lane(lane)
        if not lane_nodes:
            continue
        cur = lane_nodes[0]
        if prev:
            edges.append((prev["x"], prev["y"], cur["x"], cur["y"], GREEN, False))
        prev = cur

    # Fan-out: ROUTER → all HANDLERs (dashed)
    router_nodes  = _nodes_in_lane("ROUTER")
    handler_nodes = _nodes_in_lane("HANDLER")
    if router_nodes and len(handler_nodes) > 1:
        r0 = router_nodes[0]
        for h in handler_nodes[1:]:
            edges.append((r0["x"], r0["y"], h["x"], h["y"], PURPLE, True))

    # Fan-out: HANDLER → all SERVICEs (dashed)
    handler_nodes2 = _nodes_in_lane("HANDLER")
    service_nodes2 = _nodes_in_lane("SERVICE")
    if handler_nodes2 and len(service_nodes2) > 1:
        h0 = handler_nodes2[0]
        for s in service_nodes2[1:]:
            edges.append((h0["x"], h0["y"], s["x"], s["y"], BLUE, True))

    # ── Build Plotly figure ────────────────────────────────────────────
    fig = go.Figure()

    # Swimlane backgrounds
    for label, color, fill, y_center in LANES:
        half = 0.075
        fig.add_shape(type="rect",
            x0=0, y0=y_center-half, x1=1, y1=y_center+half,
            fillcolor=fill, line=dict(color=f"rgba({_rgb(color)},0.2)", width=0.5),
            layer="below")
        # Lane label on left
        fig.add_annotation(x=-0.01, y=y_center,
            text=label, showarrow=False,
            xanchor="right", yanchor="middle",
            font=dict(size=9, color=color, family="JetBrains Mono"),
            xref="paper", yref="paper")

    # Edges
    for x0, y0, x1, y1, col, dashed in edges:
        fig.add_shape(type="line",
            x0=x0, y0=y0, x1=x1, y1=y1,
            line=dict(color=f"rgba({_rgb(col)},0.5)",
                      width=1.5, dash="dot" if dashed else "solid"),
            xref="paper", yref="paper", layer="below")
        # Arrowhead at destination
        if not dashed:
            fig.add_annotation(x=x1, y=y1,
                ax=x0, ay=y0,
                xref="paper", yref="paper",
                axref="paper", ayref="paper",
                showarrow=True, arrowhead=3, arrowsize=1.2,
                arrowwidth=1.5, arrowcolor=f"rgba({_rgb(col)},0.7)")

    # Node markers
    node_x     = [n["x"] for n in nodes]
    node_y     = [n["y"] for n in nodes]
    node_text  = [_trunc(n["label"], 20) for n in nodes]
    node_color = [n["color"] for n in nodes]
    node_hover = [f"<b>{n['label']}</b><br><i>{n['lane']}</i><br>{n['detail']}" for n in nodes]

    # Glow circles
    fig.add_trace(go.Scatter(
        x=node_x, y=node_y, mode="markers",
        marker=dict(size=32,
                    color=[f"rgba({_rgb(c)},0.08)" for c in node_color],
                    line=dict(color=[f"rgba({_rgb(c)},0.3)" for c in node_color], width=1)),
        hoverinfo="skip", showlegend=False,
        xaxis="x", yaxis="y",
    ))

    # Inner dots + labels
    fig.add_trace(go.Scatter(
        x=node_x, y=node_y, mode="markers+text",
        marker=dict(size=10, color=node_color,
                    line=dict(color=BG, width=2)),
        text=node_text,
        textposition="bottom center",
        textfont=dict(size=9, color=TEXT, family="JetBrains Mono"),
        hovertext=node_hover, hoverinfo="text",
        hoverlabel=dict(bgcolor=CARD, bordercolor=PURPLE,
                        font=dict(size=11, color=TEXT, family="JetBrains Mono")),
        showlegend=False,
        xaxis="x", yaxis="y",
    ))

    fig.update_layout(
        paper_bgcolor=BG, plot_bgcolor=BG,
        height=600, margin=dict(l=90, r=20, t=30, b=20),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False,
                   range=[0, 1], domain=[0, 1]),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False,
                   range=[-0.02, 1.02], domain=[0, 1]),
        hovermode="closest",
    )
    return fig


# ══════════════════════════════════════════════════════════════════════════════
#  2. ARCHITECTURE MAP — layered scatter
# ══════════════════════════════════════════════════════════════════════════════

def _build_arch_map(result: AnalysisResult) -> go.Figure:
    arch = result.arch
    LAYER_ORDER = ["entry","ctrl","service","data","util","ext"]

    fig = go.Figure()

    for li, layer in enumerate(arch.layers):
        if not layer.nodes:
            continue
        color = LAYER_COLOR.get(layer.key, "#888")
        n     = len(layer.nodes)

        # Band background
        fig.add_shape(type="rect",
            x0=li-0.45, y0=-5, x1=li+0.45, y1=5,
            fillcolor=f"rgba({_rgb(color)},0.04)",
            line=dict(color=f"rgba({_rgb(color)},0.2)", width=1),
            layer="below")

        # Layer header
        fig.add_annotation(x=li, y=5.3,
            text=layer.label, showarrow=False,
            font=dict(size=8, color=color, family="JetBrains Mono"),
            xanchor="center")

        # Nodes
        node_y = [(j - (n-1)/2) * 1.3 for j in range(n)]
        node_labels = [_trunc(nd.label, 14) for nd in layer.nodes]
        node_hover  = [f"<b>{nd.label}</b><br><i>{layer.label}</i><br>{nd.detail}"
                       for nd in layer.nodes]

        # Glow
        fig.add_trace(go.Scatter(
            x=[li]*n, y=node_y, mode="markers",
            marker=dict(size=30, color=f"rgba({_rgb(color)},0.08)",
                        line=dict(color=f"rgba({_rgb(color)},0.3)", width=1.5)),
            hoverinfo="skip", showlegend=False))

        # Node dots
        fig.add_trace(go.Scatter(
            x=[li]*n, y=node_y, mode="markers+text",
            marker=dict(size=9, color=color, line=dict(color=BG, width=2)),
            text=node_labels,
            textposition="bottom center",
            textfont=dict(size=8, color=TEXT, family="JetBrains Mono"),
            hovertext=node_hover, hoverinfo="text",
            name=layer.label,
            hoverlabel=dict(bgcolor=CARD, bordercolor=color,
                            font=dict(size=11, color=TEXT, family="JetBrains Mono"))))

    # Inter-layer arrows
    prev_layer = None
    for layer in arch.layers:
        if not layer.nodes:
            continue
        li = LAYER_ORDER.index(layer.key) if layer.key in LAYER_ORDER else 0
        if prev_layer is not None:
            pli = LAYER_ORDER.index(prev_layer.key) if prev_layer.key in LAYER_ORDER else 0
            py  = (0 - (len(prev_layer.nodes)-1)/2) * 1.3
            cy  = (0 - (len(layer.nodes)-1)/2) * 1.3
            fig.add_annotation(
                x=li-0.46, y=cy, ax=pli+0.46, ay=py,
                xref="x", yref="y", axref="x", ayref="y",
                showarrow=True, arrowhead=3, arrowsize=1, arrowwidth=1.5,
                arrowcolor=f"rgba({_rgb(PURPLE)},0.4)")
        prev_layer = layer

    fig.update_layout(
        paper_bgcolor=BG, plot_bgcolor=BG,
        height=580, margin=dict(l=20, r=20, t=40, b=20),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False,
                   range=[-0.7, len(LAYER_ORDER)-0.3]),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False,
                   range=[-6, 6]),
        hovermode="closest",
        legend=dict(orientation="h", y=1.06, x=0,
                    font=dict(size=9, color=TEXT, family="JetBrains Mono"),
                    bgcolor="rgba(0,0,0,0)"),
    )
    return fig


# ══════════════════════════════════════════════════════════════════════════════
#  3. IMPORT FLOW — Sankey
# ══════════════════════════════════════════════════════════════════════════════

def _build_sankey(result: AnalysisResult) -> go.Figure | None:
    ext_imports = [i for i in result.imports if not i.local]
    if not ext_imports:
        return None

    files = list(dict.fromkeys(i.file.rsplit("/",1)[-1] for i in ext_imports))[:18]
    pkgs  = list(dict.fromkeys(
        "/".join(i.name.split("/")[:2]) if i.name.startswith("@") else i.name.split("/")[0]
        for i in ext_imports
    ))[:18]

    fi = {f: i for i, f in enumerate(files)}
    pi = {p: len(files)+i for i, p in enumerate(pkgs)}

    counts: dict[tuple,int] = {}
    for imp in ext_imports:
        f = imp.file.rsplit("/",1)[-1]
        p = "/".join(imp.name.split("/")[:2]) if imp.name.startswith("@") else imp.name.split("/")[0]
        if f in fi and p in pi:
            k = (fi[f], pi[p])
            counts[k] = counts.get(k, 0) + 1

    if not counts:
        return None

    sources = [k[0] for k in counts]
    targets = [k[1] for k in counts]
    values  = list(counts.values())

    fig = go.Figure(go.Sankey(
        arrangement="snap",
        node=dict(
            pad=18, thickness=16,
            line=dict(color=CARD, width=0.5),
            label=files + pkgs,
            color=(["rgba(0,232,122,0.7)"]*len(files) +
                   ["rgba(75,158,255,0.7)"]*len(pkgs)),
            hovertemplate="<b>%{label}</b><br>%{value} import(s)<extra></extra>",
        ),
        link=dict(
            source=sources, target=targets, value=values,
            color="rgba(166,124,255,0.15)",
            hovertemplate="%{source.label} → %{target.label}<br>%{value} import(s)<extra></extra>",
        ),
        textfont=dict(color=TEXT, size=10, family="JetBrains Mono"),
    ))
    fig.update_layout(
        paper_bgcolor=BG, height=480,
        margin=dict(l=10, r=10, t=10, b=10),
        font=dict(color=TEXT, family="JetBrains Mono"),
    )
    return fig


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN RENDER
# ══════════════════════════════════════════════════════════════════════════════

def render_diagram(result: AnalysisResult) -> None:
    tab_req, tab_arch, tab_import = st.tabs([
        "Request / Response Flow",
        "Architecture Map",
        "Import Flow",
    ])

    # ── 1. Request / Response Flow ────────────────────────────────────
    with tab_req:
        st.markdown(
            '<div style="font-size:9px;letter-spacing:2px;color:#505070;margin-bottom:4px">'
            'HOW A REQUEST FLOWS THROUGH THE CODEBASE — left lane = entry, right = exit</div>',
            unsafe_allow_html=True,
        )

        # Legend pills — using native st.markdown for LABELS only
        legend_items = [
            ("CLIENT / RESPONSE", GREEN),
            ("ROUTER / HANDLER",  PURPLE),
            ("SERVICE LAYER",     BLUE),
            ("DATA / DB LAYER",   ORANGE),
        ]
        cols = st.columns(len(legend_items))
        for col, (label, color) in zip(cols, legend_items):
            with col:
                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:6px;'
                    f'padding:5px 10px;border-radius:20px;border:1px solid rgba({_rgb(color)},0.3);'
                    f'background:rgba({_rgb(color)},0.06);justify-content:center;">'
                    f'<span style="width:7px;height:7px;border-radius:50%;'
                    f'background:{color};flex-shrink:0;display:inline-block;"></span>'
                    f'<span style="font-size:9px;color:{color};letter-spacing:0.5px;">{label}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

        st.markdown("")
        fig = _build_req_flow(result)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        # Annotated walkthrough — pure native Streamlit
        st.markdown("---")
        st.markdown("**Request Walkthrough**")

        routes   = result.routes
        arch     = result.arch
        stack    = result.stack

        def _layer_nodes(key):
            for lyr in arch.layers:
                if lyr.key == key:
                    return [n.label for n in lyr.nodes[:4]]
            return []

        walkthrough = [
            ("1  Client sends request",
             f"An HTTP request originates from the client (browser / API consumer).",
             GREEN),
            ("2  Router matches URL",
             (f"Matched against {len(routes)} defined route(s). "
              f"Example: `{routes[0].method} {routes[0].path}`" if routes else
              "URL is matched to a route handler."),
             PURPLE),
            ("3  Handler processes request",
             (f"Handler in `{_layer_nodes('entry')[0]}` runs — validates input, "
              f"calls service layer." if _layer_nodes('entry') else
              "Handler validates input and calls the service layer."),
             PURPLE),
            ("4  Service layer applies logic",
             (f"Business logic in `{_layer_nodes('service')[0]}` executes — "
              f"orchestrates data access." if _layer_nodes('service') else
              "Service layer applies business rules."),
             BLUE),
            ("5  Data layer queries DB",
             (f"`{_layer_nodes('data')[0]}` queries the database "
              f"({stack.database or 'data store'}) and returns results."
              if _layer_nodes('data') else
              f"Data layer queries {stack.database or 'the database'}."),
             ORANGE),
            ("6  Response returned",
             "Results pass back up through service → handler → serialized to JSON/HTML → client.",
             GREEN),
        ]

        for title, body, color in walkthrough:
            col_dot, col_text = st.columns([0.03, 0.97])
            with col_dot:
                st.markdown(
                    f'<div style="width:10px;height:10px;border-radius:50%;'
                    f'background:{color};margin-top:7px;"></div>',
                    unsafe_allow_html=True,
                )
            with col_text:
                st.markdown(f"**{title}**")
                st.markdown(body)

    # ── 2. Architecture Map ───────────────────────────────────────────
    with tab_arch:
        st.markdown(
            '<div style="font-size:9px;letter-spacing:2px;color:#505070;margin-bottom:8px">'
            'LAYERED ARCHITECTURE — all detected nodes by layer · hover for details</div>',
            unsafe_allow_html=True,
        )

        fig_arch = _build_arch_map(result)
        st.plotly_chart(fig_arch, use_container_width=True, config={"displayModeBar": False})

        # Layer summary cards
        layer_cols = st.columns(6)
        for col, layer in zip(layer_cols, result.arch.layers):
            color = LAYER_COLOR.get(layer.key, "#888")
            with col:
                st.markdown(
                    f'<div style="background:{CARD};border:1px solid rgba({_rgb(color)},0.3);'
                    f'border-top:2px solid {color};border-radius:8px;'
                    f'padding:10px;text-align:center;">'
                    f'<div style="font-family:Outfit,sans-serif;font-weight:800;'
                    f'font-size:22px;color:{color}">{len(layer.nodes)}</div>'
                    f'<div style="font-size:8px;color:{MUTED};letter-spacing:1px;margin-top:2px">'
                    f'{layer.label}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

        # Node detail pills
        st.markdown("")
        for layer in result.arch.layers:
            if not layer.nodes:
                continue
            color = LAYER_COLOR.get(layer.key, "#888")
            st.markdown(
                f'<div style="font-size:9px;color:{MUTED};letter-spacing:1px;'
                f'margin:12px 0 5px">{layer.label} ({len(layer.nodes)})</div>',
                unsafe_allow_html=True,
            )
            pills = "".join(
                f'<span title="{html_lib.escape(nd.detail or "")}" '
                f'style="display:inline-flex;align-items:center;gap:4px;'
                f'padding:3px 9px;border-radius:4px;margin:3px;cursor:default;'
                f'border:1px solid rgba({_rgb(color)},0.3);'
                f'color:{color};background:rgba({_rgb(color)},0.07);font-size:10px;">'
                f'<span style="width:5px;height:5px;border-radius:50%;'
                f'background:{color};display:inline-block;flex-shrink:0;"></span>'
                f'{html_lib.escape(nd.label)}</span>'
                for nd in layer.nodes
            )
            st.markdown(
                f'<div style="display:flex;flex-wrap:wrap;">{pills}</div>',
                unsafe_allow_html=True,
            )

    # ── 3. Import Flow ────────────────────────────────────────────────
    with tab_import:
        st.markdown(
            '<div style="font-size:9px;letter-spacing:2px;color:#505070;margin-bottom:8px">'
            'IMPORT FLOW — source files (green) to external packages (blue) · '
            'width = import frequency</div>',
            unsafe_allow_html=True,
        )

        fig_sankey = _build_sankey(result)
        if fig_sankey:
            st.plotly_chart(fig_sankey, use_container_width=True,
                            config={"displayModeBar": False})
        else:
            st.info("Not enough import data to render the Sankey diagram.")

        # Top packages
        pkg_counts: dict[str,int] = {}
        for imp in result.imports:
            if imp.local: continue
            pkg = ("/".join(imp.name.split("/")[:2]) if imp.name.startswith("@")
                   else imp.name.split("/")[0])
            pkg_counts[pkg] = pkg_counts.get(pkg, 0) + 1

        if pkg_counts:
            top = sorted(pkg_counts.items(), key=lambda x: -x[1])[:8]
            st.markdown("**Most imported packages**")
            for pkg, cnt in top:
                bar_w = int(cnt / top[0][1] * 100)
                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:10px;'
                    f'margin-bottom:5px;">'
                    f'<span style="color:{TEXT};font-size:11px;width:160px;'
                    f'overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">'
                    f'{html_lib.escape(pkg)}</span>'
                    f'<div style="flex:1;background:{BORDER};border-radius:3px;height:6px;">'
                    f'<div style="width:{bar_w}%;background:{BLUE};border-radius:3px;height:6px;"></div>'
                    f'</div>'
                    f'<span style="color:{MUTED};font-size:10px;width:30px;text-align:right;">'
                    f'{cnt}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
