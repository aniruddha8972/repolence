"""
RepoLens — GitHub API Client
Handles all communication with GitHub REST API and raw.githubusercontent.com.
"""
from __future__ import annotations

import re
import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Optional

import requests

from config.settings import (
    GH_API_BASE, GH_RAW_BASE, GH_API_HDRS,
    MAX_FILES_TO_FETCH, MAX_FILE_SIZE_BYTES,
    FILE_FETCH_TIMEOUT, API_FETCH_TIMEOUT, FETCH_WORKERS,
)

log = logging.getLogger(__name__)


# ── Data classes ──────────────────────────────────────────────────────────────
@dataclass
class RepoMeta:
    owner:           str
    repo:            str
    full_name:       str
    description:     str
    default_branch:  str
    language:        str
    stars:           int
    forks:           int
    size_kb:         int
    topics:          list[str] = field(default_factory=list)
    homepage:        str = ""
    created_at:      str = ""
    updated_at:      str = ""
    license_name:    str = ""
    open_issues:     int = 0
    watchers:        int = 0

    @classmethod
    def from_api(cls, owner: str, repo: str, data: dict) -> "RepoMeta":
        return cls(
            owner          = owner,
            repo           = repo,
            full_name      = data.get("full_name", f"{owner}/{repo}"),
            description    = data.get("description") or "",
            default_branch = data.get("default_branch", "main"),
            language       = data.get("language") or "Unknown",
            stars          = data.get("stargazers_count", 0),
            forks          = data.get("forks_count", 0),
            size_kb        = data.get("size", 0),
            topics         = data.get("topics", []),
            homepage       = data.get("homepage") or "",
            created_at     = data.get("created_at", ""),
            updated_at     = data.get("updated_at", ""),
            license_name   = (data.get("license") or {}).get("name", ""),
            open_issues    = data.get("open_issues_count", 0),
            watchers       = data.get("watchers_count", 0),
        )


@dataclass
class FetchResult:
    path:    str
    content: str          # empty string means failed / empty
    ok:      bool = True
    error:   str  = ""


# ── URL parser ────────────────────────────────────────────────────────────────
def parse_github_url(url: str) -> Optional[tuple[str, str]]:
    """
    Parse a GitHub URL and return (owner, repo) or None.
    Handles:
      https://github.com/owner/repo
      https://github.com/owner/repo.git
      github.com/owner/repo
    """
    url = url.strip().rstrip("/")
    m = re.search(r"github\.com/([^/\s]+)/([^/\s?#]+)", url)
    if not m:
        return None
    owner = m.group(1)
    repo  = m.group(2).removesuffix(".git")
    return owner, repo


# ── Core HTTP helpers ─────────────────────────────────────────────────────────
def _gh_get(url: str, timeout: int = API_FETCH_TIMEOUT, token: str = "") -> dict:
    headers = dict(GH_API_HDRS)
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        r = requests.get(url, headers=headers, timeout=timeout)
        if r.status_code == 403:
            raise RuntimeError("GitHub rate limit reached. Wait a few minutes or add a token.")
        if r.status_code == 404:
            raise RuntimeError("Repository not found — check the URL or ensure it is public.")
        r.raise_for_status()
        return r.json()
    except requests.exceptions.Timeout:
        raise RuntimeError(f"Request timed out: {url}")
    except requests.exceptions.ConnectionError:
        raise RuntimeError("Network error — check your internet connection.")
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"GitHub API error: {e}") from e


def _raw_get(owner: str, repo: str, branch: str, path: str, token: str = "") -> str:
    """Fetch raw file content from raw.githubusercontent.com."""
    url = f"{GH_RAW_BASE}/{owner}/{repo}/{branch}/{path}"
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        r = requests.get(url, headers=headers, timeout=FILE_FETCH_TIMEOUT)
        if not r.ok:
            return ""
        text = r.text
        if len(text) > MAX_FILE_SIZE_BYTES:
            text = text[:MAX_FILE_SIZE_BYTES]
        return text
    except Exception:
        return ""


# ── Public API ────────────────────────────────────────────────────────────────
def fetch_repo_meta(owner: str, repo: str, token: str = "") -> RepoMeta:
    """Fetch repository metadata."""
    data = _gh_get(f"{GH_API_BASE}/repos/{owner}/{repo}", token=token)
    return RepoMeta.from_api(owner, repo, data)


def fetch_file_tree(owner: str, repo: str, branch: str, token: str = "") -> list[str]:
    """
    Fetch the complete recursive file tree.
    Returns a flat list of file paths.
    Falls back to empty list on error (e.g. very large repos).
    """
    url  = f"{GH_API_BASE}/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
    try:
        data = _gh_get(url, timeout=API_FETCH_TIMEOUT, token=token)
        tree = data.get("tree", [])
        # GitHub may truncate on large repos — flag it
        if data.get("truncated"):
            log.warning("File tree was truncated by GitHub (repo too large).")
        return [n["path"] for n in tree if n.get("type") == "blob"]
    except Exception as e:
        log.warning("Could not fetch full file tree: %s", e)
        return []


def fetch_files_parallel(
    owner:   str,
    repo:    str,
    branch:  str,
    paths:   list[str],
    token:   str = "",
    on_progress=None,     # optional callback(done: int, total: int)
) -> dict[str, str]:
    """
    Fetch multiple files in parallel using a thread pool.
    Returns {path: content} for non-empty files only.
    """
    results: dict[str, str] = {}
    total  = len(paths)
    done   = 0

    def _fetch(path: str) -> FetchResult:
        content = _raw_get(owner, repo, branch, path, token=token)
        return FetchResult(path=path, content=content, ok=bool(content.strip()))

    with ThreadPoolExecutor(max_workers=FETCH_WORKERS) as pool:
        futures = {pool.submit(_fetch, p): p for p in paths}
        for future in as_completed(futures):
            done += 1
            try:
                r = future.result()
                if r.ok:
                    results[r.path] = r.content
            except Exception as e:
                log.debug("File fetch error for %s: %s", futures[future], e)
            if on_progress:
                on_progress(done, total)

    return results


def check_rate_limit(token: str = "") -> dict:
    """Return current GitHub rate limit status."""
    try:
        return _gh_get(f"{GH_API_BASE}/rate_limit", token=token)
    except Exception:
        return {}
