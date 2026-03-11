"""
RepoLens — Deep Code Parser
Extracts imports, classes, functions, routes, and middleware
from JS/TS, Python, Go, Rust, Ruby, and more.
"""
from __future__ import annotations

import re
import json
import logging
from dataclasses import dataclass, field
from typing import Optional

log = logging.getLogger(__name__)


# ── Data classes ──────────────────────────────────────────────────────────────
@dataclass
class Import:
    name:  str
    file:  str
    local: bool    # True if starts with . or /
    how:   str     # 'esm', 'cjs', 'py', 'go', 'rust'


@dataclass
class ClassDef:
    name:    str
    file:    str
    parent:  Optional[str]
    methods: list[str] = field(default_factory=list)
    lang:    str = "unknown"

    @property
    def is_private(self) -> bool:
        return self.name.startswith("_")


@dataclass
class FunctionDef:
    name: str
    file: str

    @property
    def is_private(self) -> bool:
        return self.name.startswith("_") or self.name.startswith("__")


@dataclass
class Route:
    method:  str
    path:    str
    file:    str
    handler: str = ""

    def dedup_key(self) -> str:
        return f"{self.method}:{self.path}"


@dataclass
class CallEdge:
    caller: str
    callee: str
    file:   str


# ── Skip sets for function name noise ────────────────────────────────────────
_FN_SKIP = frozenset({
    "if", "for", "while", "switch", "catch", "else", "return", "new",
    "typeof", "void", "delete", "in", "of", "async", "from", "import",
    "export", "class", "interface", "describe", "it", "test", "expect",
    "beforeEach", "afterEach", "beforeAll", "afterAll", "get", "set",
    "use", "all", "let", "var", "const", "try", "do", "yield",
})


# ═════════════════════════════════════════════════════════════════════════════
#  IMPORTS
# ═════════════════════════════════════════════════════════════════════════════
def parse_imports(src: str, file: str) -> list[Import]:
    out: list[Import] = []
    seen: set[str] = set()

    def add(name: str, how: str) -> None:
        name = name.strip()
        if not name or name in seen:
            return
        seen.add(name)
        local = name.startswith(".") or name.startswith("/")
        out.append(Import(name=name, file=file, local=local, how=how))

    # ES6: import X from 'y' / import 'y' / import type X from 'y'
    for m in re.finditer(r"""import\s+(?:type\s+)?(?:[\w{},*\s]+?\bfrom\b\s+)?['"]([^'"]+)['"]""", src):
        add(m.group(1), "esm")

    # CommonJS: require('x')
    for m in re.finditer(r"""require\s*\(\s*['"]([^'"]+)['"]\s*\)""", src):
        add(m.group(1), "cjs")

    # Python: from x import y
    for m in re.finditer(r"^from\s+([\w.]+)\s+import\s+", src, re.MULTILINE):
        add(m.group(1), "py")

    # Python: import x, y, z  (skip JS "import X from Y" lines)
    for m in re.finditer(r"^import\s+((?!.*\bfrom\b)[\w.,\s]+?)(?:\s*(?:#|;|$))", src, re.MULTILINE):
        for part in m.group(1).split(","):
            name = part.strip().split(" as ")[0].strip().split(".")[0]
            if name:
                add(name, "py")

    # Go: import block
    for block in re.finditer(r'import\s*\(([^)]+)\)', src):
        for line in block.group(1).splitlines():
            gm = re.search(r'"([^"]+)"', line)
            if gm:
                add(gm.group(1), "go")

    # Go: single import
    for m in re.finditer(r'^import\s+"([^"]+)"', src, re.MULTILINE):
        add(m.group(1), "go")

    # Rust: use x::y;
    for m in re.finditer(r"^use\s+([\w:]+)", src, re.MULTILINE):
        add(m.group(1).split("::")[0], "rust")

    return out


