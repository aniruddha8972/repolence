"""
RepoLens — Analysis Engine
Top-level orchestrator that coordinates fetching, parsing,
and building the complete analysis result.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Callable, Optional

from config.settings import MAX_FILES_TO_FETCH
from backend.utils.github_client import (
    fetch_repo_meta, fetch_file_tree, fetch_files_parallel, RepoMeta,
)
from backend.utils.file_selector import select_files, stats_summary
from backend.parsers.code_parser import (
    parse_imports, parse_classes, parse_functions,
    parse_routes, parse_middleware, build_call_graph,
    parse_package_json,
    Import, ClassDef, FunctionDef, Route, CallEdge,
)
from backend.analyzers.stack_detector import detect_stack, StackInfo
from backend.analyzers.arch_builder import (
    build_arch_model, build_call_chains, ArchModel, CallChain,
)

log = logging.getLogger(__name__)


# ── Result dataclass ──────────────────────────────────────────────────────────
@dataclass
class AnalysisResult:
    # Repo metadata
    meta:           RepoMeta

    # File data
    all_files:      list[str]
    analyzed_files: dict[str, str]   # {path: content}
    file_stats:     dict             # total / code / ext_counts

    # Parsed data
    imports:        list[Import]
    classes:        list[ClassDef]
    functions:      list[FunctionDef]
    routes:         list[Route]
    middleware:     list[str]
    call_edges:     list[CallEdge]
    pkg:            Optional[dict]
    readme:         str
    all_src:        str              # concatenated source for pattern matching

    # Analysed data
    stack:          StackInfo
    arch:           ArchModel
    chains:         list[CallChain]

    # Convenience counters
    @property
    def n_files_analyzed(self) -> int:
        return len(self.analyzed_files)

    @property
    def n_functions(self) -> int:
        return len(self.functions)

    @property
    def n_classes(self) -> int:
        return len(self.classes)

    @property
    def n_routes(self) -> int:
        return len(self.routes)

    @property
    def n_ext_packages(self) -> int:
        seen: set[str] = set()
        for imp in self.imports:
            if not imp.local:
                pkg = (
                    "/".join(imp.name.split("/")[:2])
                    if imp.name.startswith("@")
                    else imp.name.split("/")[0]
                )
                seen.add(pkg)
        return len(seen)


# ── Progress helper ───────────────────────────────────────────────────────────
@dataclass
class ProgressUpdate:
    step:    int        # 0–5
    message: str
    pct:     int        # 0–100


ProgressCallback = Callable[[ProgressUpdate], None]


def _noop(_: ProgressUpdate) -> None:
    pass


# ── Main engine ───────────────────────────────────────────────────────────────
def run_analysis(
    owner:    str,
    repo:     str,
    token:    str = "",
    on_progress: ProgressCallback = _noop,
) -> AnalysisResult:
    """
    Run a full analysis of a GitHub repository.
    Calls `on_progress` at each major step.
    Raises RuntimeError with a human-readable message on failure.
    """

    # ── Step 0: Fetch repo metadata ──────────────────────────────────────
    on_progress(ProgressUpdate(0, f"Fetching metadata for {owner}/{repo}…", 5))
    meta = fetch_repo_meta(owner, repo, token=token)
    log.info("Repo: %s  branch=%s  size=%dKB", meta.full_name, meta.default_branch, meta.size_kb)

    # ── Step 1: Fetch file tree ──────────────────────────────────────────
    on_progress(ProgressUpdate(1, "Fetching file tree…", 15))
    all_files = fetch_file_tree(owner, repo, meta.default_branch, token=token)
    log.info("Total files in tree: %d", len(all_files))
    file_stats = stats_summary(all_files)

    # ── Step 2: Select + fetch files ────────────────────────────────────
    to_fetch = select_files(all_files)
    log.info("Selected %d files to fetch", len(to_fetch))

    def _on_file_progress(done: int, total: int) -> None:
        pct = 20 + int(done / max(total, 1) * 38)
        on_progress(ProgressUpdate(2, f"Fetching {done}/{total} files…", min(pct, 58)))

    on_progress(ProgressUpdate(2, f"Fetching {len(to_fetch)} files in parallel…", 20))
    file_map = fetch_files_parallel(
        owner, repo, meta.default_branch, to_fetch,
        token=token, on_progress=_on_file_progress,
    )
    log.info("Fetched %d files with content", len(file_map))

    if len(file_map) < 2:
        raise RuntimeError(
            f"Only {len(file_map)} files could be fetched. "
            "The repository may be private or empty."
        )

    # ── Step 3: Deep parse ───────────────────────────────────────────────
    on_progress(ProgressUpdate(3, "Parsing classes, functions, routes, imports…", 62))

    # Parse package.json / manifests
    pkg    = parse_package_json(file_map.get("package.json", ""))
    readme = file_map.get("README.md", "")

    # Build concatenated source for fast pattern matching (skip binaries/manifests)
    _skip_parse = {
        "package.json", "package-lock.json", "yarn.lock",
        "requirements.txt", "go.mod", "Cargo.toml",
        "Gemfile", "composer.json", "README.md",
    }
    source_files = {p: c for p, c in file_map.items() if p not in _skip_parse}
    all_src      = "\n".join(source_files.values())

    imports:    list[Import]      = []
    classes:    list[ClassDef]    = []
    functions:  list[FunctionDef] = []
    routes:     list[Route]       = []
    middleware: list[str]         = []
    mw_set:     set[str]          = set()

    for path, src in source_files.items():
        imports   .extend(parse_imports(src, path))
        classes   .extend(parse_classes(src, path))
        functions .extend(parse_functions(src, path))
        routes    .extend(parse_routes(src, path))
        for mw in parse_middleware(src):
            mw_set.add(mw)

    middleware = sorted(mw_set)

    # Deduplicate routes
    seen_routes: set[str] = set()
    deduped_routes: list[Route] = []
    for r in routes:
        key = r.dedup_key()
        if key not in seen_routes:
            seen_routes.add(key)
            deduped_routes.append(r)
    routes = deduped_routes

    log.info(
        "Parsed: %d imports, %d classes, %d functions, %d routes",
        len(imports), len(classes), len(functions), len(routes),
    )

    # Build call graph
    call_edges = build_call_graph(source_files, functions)
    log.info("Call graph: %d edges", len(call_edges))

    # ── Step 4: Detect stack & build architecture ────────────────────────
    on_progress(ProgressUpdate(4, "Detecting stack & building architecture graph…", 86))

    stack  = detect_stack(all_files, pkg, all_src)
    arch   = build_arch_model(file_map, classes, imports, routes, stack)
    chains = build_call_chains(call_edges, functions, routes, classes)

    log.info("Stack: lang=%s fw=%s", stack.language, stack.framework)

    # ── Step 5: Done ─────────────────────────────────────────────────────
    on_progress(ProgressUpdate(5, "Analysis complete!", 100))

    return AnalysisResult(
        meta           = meta,
        all_files      = all_files,
        analyzed_files = file_map,
        file_stats     = file_stats,
        imports        = imports,
        classes        = classes,
        functions      = functions,
        routes         = routes,
        middleware     = middleware,
        call_edges     = call_edges,
        pkg            = pkg,
        readme         = readme,
        all_src        = all_src,
        stack          = stack,
        arch           = arch,
        chains         = chains,
    )
