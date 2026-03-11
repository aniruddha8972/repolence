"""
RepoLens — Smart File Selector
Scores every file in the repo tree and picks the most architecturally
significant ones to fetch, up to the configured limit.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from config.settings import (
    CODE_EXTENSIONS, SKIP_PATTERNS, TEST_PATTERNS,
    MAX_FILES_TO_FETCH, PRIORITY_MANIFESTS,
)


@dataclass
class ScoredFile:
    path:  str
    score: int
    ext:   str
    depth: int
    is_test: bool


_SKIP_RE = re.compile("|".join(SKIP_PATTERNS), re.IGNORECASE)
_TEST_RE = re.compile("|".join(TEST_PATTERNS), re.IGNORECASE)


def _get_ext(path: str) -> str:
    parts = path.rsplit(".", 1)
    return parts[1].lower() if len(parts) == 2 else ""


def score_file(path: str) -> int:
    """
    Return an integer priority score for a source file.
    Higher = fetch first.  Returns -1 to skip entirely.
    """
    ext   = _get_ext(path)
    lower = path.lower()
    fname = lower.rsplit("/", 1)[-1]          # filename without directory
    fname_no_ext = fname.rsplit(".", 1)[0] if "." in fname else fname
    depth = path.count("/")

    # Skip non-code files
    if ext not in CODE_EXTENSIONS:
        return -1

    # Skip generated / vendor / cache paths
    if _SKIP_RE.search(path):
        return -1

    score = 50

    # Shallower files are usually more important
    score -= depth * 8

    # High-value entry-point names
    if re.match(
        r"^(index|app|main|server|manage|wsgi|asgi|run|start|bootstrap|entry|"
        r"application|program|init|__init__|__main__)$",
        fname_no_ext,
    ):
        score += 40

    # High-value module names
    if re.match(
        r"^(router|routes|api|controller|handler|endpoint|view|views|"
        r"model|models|schema|schemas|service|services|repository|repositories|"
        r"store|stores|db|database|config|settings|middleware|interceptor)$",
        fname_no_ext,
    ):
        score += 30

    # Path keyword bonuses
    kw_bonuses = [
        (r"route|controller|handler|endpoint|api/",   20),
        (r"model|schema|entity|orm",                  18),
        (r"service|logic|business|use.?case",         16),
        (r"repositor|dao|store|database|db/|query",   16),
        (r"middleware|interceptor|guard",              14),
        (r"src/",                                      12),
        (r"util|helper|shared|common|lib/",             8),
        (r"config|setting|constant|env",               10),
        (r"/v[0-9]+/|/api/",                           14),
        (r"urls\.py",                                  22),   # Django URL conf
        (r"views\.py",                                 20),   # Django views
        (r"models\.py",                                20),   # Django models
        (r"serializer",                                16),   # DRF
        (r"celery|tasks",                              12),   # async tasks
    ]
    for pattern, bonus in kw_bonuses:
        if re.search(pattern, lower):
            score += bonus

    # Test files — still useful but lower priority
    if _TEST_RE.search(lower):
        score -= 20

    return max(score, 0)


def select_files(all_files: list[str], limit: int = MAX_FILES_TO_FETCH) -> list[str]:
    """
    Given the full flat file list from the git tree, return an ordered list
    of up to `limit` paths to fetch — manifests first, then by score.
    """
    # Always grab manifests / README regardless of score
    manifests_present = [f for f in PRIORITY_MANIFESTS if f in set(all_files)]

    # Score the remaining files
    scored: list[ScoredFile] = []
    manifest_set = set(manifests_present)
    for path in all_files:
        if path in manifest_set:
            continue
        s = score_file(path)
        if s < 0:
            continue
        scored.append(ScoredFile(
            path    = path,
            score   = s,
            ext     = _get_ext(path),
            depth   = path.count("/"),
            is_test = bool(_TEST_RE.search(path.lower())),
        ))

    scored.sort(key=lambda x: (-x.score, x.depth, x.path))
    top_code = [sf.path for sf in scored]

    # Combine: manifests first, then top scored
    selected = list(dict.fromkeys([*manifests_present, *top_code]))
    return selected[:limit]


def stats_summary(all_files: list[str]) -> dict:
    """Return simple statistics about the file tree."""
    ext_counts: dict[str, int] = {}
    for f in all_files:
        ext = _get_ext(f)
        ext_counts[ext] = ext_counts.get(ext, 0) + 1

    code_files = [f for f in all_files if _get_ext(f) in CODE_EXTENSIONS and not _SKIP_RE.search(f)]
    return {
        "total":      len(all_files),
        "code":       len(code_files),
        "ext_counts": ext_counts,
    }
