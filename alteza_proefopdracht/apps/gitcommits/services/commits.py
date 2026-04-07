from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from .. import github

DEFAULT_COMMITS_PER_PAGE = 6
SCAN_PER_PAGE = 100
MAX_SCAN_PAGES_AUTHOR = 50
MAX_SCAN_PAGES_GROUPED = 200


@dataclass
class CommitPage:
    results: list[dict[str, Any]]
    count: int | None
    page: int
    has_next: bool
    has_prev: bool
    grouped: bool


def get_flat_commits(
    repo: str,
    branch: str | None,
    since: datetime,
    until: datetime,
    token: str | None,
    page: int,
) -> CommitPage:
    commits, total = github.get_branch_commits(
        repo_name=repo,
        branch_name=branch,
        since=since,
        until=until,
        token=token,
        page=page,
    )
    commits.sort(
        key=lambda c: c.date or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )
    return CommitPage(
        results=[_serialize_commit(c) for c in commits],
        count=total,
        page=page,
        has_next=page * DEFAULT_COMMITS_PER_PAGE < total,
        has_prev=page > 1,
        grouped=False,
    )


def get_author_filtered_commits(
    repo: str,
    branch: str | None,
    since: datetime,
    until: datetime,
    token: str | None,
    page: int,
    author: str,
) -> CommitPage:
    author_norm = author.strip().lower()
    want_start = (page - 1) * DEFAULT_COMMITS_PER_PAGE
    want_end_exclusive = want_start + DEFAULT_COMMITS_PER_PAGE
    matched: list = []
    scan_page = 1
    total_unfiltered: int | None = None

    while len(matched) <= want_end_exclusive and scan_page <= MAX_SCAN_PAGES_AUTHOR:
        batch, batch_total = github.get_branch_commits(
            repo_name=repo,
            branch_name=branch,
            since=since,
            until=until,
            token=token,
            page=scan_page,
            per_page=SCAN_PER_PAGE,
        )
        if total_unfiltered is None:
            total_unfiltered = batch_total
        if not batch:
            break
        matched.extend(
            c for c in batch if (c.author or "").strip().lower() == author_norm
        )
        if total_unfiltered and scan_page * SCAN_PER_PAGE >= total_unfiltered:
            break
        scan_page += 1

    page_commits = matched[want_start:want_end_exclusive]
    page_commits.sort(
        key=lambda c: c.date or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )

    return CommitPage(
        results=[_serialize_commit(c) for c in page_commits],
        count=None,
        page=page,
        has_next=len(matched) > want_end_exclusive,
        has_prev=page > 1,
        grouped=False,
    )


def get_grouped_by_author(
    repo: str,
    branch: str | None,
    since: datetime,
    until: datetime,
    token: str | None,
    page: int,
) -> CommitPage:
    author_stats: dict[str, dict[str, Any]] = {}
    scan_page = 1
    total_unfiltered: int | None = None

    while scan_page <= MAX_SCAN_PAGES_GROUPED:
        batch, batch_total = github.get_branch_commits(
            repo_name=repo,
            branch_name=branch,
            since=since,
            until=until,
            token=token,
            page=scan_page,
            per_page=SCAN_PER_PAGE,
        )
        if total_unfiltered is None:
            total_unfiltered = batch_total
        if not batch:
            break
        _accumulate_author_stats(author_stats, batch)
        if total_unfiltered and scan_page * SCAN_PER_PAGE >= total_unfiltered:
            break
        scan_page += 1

    grouped = sorted(
        author_stats.values(),
        key=lambda d: (-int(d["count"]), str(d["author"]).lower()),
    )
    start = (page - 1) * DEFAULT_COMMITS_PER_PAGE
    end = start + DEFAULT_COMMITS_PER_PAGE
    page_rows = grouped[start:end]

    return CommitPage(
        results=[_grouped_author_row_to_api(it) for it in page_rows],
        count=len(grouped),
        page=page,
        has_next=end < len(grouped),
        has_prev=page > 1,
        grouped=True,
    )


def _serialize_commit(c: Any) -> dict[str, Any]:
    return {
        "sha": c.commit_hash,
        "sha7": (c.commit_hash or "")[:7],
        "message": c.message,
        "author": c.author or "Unknown",
        "date": c.date.isoformat() if getattr(c, "date", None) else None,
    }


def _serialize_commit_for_group_recent(c: Any) -> dict[str, Any]:
    return {
        "sha": c.commit_hash,
        "sha7": (c.commit_hash or "")[:7],
        "message": c.message,
        "date": c.date.isoformat() if getattr(c, "date", None) else None,
    }


def _accumulate_author_stats(stats: dict[str, dict[str, Any]], batch: list) -> None:
    for c in batch:
        a = (c.author or "Unknown").strip()
        st = stats.get(a)
        if st is None:
            st = {
                "author": a,
                "count": 0,
                "latest_date": None,
                "latest_sha": None,
                "latest_message": None,
                "recent": [],
            }
            stats[a] = st
        st["count"] += 1
        if getattr(c, "date", None) and (
            st["latest_date"] is None or c.date > st["latest_date"]
        ):
            st["latest_date"] = c.date
            st["latest_sha"] = c.commit_hash
            st["latest_message"] = c.message
        st["recent"].append(_serialize_commit_for_group_recent(c))


def _grouped_author_row_to_api(it: dict[str, Any]) -> dict[str, Any]:
    return {
        "author": it["author"],
        "count": it["count"],
        "latest": {
            "sha": it["latest_sha"],
            "sha7": (it["latest_sha"] or "")[:7],
            "message": it["latest_message"],
            "date": it["latest_date"].isoformat() if it["latest_date"] else None,
        },
        "recent": it.get("recent") or [],
    }
