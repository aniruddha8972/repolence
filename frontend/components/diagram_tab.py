"""
RepoLens — Diagrams Tab
Three interactive Plotly diagrams:
  1. Request/Response Flow — swimlane: CLIENT → ROUTER → HANDLER → SERVICE → DB → RESPONSE
  2. Architecture Map      — layered scatter of all detected nodes
  3. Import Flow           — Sankey: files → external packages

Compatibility note: all arrowheads drawn as Scatter marker triangles because
plotly axref='paper' is not supported in all versions (only 'pixel' or axis refs).
"""
from __future__ import annotations
import math
import html as html_lib
import re
import streamlit as st
import plotly.graph_objects as go

from backend.analyzers.analysis_engine import AnalysisResult
from config.settings import ARCH_LAYERS

# ── Theme ──────────────────────────────────────────────────────────────────
BG     = "#06060d"
CARD   = "#0d0d1a"
BORDER = "#1a1a2e"
TEXT   = "#dde0f5"
MUTED  = "#505070"
GREEN  = "#00e87a"
BLUE   = "#4b9eff"
PURPLE = "#a67cff"
ORANGE = "#ff8f3c"
YELLOW = "#ffd166"
RED    = "#ff4d6a"

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
    if len(h) == 3: h = "".join(c * 2 for c in h)
    return f"{int(h[0:2],16)},{int(h[2:4],16)},{int(h[4:6],16)}"

def _trunc(s: str, n: int) -> str:
    return s if len(s) <= n else s[:n - 2] + "…"

def _arrow_traces(x0, y0, x1, y1, color: str, dashed: bool = False,
                  xref="paper", yref="paper") -> list:
    """
    Draw a line + triangle arrowhead as Scatter traces.
    Avoids axref/ayref which are not universally supported.
    """
    traces = []
    # Line
    traces.append(go.Scatter(
        x=[x0, x1], y=[y0, y1],
        mode="lines",
        line=dict(color=f"rgba({_rgb(color)},0.55)",
                  width=1.5, dash="dot" if dashed else "solid"),
        hoverinfo="skip", showlegend=False,
        xaxis="x" if xref == "x" else None,
        yaxis="y" if yref == "y" else None,
    ))
    # Arrowhead: a small filled triangle at (x1, y1) pointing in direction of travel
    if not dashed:
        dx = x1 - x0
        dy = y1 - y0
        dist = math.sqrt(dx * dx + dy * dy) or 1
        # Angle in degrees for the marker symbol rotation
        angle = math.degrees(math.atan2(dy, dx)) - 90
        traces.append(go.Scatter(
            x=[x1], y=[y1],
            mode="markers",
            marker=dict(symbol="triangle-up", size=10,
                        color=f"rgba({_rgb(color)},0.8)",
                        angle=angle,
                        line=dict(width=0)),
            hoverinfo="skip", showlegend=False,
            xaxis="x" if xref == "x" else None,
            yaxis="y" if yref == "y" else None,
        ))
    return traces


# ══════════════════════════════════════════════════════════════════════════════
#  1. REQUEST / RESPONSE FLOW — swimlane diagram
# ══════════════════════════════════════════════════════════════════════════════

