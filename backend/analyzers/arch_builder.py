"""
RepoLens — Architecture Builder
Constructs the layered architecture model and call chains
from parsed code data.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from config.settings import MAX_NODES_PER_LAYER
from backend.parsers.code_parser import (
    ClassDef, FunctionDef, Route, CallEdge, Import,
)
from backend.analyzers.stack_detector import StackInfo


# ── Data classes ──────────────────────────────────────────────────────────────
@dataclass
class ArchNode:
    label:  str
    layer:  str          # 'entry' | 'ctrl' | 'service' | 'data' | 'util' | 'ext'
    detail: str = ""     # tooltip / source path


@dataclass
class ArchLayer:
    key:   str
    label: str
    desc:  str
    nodes: list[ArchNode] = field(default_factory=list)


@dataclass
class FlowEdge:
    src:  str
    dst:  str
    desc: str


@dataclass
class ArchModel:
    layers: list[ArchLayer]
    flows:  list[FlowEdge]


@dataclass
class ChainStep:
    fn:   str
    cls:  str
    file: str
    desc: str


@dataclass
class CallChain:
    name:    str
    trigger: str
    steps:   list[ChainStep]


# ── File-to-layer classifier ──────────────────────────────────────────────────
def layer_of(path: str) -> str:
    p = path.lower()
    f = p.rsplit("/", 1)[-1]
    fname = f.rsplit(".", 1)[0] if "." in f else f

    # Entry / routing
    if re.match(
        r"^(index|app|main|server|manage|wsgi|asgi|run|start|entry|bootstrap|"
        r"application|program|init|__init__|__main__)$",
        fname,
    ):
        return "entry"
    if re.search(r"route|router|endpoint|controller|handler|view|views|urls?", p):
        return "entry"

    # Data
    if re.search(r"model|schema|entity|orm|migration|seed", p):
        return "data"
    if re.search(r"repositor|dao|query|database|db/|storage|store(?!re)", p):
        return "data"
    if re.search(r"[/\\](models|schemas|entities|migrations)[/\\]", p):
        return "data"

    # Services
    if re.search(r"service|use.?case|interactor|business|logic", p):
        return "service"
    if re.search(r"[/\\]services[/\\]", p):
        return "service"

    # Utils / config
    if re.search(r"util|helper|tool|common|shared|constant|config|setting|env", p):
        return "util"
    if re.search(r"[/\\](utils?|helpers?|lib|common|shared|config)[/\\]", p):
        return "util"

    # Middleware
    if re.search(r"middleware|interceptor|guard|pipe", p):
        return "ctrl"

    return "ctrl"


# ── Architecture model builder ────────────────────────────────────────────────
def build_arch_model(
    file_map:   dict[str, str],
    classes:    list[ClassDef],
    imports:    list[Import],
    routes:     list[Route],
    stack:      StackInfo,
) -> ArchModel:

    LAYER_KEYS  = ["entry", "ctrl", "service", "data", "util", "ext"]
    LAYER_META  = {
        "entry":   ("ENTRY / ROUTES",      "Routers, controllers, URL mappings, API entry points"),
        "ctrl":    ("CONTROLLERS / LOGIC", "Middleware, business logic, request handlers"),
        "service": ("SERVICES",            "Service classes, use-cases, domain logic"),
        "data":    ("DATA / MODELS",       "ORM models, repositories, DB queries, schemas"),
        "util":    ("UTILS / CONFIG",      "Helpers, config, constants, shared utilities"),
        "ext":     ("EXTERNAL DEPS",       "npm/pip packages, third-party APIs, SDKs"),
    }
    layers = {k: ArchLayer(key=k, label=LAYER_META[k][0], desc=LAYER_META[k][1]) for k in LAYER_KEYS}

    placed_labels: set[str] = set()

    # 1. Place analyzed source files
    skip_manifests = {
        "package.json", "requirements.txt", "go.mod",
        "Cargo.toml", "Gemfile", "composer.json", "README.md",
    }
    for path in file_map:
        if path in skip_manifests:
            continue
        layer = layer_of(path)
        label = re.sub(r"\.(js|ts|jsx|tsx|py|go|rb|php|java|rs|cs|swift|kt)$", "", path.rsplit("/", 1)[-1])
        if not label or label in placed_labels:
            continue
        placed_labels.add(label)
        layers[layer].nodes.append(ArchNode(label=label, layer=layer, detail=path))

    # 2. Add notable class names
    for cls in classes:
        layer = layer_of(cls.file)
        lyr   = layers.get(layer, layers["ctrl"])
        if cls.name not in placed_labels:
            placed_labels.add(cls.name)
            lyr.nodes.append(ArchNode(label=cls.name, layer=layer, detail=f"{cls.file} [class]"))

    # 3. Fill entry from routes if still empty
    if not layers["entry"].nodes and routes:
        route_files = list(dict.fromkeys(
            re.sub(r"\.\w+$", "", r.file.rsplit("/", 1)[-1])
            for r in routes
        ))
        for rf in route_files[:8]:
            if rf not in placed_labels:
                placed_labels.add(rf)
                layers["entry"].nodes.append(ArchNode(label=rf, layer="entry", detail="route file"))

    # 4. External packages
    ext_pkgs = []
    seen_ext: set[str] = set()
    for imp in imports:
        if imp.local:
            continue
        name = imp.name
        pkg  = "/".join(name.split("/")[:2]) if name.startswith("@") else name.split("/")[0]
        if pkg and pkg not in seen_ext:
            seen_ext.add(pkg)
            ext_pkgs.append(pkg)
    for pkg in ext_pkgs[:14]:
        layers["ext"].nodes.append(ArchNode(label=pkg, layer="ext", detail="external package"))

    # 5. Cap layers
    for lyr in layers.values():
        lyr.nodes = lyr.nodes[:MAX_NODES_PER_LAYER]

    # 6. Build flow edges
    flows: list[FlowEdge] = []
    layer_order = [layers["entry"], layers["ctrl"], layers["service"], layers["data"]]
    flow_descs  = ["routes to →", "delegates to →", "queries →"]
    for i in range(len(layer_order) - 1):
        src_lyr = layer_order[i]
        dst_lyr = layer_order[i + 1]
        if src_lyr.nodes and dst_lyr.nodes:
            flows.append(FlowEdge(
                src  = src_lyr.nodes[0].label,
                dst  = dst_lyr.nodes[0].label,
                desc = flow_descs[i] if i < len(flow_descs) else "→",
            ))
    if layers["ctrl"].nodes and layers["ext"].nodes:
        flows.append(FlowEdge(
            src  = layers["ctrl"].nodes[0].label,
            dst  = layers["ext"].nodes[0].label,
            desc = "uses →",
        ))

    return ArchModel(layers=list(layers.values()), flows=flows)


# ── Call chain builder ────────────────────────────────────────────────────────
def build_call_chains(
    call_edges: list[CallEdge],
    functions:  list[FunctionDef],
    routes:     list[Route],
    classes:    list[ClassDef],
) -> list[CallChain]:
    chains: list[CallChain] = []

    # 1. HTTP request lifecycle
    if routes:
        r = routes[0]
        handlers = functions[:5]
        chains.append(CallChain(
            name    = "HTTP Request Lifecycle",
            trigger = f"{r.method} {r.path}",
            steps   = [
                ChainStep("Client Request",       "",  "network",  "Inbound HTTP request arrives"),
                ChainStep("Router / Dispatcher",  "",  "routing",  "URL matched → handler dispatched"),
                *[
                    ChainStep(fn.name, "", fn.file,
                              "Primary handler — processes req & res" if i == 0 else "Helper or middleware")
                    for i, fn in enumerate(handlers)
                ],
                ChainStep("HTTP Response", "", "network", "JSON / HTML returned to client"),
            ],
        ))

    # 2. Top class method chain
    top_cls = max(classes, key=lambda c: len(c.methods), default=None)
    if top_cls and len(top_cls.methods) >= 2:
        chains.append(CallChain(
            name    = f"{top_cls.name} — Class Flow",
            trigger = f"new {top_cls.name}() created",
            steps   = [
                ChainStep("constructor", top_cls.name, top_cls.file,
                          f"Instantiated{' (extends ' + top_cls.parent + ')' if top_cls.parent else ''}"),
                *[
                    ChainStep(m, top_cls.name, top_cls.file,
                              "Private / dunder method" if m.startswith("_") else "Public method")
                    for m in top_cls.methods[:6]
                ],
            ],
        ))

    # 3. Top-caller chain from call graph
    caller_count: dict[str, int] = {}
    for e in call_edges:
        caller_count[e.caller] = caller_count.get(e.caller, 0) + 1

    if caller_count:
        top_caller = max(caller_count, key=caller_count.__getitem__)
        callees    = [e for e in call_edges if e.caller == top_caller][:7]
        if len(callees) >= 2:
            chains.append(CallChain(
                name    = f"{top_caller}() — Execution Chain",
                trigger = f"{top_caller} invoked",
                steps   = [
                    ChainStep(top_caller, "", callees[0].file, "Root function — initiates chain"),
                    *[ChainStep(e.callee, "", e.file, f"Called by {top_caller}") for e in callees],
                ],
            ))

    # 4. Data access flow
    data_fns = [
        fn for fn in functions
        if re.search(r"create|save|insert|update|delete|find|get|fetch|load|read|write|query|select|filter",
                     fn.name, re.IGNORECASE)
    ][:7]
    if len(data_fns) >= 2:
        chains.append(CallChain(
            name    = "Data Access Flow",
            trigger = "Data operation triggered",
            steps   = [
                ChainStep(fn.name, "", fn.file,
                          "READ — fetches from data store"
                          if re.search(r"find|get|fetch|read|load|query|select|filter", fn.name, re.IGNORECASE)
                          else "WRITE — mutates data store")
                for fn in data_fns
            ],
        ))

    # 5. Bootstrap / startup
    init_fns = [
        fn for fn in functions
        if re.match(r"^(init|start|boot|setup|configure|listen|connect|bootstrap|launch|run|main|create|build|register)",
                    fn.name, re.IGNORECASE)
    ][:6]
    if len(init_fns) >= 2:
        chains.append(CallChain(
            name    = "Bootstrap / Startup Sequence",
            trigger = "Process start",
            steps   = [ChainStep(fn.name, "", fn.file, "Initialization step") for fn in init_fns],
        ))

    # 6. Fallback
    if not chains:
        chains.append(CallChain(
            name    = "Module Execution Flow",
            trigger = "Entry point",
            steps   = [ChainStep(fn.name, "", fn.file, "Called in sequence") for fn in functions[:7]],
        ))

    return chains