# ═════════════════════════════════════════════════════════════════════════════
#  CLASSES
# ═════════════════════════════════════════════════════════════════════════════
def parse_classes(src: str, file: str) -> list[ClassDef]:
    out:  list[ClassDef] = []
    seen: set[str] = set()

    _METHOD_SKIP = frozenset({"if", "for", "while", "switch", "catch", "constructor", "super"})

    # ── JavaScript / TypeScript ───────────────────────────────────────────
    for m in re.finditer(r"class\s+([A-Z][A-Za-z0-9_$]*)[^{]*\{", src):
        name = m.group(1)
        if name in seen:
            continue
        seen.add(name)

        snippet = src[m.start(): m.start() + 3000]
        parent_m = re.search(r"extends\s+([A-Za-z0-9_$<>]+)", src[m.start(): m.start() + 100])
        parent   = parent_m.group(1) if parent_m else None

        methods: list[str] = []
        for mm in re.finditer(
            r"(?:async\s+)?(?:static\s+)?(?:public\s+|private\s+|protected\s+)?"
            r"(?:get\s+|set\s+)?([a-z_$][A-Za-z0-9_$]*)\s*\([^)]*\)\s*(?::\s*[\w<>\[\]|&]+\s*)?\{",
            snippet,
        ):
            mn = mm.group(1)
            if mn not in _METHOD_SKIP:
                methods.append(mn)

        out.append(ClassDef(
            name=name, file=file, parent=parent,
            methods=list(dict.fromkeys(methods))[:15], lang="js",
        ))

    # ── Python ───────────────────────────────────────────────────────────
    for m in re.finditer(r"^class\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?:\(([^)]*)\))?:", src, re.MULTILINE):
        name = m.group(1)
        if name in seen:
            continue
        seen.add(name)

        raw_parent = (m.group(2) or "").strip()
        parent     = raw_parent.split(",")[0].strip().split("(")[0] or None
        if parent in ("object", ""):
            parent = None

        snippet = src[m.start(): m.start() + 3000]
        methods: list[str] = []
        for mm in re.finditer(r"^\s{4}(?:async\s+)?def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", snippet, re.MULTILINE):
            methods.append(mm.group(1))

        out.append(ClassDef(
            name=name, file=file, parent=parent,
            methods=list(dict.fromkeys(methods))[:15], lang="py",
        ))

    # ── Go structs (treated as classes) ─────────────────────────────────
    for m in re.finditer(r"^type\s+([A-Z][A-Za-z0-9_]*)\s+struct\s*\{", src, re.MULTILINE):
        name = m.group(1)
        if name in seen:
            continue
        seen.add(name)
        # Find methods on this struct
        methods: list[str] = []
        for mm in re.finditer(
            rf"^func\s+\(\w+\s+\*?{re.escape(name)}\)\s+([A-Za-z][A-Za-z0-9_]*)\s*\(",
            src, re.MULTILINE,
        ):
            methods.append(mm.group(1))
        out.append(ClassDef(name=name, file=file, parent=None, methods=methods[:15], lang="go"))

    return out


# ═════════════════════════════════════════════════════════════════════════════
#  FUNCTIONS
# ═════════════════════════════════════════════════════════════════════════════
def parse_functions(src: str, file: str) -> list[FunctionDef]:
    out:  list[FunctionDef] = []
    seen: set[str] = set()

    def add(name: str) -> None:
        if name and len(name) > 1 and name not in seen and name not in _FN_SKIP and not name[0].isupper():
            seen.add(name)
            out.append(FunctionDef(name=name, file=file))

    patterns = [
        # JS/TS named function declaration
        r"(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s*\*?\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*[<(]",
        # Arrow / expression
        r"(?:export\s+)?(?:const|let|var)\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>",
        r"(?:export\s+)?(?:const|let|var)\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*=\s*(?:async\s*)?function",
        # Python top-level def
        r"^(?:async\s+)?def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(",
        # Python indented method (4 spaces)
        r"^    (?:async\s+)?def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(",
        # Go function
        r"^func\s+(?:\(\w+\s+\*?[A-Za-z0-9_]+\)\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*\(",
        # Rust fn
        r"^(?:pub\s+)?(?:async\s+)?fn\s+([A-Za-z_][A-Za-z0-9_]*)\s*[<(]",
        # Ruby def
        r"^  ?def\s+([A-Za-z_][A-Za-z0-9_?!]*)",
    ]

    for pattern in patterns:
        for m in re.finditer(pattern, src, re.MULTILINE):
            add(m.group(1))

    return out