def _build_req_flow(result: AnalysisResult) -> go.Figure:
    routes    = result.routes
    functions = result.functions
    arch      = result.arch
    stack     = result.stack

    def _layer_node_labels(key: str) -> list[str]:
        for lyr in arch.layers:
            if lyr.key == key:
                return [n.label for n in lyr.nodes[:5]]
        return []

    entry_nodes   = _layer_node_labels("entry")
    service_nodes = _layer_node_labels("service")
    data_nodes    = _layer_node_labels("data")

    route_labels = [f"{r.method} {r.path}" for r in routes[:4]]

    handler_fns = [fn.name for fn in functions
                   if any(e.lower() in fn.file.lower() for e in entry_nodes)][:4]
    if not handler_fns:
        handler_fns = [fn.name for fn in functions[:4]]

    service_fns = [fn.name for fn in functions
                   if any(s.lower() in fn.file.lower() for s in service_nodes)][:4]
    if not service_fns:
        service_fns = [fn.name for fn in functions[len(handler_fns):len(handler_fns)+4]]

    data_fns = [fn.name for fn in functions
                if re.search(r"find|get|fetch|save|create|update|delete|query|insert|select",
                             fn.name, re.IGNORECASE)][:4]

    # ── Swimlane y positions (paper coords 0–1) ───────────────────────
    LANES = [
        # (id,       label,          color,   y_center)
        ("client",   "CLIENT",       GREEN,   0.92),
        ("router",   "ROUTER",       PURPLE,  0.74),
        ("handler",  "HANDLER",      PURPLE,  0.56),
        ("service",  "SERVICE",      BLUE,    0.38),
        ("data",     "DATA / DB",    ORANGE,  0.20),
        ("response", "RESPONSE",     GREEN,   0.04),
    ]
    HALF = 0.07   # half-height of each swim lane band

    def _spread(labels: list[str], y: float, spacing: float = 0.19) -> list[dict]:
        n  = len(labels)
        xs = [0.5 + (i - (n - 1) / 2) * spacing for i in range(n)]
        return [{"label": _trunc(lb, 22), "x": x, "y": y} for lb, x in zip(labels, xs)]

    # Build node list per lane
    lane_nodes: dict[str, list[dict]] = {}
    lane_nodes["client"]   = [{"label": "Client / Browser", "x": 0.5, "y": 0.92}]
    lane_nodes["router"]   = (_spread(route_labels, 0.74, 0.19)
                               if route_labels else _spread(entry_nodes[:3], 0.74, 0.22))
    lane_nodes["handler"]  = _spread([_trunc(l, 22) for l in (handler_fns or ["handler"])], 0.56, 0.22)
    lane_nodes["service"]  = _spread([_trunc(l, 22) for l in service_fns], 0.38, 0.22) if service_fns else []
    lane_nodes["data"]     = _spread([_trunc(l, 22) for l in (data_fns or data_nodes[:3])], 0.20, 0.22) if (data_fns or data_nodes) else []
    lane_nodes["response"] = [{"label": "HTTP Response", "x": 0.5, "y": 0.04}]

    lane_color = {lid: col for lid, _, col, _ in LANES}

    fig = go.Figure()

    # Swimlane backgrounds (shapes on paper)
    for lid, lbl, col, yc in LANES:
        fig.add_shape(type="rect",
            x0=0, y0=yc - HALF, x1=1, y1=yc + HALF,
            xref="paper", yref="paper",
            fillcolor=f"rgba({_rgb(col)},0.06)",
            line=dict(color=f"rgba({_rgb(col)},0.18)", width=0.5),
            layer="below")
        fig.add_annotation(
            x=0.01, y=yc,
            xref="paper", yref="paper",
            text=f"<b>{lbl}</b>",
            showarrow=False, xanchor="left", yanchor="middle",
            font=dict(size=9, color=col, family="JetBrains Mono"))

    # Main request path: client→router→handler→service→data→response
    spine = ["client", "router", "handler", "service", "data", "response"]
    prev_nd = None
    for lid in spine:
        nds = lane_nodes.get(lid, [])
        if not nds:
            continue
        nd = nds[0]
        if prev_nd:
            col = lane_color.get(lid, GREEN)
            for t in _arrow_traces(prev_nd["x"], prev_nd["y"],
                                    nd["x"], nd["y"], col):
                fig.add_trace(t)
        prev_nd = nd

    # Fan-out dashed arrows: router → extra handlers, handler → extra services
    for lid_src, lid_dst in [("router", "handler"), ("handler", "service")]:
        src_nds = lane_nodes.get(lid_src, [])
        dst_nds = lane_nodes.get(lid_dst, [])
        col     = lane_color.get(lid_dst, PURPLE)
        if src_nds and len(dst_nds) > 1:
            s = src_nds[0]
            for d in dst_nds[1:]:
                for t in _arrow_traces(s["x"], s["y"], d["x"], d["y"],
                                        col, dashed=True):
                    fig.add_trace(t)

    # All nodes as scatter
    all_nodes = [nd for nds in lane_nodes.values() for nd in nds]
    if all_nodes:
        nx     = [n["x"] for n in all_nodes]
        ny     = [n["y"] for n in all_nodes]
        ntxt   = [n["label"] for n in all_nodes]
        # Colour by lane
        ncolor = []
        for n in all_nodes:
            for lid, _, col, yc in LANES:
                if abs(n["y"] - yc) < 0.1:
                    ncolor.append(col); break
            else:
                ncolor.append(PURPLE)

        # Glow
        fig.add_trace(go.Scatter(
            x=nx, y=ny, mode="markers",
            marker=dict(size=34,
                        color=[f"rgba({_rgb(c)},0.08)" for c in ncolor],
                        line=dict(color=[f"rgba({_rgb(c)},0.28)" for c in ncolor], width=1)),
            hoverinfo="skip", showlegend=False,
            xaxis="x", yaxis="y"))

        hover = [f"<b>{n['label']}</b>" for n in all_nodes]
        fig.add_trace(go.Scatter(
            x=nx, y=ny, mode="markers+text",
            marker=dict(size=10, color=ncolor, line=dict(color=BG, width=2)),
            text=ntxt, textposition="bottom center",
            textfont=dict(size=9, color=TEXT, family="JetBrains Mono"),
            hovertext=hover, hoverinfo="text",
            hoverlabel=dict(bgcolor=CARD, bordercolor=PURPLE,
                            font=dict(size=11, color=TEXT, family="JetBrains Mono")),
            showlegend=False,
            xaxis="x", yaxis="y"))

    fig.update_layout(
        paper_bgcolor=BG, plot_bgcolor=BG,
        height=590, margin=dict(l=10, r=10, t=20, b=20),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False,
                   range=[0, 1], domain=[0, 1]),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False,
                   range=[-0.02, 1.02], domain=[0, 1]),
        hovermode="closest")
    return fig


# ══════════════════════════════════════════════════════════════════════════════
#  2. ARCHITECTURE MAP — layered scatter
# ══════════════════════════════════════════════════════════════════════════════

def _build_arch_map(result: AnalysisResult) -> go.Figure:
    LAYER_ORDER = ["entry", "ctrl", "service", "data", "util", "ext"]
    arch = result.arch

    fig = go.Figure()

    populated = [lyr for lyr in arch.layers if lyr.nodes]

    for layer in populated:
        li    = LAYER_ORDER.index(layer.key) if layer.key in LAYER_ORDER else 0
        color = LAYER_COLOR.get(layer.key, "#888")
        n     = len(layer.nodes)

        # Band background
        fig.add_shape(type="rect",
            x0=li - 0.45, y0=-6, x1=li + 0.45, y1=6,
            fillcolor=f"rgba({_rgb(color)},0.05)",
            line=dict(color=f"rgba({_rgb(color)},0.2)", width=1),
            layer="below")

        fig.add_annotation(x=li, y=5.6,
            text=f"<b>{layer.label}</b>", showarrow=False,
            font=dict(size=8, color=color, family="JetBrains Mono"),
            xanchor="center")

        node_y  = [(j - (n - 1) / 2) * 1.3 for j in range(n)]
        labels  = [_trunc(nd.label, 14) for nd in layer.nodes]
        hovers  = [f"<b>{nd.label}</b><br><i>{layer.label}</i><br>{nd.detail}"
                   for nd in layer.nodes]

        # Glow circles
        fig.add_trace(go.Scatter(
            x=[li] * n, y=node_y, mode="markers",
            marker=dict(size=30, color=f"rgba({_rgb(color)},0.09)",
                        line=dict(color=f"rgba({_rgb(color)},0.3)", width=1.5)),
            hoverinfo="skip", showlegend=False))

        fig.add_trace(go.Scatter(
            x=[li] * n, y=node_y, mode="markers+text",
            marker=dict(size=9, color=color, line=dict(color=BG, width=2)),
            text=labels, textposition="bottom center",
            textfont=dict(size=8, color=TEXT, family="JetBrains Mono"),
            hovertext=hovers, hoverinfo="text",
            name=layer.label,
            hoverlabel=dict(bgcolor=CARD, bordercolor=color,
                            font=dict(size=11, color=TEXT, family="JetBrains Mono"))))

    # Inter-layer arrows as Scatter (no axref)
    prev = None
    for layer in populated:
        li = LAYER_ORDER.index(layer.key) if layer.key in LAYER_ORDER else 0
        n  = len(layer.nodes)
        cy = (0 - (n - 1) / 2) * 1.3   # y of first node
        if prev is not None:
            pli, pcy = prev
            for t in _arrow_traces(pli + 0.46, pcy, li - 0.46, cy,
                                    PURPLE, xref="x", yref="y"):
                fig.add_trace(t)
        prev = (li, cy)

    fig.update_layout(
        paper_bgcolor=BG, plot_bgcolor=BG,
        height=580, margin=dict(l=20, r=20, t=50, b=20),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False,
                   range=[-0.7, len(LAYER_ORDER) - 0.3]),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False,
                   range=[-6.5, 6.2]),
        hovermode="closest",
        legend=dict(orientation="h", y=1.06, x=0,
                    font=dict(size=9, color=TEXT, family="JetBrains Mono"),
                    bgcolor="rgba(0,0,0,0)"))
    return fig