# ═════════════════════════════════════════════════════════════════════════════
#  ROUTES
# ═════════════════════════════════════════════════════════════════════════════
def parse_routes(src: str, file: str) -> list[Route]:
    out:  list[Route] = []
    seen: set[str] = set()

    def add(method: str, path: str, handler: str = "") -> None:
        key = f"{method}:{path}"
        if key not in seen:
            seen.add(key)
            out.append(Route(method=method.upper(), path=path, file=file, handler=handler))

    http_methods = ["get", "post", "put", "delete", "patch", "options", "head", "use", "all"]

    # Express / Fastify / Koa / Hapi
    for method in http_methods:
        pattern = (
            r"(?:app|router|server|this|fastify|koa|hapi|r|api|route|handler)"
            r"\s*\.\s*" + re.escape(method) + r"""\s*\(\s*['"`]([^'"`\s]+)['"`]"""
        )
        for m in re.finditer(pattern, src, re.IGNORECASE):
            add(method, m.group(1))

    # NestJS / TypeScript decorators: @Get('/path'), @Post()
    for m in re.finditer(
        r"@(Get|Post|Put|Delete|Patch|All|Options|Head)\s*\(\s*(?:['\"`]([^'\"`]*)['\"`])?\s*\)",
        src,
    ):
        add(m.group(1), m.group(2) or "/")

    # Flask: @app.route('/path', methods=['GET','POST'])
    for m in re.finditer(
        r"@[\w.]+\.route\s*\(\s*['\"]([^'\"]+)['\"](?:[^)]*methods\s*=\s*\[([^\]]+)\])?",
        src,
    ):
        raw_methods = m.group(2)
        methods = (
            [x.strip().strip("'\"").upper() for x in raw_methods.split(",")]
            if raw_methods else ["GET"]
        )
        for mt in methods:
            add(mt, m.group(1))

    # FastAPI / APIRouter: @app.get('/path'), @router.post('/path')
    for m in re.finditer(
        r"@(?:app|router|api_router)\.(get|post|put|delete|patch)\s*\(\s*['\"]([^'\"]+)['\"]",
        src,
        re.IGNORECASE,
    ):
        add(m.group(1), m.group(2))

    # Django path() / re_path() in urls.py
    if "urls" in file.lower() or "url" in file.lower():
        for m in re.finditer(
            r"""(?:path|re_path|url)\s*\(\s*[r]?['"](.*?)['"](?:\s*,\s*([A-Za-z_][\w.]*(?:\.as_view\(\))?))?\s*""",
            src,
        ):
            add("URL", m.group(1), m.group(2) or "")

    # Go net/http
    for m in re.finditer(
        r"""(?:http|mux|r|router)\s*\.\s*Handle(?:Func)?\s*\(\s*['"]([^'"]+)['"]""",
        src,
    ):
        add("HANDLE", m.group(1))

    # Gin (Go): r.GET("/path", handler)
    for m in re.finditer(
        r"""\b(?:r|router|engine)\s*\.\s*(GET|POST|PUT|DELETE|PATCH)\s*\(\s*['"]([^'"]+)['"]""",
        src,
    ):
        add(m.group(1), m.group(2))

    return out


# ═════════════════════════════════════════════════════════════════════════════
#  MIDDLEWARE
# ═════════════════════════════════════════════════════════════════════════════
def parse_middleware(src: str) -> list[str]:
    out: set[str] = set()

    # Express app.use(name) or app.use('/path', name)
    for m in re.finditer(
        r"""(?:app|router)\s*\.\s*use\s*\(\s*(?:['"`][^'"`]+['"`]\s*,\s*)?([A-Za-z_$][A-Za-z0-9_.()$]*)\s*[,)]""",
        src,
    ):
        name = m.group(1).split("(")[0].split(".")[-1].strip()
        if name and re.match(r"^[A-Za-z]", name) and len(name) < 40 and name not in ("function", "async", "require"):
            out.add(name)

    # Django MIDDLEWARE list strings
    for m in re.finditer(r"""['\"]([\w.]+Middleware)['\"]""", src):
        out.add(m.group(1).split(".")[-1])

    return sorted(out)


# ═════════════════════════════════════════════════════════════════════════════
#  CALL GRAPH
# ═════════════════════════════════════════════════════════════════════════════
def build_call_graph(file_src_map: dict[str, str], all_functions: list[FunctionDef]) -> list[CallEdge]:
    """
    Build a call graph: for each function in a file, find which other
    known functions it calls (based on regex body search).
    """
    fn_set   = {fn.name for fn in all_functions}
    edges:    list[CallEdge] = []
    seen_e:  set[tuple[str, str]] = set()

    for file, src in file_src_map.items():
        my_fns = [fn for fn in all_functions if fn.file == file]
        for fn in my_fns:
            # Rough body extraction: from first occurrence forward
            idx = src.find(fn.name)
            if idx < 0:
                continue
            body = src[idx: idx + 2500]
            for target in fn_set:
                if target == fn.name:
                    continue
                if re.search(rf"\b{re.escape(target)}\s*\(", body):
                    key = (fn.name, target)
                    if key not in seen_e:
                        seen_e.add(key)
                        edges.append(CallEdge(caller=fn.name, callee=target, file=file))

    return edges


# ═════════════════════════════════════════════════════════════════════════════
#  PACKAGE.JSON PARSER
# ═════════════════════════════════════════════════════════════════════════════
def parse_package_json(content: str) -> Optional[dict]:
    try:
        return json.loads(content)
    except Exception:
        return None