# ══════════════════════════════════════════════════════════════════════════════
#  3. IMPORT FLOW — Sankey
# ══════════════════════════════════════════════════════════════════════════════

def _build_sankey(result: AnalysisResult) -> go.Figure | None:
    ext_imports = [i for i in result.imports if not i.local]
    if not ext_imports:
        return None

    files = list(dict.fromkeys(i.file.rsplit("/", 1)[-1] for i in ext_imports))[:18]
    pkgs  = list(dict.fromkeys(
        "/".join(i.name.split("/")[:2]) if i.name.startswith("@") else i.name.split("/")[0]
        for i in ext_imports))[:18]

    fi = {f: idx for idx, f in enumerate(files)}
    pi = {p: len(files) + idx for idx, p in enumerate(pkgs)}

    counts: dict[tuple, int] = {}
    for imp in ext_imports:
        f = imp.file.rsplit("/", 1)[-1]
        p = ("/".join(imp.name.split("/")[:2]) if imp.name.startswith("@")
             else imp.name.split("/")[0])
        if f in fi and p in pi:
            k = (fi[f], pi[p])
            counts[k] = counts.get(k, 0) + 1

    if not counts:
        return None

    fig = go.Figure(go.Sankey(
        arrangement="snap",
        node=dict(
            pad=18, thickness=16,
            line=dict(color=CARD, width=0.5),
            label=files + pkgs,
            color=(["rgba(0,232,122,0.7)"] * len(files) +
                   ["rgba(75,158,255,0.7)"] * len(pkgs)),
            hovertemplate="<b>%{label}</b><br>%{value} import(s)<extra></extra>",
        ),
        link=dict(
            source=[k[0] for k in counts],
            target=[k[1] for k in counts],
            value=list(counts.values()),
            color="rgba(166,124,255,0.15)",
            hovertemplate="%{source.label} → %{target.label}<br>%{value}<extra></extra>",
        ),
        textfont=dict(color=TEXT, size=10, family="JetBrains Mono"),
    ))
    fig.update_layout(
        paper_bgcolor=BG, height=480,
        margin=dict(l=10, r=10, t=10, b=10),
        font=dict(color=TEXT, family="JetBrains Mono"))
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

    # ── 1. Request / Response Flow ─────────────────────────────────────
    with tab_req:
        st.markdown(
            '<div style="font-size:9px;letter-spacing:2px;color:#505070;margin-bottom:8px">'
            'REQUEST / RESPONSE FLOW — real names from the analyzed repo</div>',
            unsafe_allow_html=True,
        )

        # Legend row
        legend_items = [
            ("CLIENT / RESPONSE", GREEN),
            ("ROUTER / HANDLER",  PURPLE),
            ("SERVICE LAYER",     BLUE),
            ("DATA / DB",         ORANGE),
        ]
        cols = st.columns(len(legend_items))
        for col, (label, color) in zip(cols, legend_items):
            with col:
                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:6px;padding:5px 10px;'
                    f'border-radius:20px;border:1px solid rgba({_rgb(color)},0.3);'
                    f'background:rgba({_rgb(color)},0.06);justify-content:center;">'
                    f'<span style="width:7px;height:7px;border-radius:50%;background:{color};'
                    f'flex-shrink:0;display:inline-block;"></span>'
                    f'<span style="font-size:9px;color:{color};letter-spacing:0.5px;">{label}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

        st.markdown("")
        st.plotly_chart(_build_req_flow(result), use_container_width=True,
                        config={"displayModeBar": False})

        # Written walkthrough
        st.markdown("---")
        st.markdown("**Step-by-step walkthrough**")

        routes  = result.routes
        arch    = result.arch
        stack   = result.stack

        def _ln(key):
            for lyr in arch.layers:
                if lyr.key == key:
                    return [n.label for n in lyr.nodes[:3]]
            return []

        steps = [
            ("1 · Client sends request",
             "An HTTP request originates from the client (browser / API consumer / SDK).",
             GREEN),
            ("2 · Router matches URL",
             (f"Matched against **{len(routes)}** defined route(s). "
              f"Example: `{routes[0].method} {routes[0].path}`" if routes
              else "URL matched to a registered route handler."),
             PURPLE),
            ("3 · Handler runs",
             (f"Handler in `{_ln('entry')[0]}` validates input and calls the service layer."
              if _ln("entry") else "Handler validates input and calls the service layer."),
             PURPLE),
            ("4 · Service applies business logic",
             (f"Business logic in `{_ln('service')[0]}` orchestrates data access and rules."
              if _ln("service") else "Service layer applies business rules and orchestration."),
             BLUE),
            ("5 · Data layer queries store",
             (f"`{_ln('data')[0]}` queries {stack.database or 'the database'} and returns results."
              if _ln("data") else f"Data layer queries {stack.database or 'the data store'}."),
             ORANGE),
            ("6 · Response returned to client",
             "Results pass back up: data → service → handler → serialized to JSON/HTML → client.",
             GREEN),
        ]

        for title, body, color in steps:
            c_dot, c_txt = st.columns([0.02, 0.98])
            with c_dot:
                st.markdown(
                    f'<div style="width:9px;height:9px;border-radius:50%;'
                    f'background:{color};margin-top:8px;"></div>',
                    unsafe_allow_html=True,
                )
            with c_txt:
                st.markdown(f"**{title}**")
                st.markdown(body)

    # ── 2. Architecture Map ─────────────────────────────────────────────
    with tab_arch:
        st.markdown(
            '<div style="font-size:9px;letter-spacing:2px;color:#505070;margin-bottom:8px">'
            'ARCHITECTURE MAP — hover nodes for file details</div>',
            unsafe_allow_html=True,
        )
        st.plotly_chart(_build_arch_map(result), use_container_width=True,
                        config={"displayModeBar": False})

        # Layer summary cards
        layer_cols = st.columns(6)
        for col, layer in zip(layer_cols, result.arch.layers):
            color = LAYER_COLOR.get(layer.key, "#888")
            with col:
                st.markdown(
                    f'<div style="background:{CARD};border:1px solid rgba({_rgb(color)},0.3);'
                    f'border-top:2px solid {color};border-radius:8px;padding:10px;text-align:center;">'
                    f'<div style="font-family:Outfit,sans-serif;font-weight:800;'
                    f'font-size:22px;color:{color}">{len(layer.nodes)}</div>'
                    f'<div style="font-size:8px;color:{MUTED};letter-spacing:1px;margin-top:2px">'
                    f'{layer.label}</div></div>',
                    unsafe_allow_html=True,
                )

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
                f'style="display:inline-flex;align-items:center;gap:4px;padding:3px 9px;'
                f'border-radius:4px;margin:3px;cursor:default;'
                f'border:1px solid rgba({_rgb(color)},0.3);'
                f'color:{color};background:rgba({_rgb(color)},0.07);font-size:10px;">'
                f'<span style="width:5px;height:5px;border-radius:50%;background:{color};'
                f'display:inline-block;flex-shrink:0;"></span>'
                f'{html_lib.escape(nd.label)}</span>'
                for nd in layer.nodes
            )
            st.markdown(f'<div style="display:flex;flex-wrap:wrap;">{pills}</div>',
                        unsafe_allow_html=True)

    # ── 3. Import Flow ───────────────────────────────────────────────────
    with tab_import:
        st.markdown(
            '<div style="font-size:9px;letter-spacing:2px;color:#505070;margin-bottom:8px">'
            'IMPORT FLOW — source files (green) to external packages (blue)</div>',
            unsafe_allow_html=True,
        )

        fig_sankey = _build_sankey(result)
        if fig_sankey:
            st.plotly_chart(fig_sankey, use_container_width=True,
                            config={"displayModeBar": False})
        else:
            st.info("Not enough import data to render the diagram.")

        # Package bar chart
        pkg_counts: dict[str, int] = {}
        for imp in result.imports:
            if imp.local:
                continue
            pkg = ("/".join(imp.name.split("/")[:2]) if imp.name.startswith("@")
                   else imp.name.split("/")[0])
            pkg_counts[pkg] = pkg_counts.get(pkg, 0) + 1

        if pkg_counts:
            st.markdown("**Most imported packages**")
            top = sorted(pkg_counts.items(), key=lambda x: -x[1])[:10]
            for pkg, cnt in top:
                bar_w = int(cnt / top[0][1] * 100)
                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:5px;">'
                    f'<span style="color:{TEXT};font-size:11px;width:160px;overflow:hidden;'
                    f'text-overflow:ellipsis;white-space:nowrap;">{html_lib.escape(pkg)}</span>'
                    f'<div style="flex:1;background:{BORDER};border-radius:3px;height:6px;">'
                    f'<div style="width:{bar_w}%;background:{BLUE};border-radius:3px;height:6px;">'
                    f'</div></div>'
                    f'<span style="color:{MUTED};font-size:10px;width:28px;text-align:right;">'
                    f'{cnt}</span></div>',
                    unsafe_allow_html=True,
                )
