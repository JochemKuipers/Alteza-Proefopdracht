from datetime import datetime
from typing import Optional

from github import Github, Auth
from github.GithubObject import Opt

from alteza_proefopdracht.apps.gitcommits.models import (
    GitBranch,
    GitRepository,
    GitCommit,
)

DEFAULT_COMMITS_PER_PAGE = 30
MAX_COMMITS_PER_PAGE = 100
DEFAULT_REPO_SUGGESTION_LIMIT = 8


def get_github_client(
    *, token: str | None = None, per_page: int = DEFAULT_COMMITS_PER_PAGE
) -> Github:
    if token:
        return Github(auth=Auth.Token(token), per_page=per_page)
    return Github(per_page=per_page)


def search_repositories(
    query: str,
    *,
    token: str | None = None,
    limit: int = DEFAULT_REPO_SUGGESTION_LIMIT,
) -> list[str]:
    query = (query or "").strip()
    if not query:
        return []

    gh_query = f"{query} in:name"
    client = get_github_client(token=token, per_page=min(max(limit, 1), 25))
    results = client.search_repositories(query=gh_query)

    suggestions: list[str] = []
    for repo in results.get_page(0)[:limit]:
        full_name = getattr(repo, "full_name", None)
        if full_name and full_name not in suggestions:
            suggestions.append(full_name)
    return suggestions


def suggest_repositories_for_user(
    query: str,
    *,
    token: str,
    limit: int = DEFAULT_REPO_SUGGESTION_LIMIT,
) -> list[str]:
    query = (query or "").strip().lower()
    if not query:
        return []

    limit = max(limit, 1)
    client = get_github_client(token=token, per_page=100)
    user = client.get_user()

    suggestions: list[str] = []
    seen: set[str] = set()

    for repo in user.get_repos():
        full_name = getattr(repo, "full_name", None)
        if not full_name:
            continue
        if query not in full_name.lower():
            continue
        if full_name in seen:
            continue
        seen.add(full_name)
        suggestions.append(full_name)
        if len(suggestions) >= limit:
            break

    return suggestions


def get_repository(repo_name: str, *, token: str | None = None) -> GitRepository:
    client = get_github_client(token=token)
    try:
        repo = client.get_repo(repo_name)
        return GitRepository(
            name=repo.name, full_name=repo.full_name, url=repo.html_url
        )
    except Exception as e:
        print(f"Error fetching repository: {e}")
        raise


def get_user_repositories(*, token: str | None = None) -> list[GitRepository]:
    client = get_github_client(token=token)
    user = client.get_user()
    repositories = user.get_repos()

    return [
        GitRepository(name=repo.name, full_name=repo.full_name, url=repo.html_url)
        for repo in repositories
    ]


def get_repository_branches(
    repo_name: str, *, token: str | None = None
) -> list[GitBranch]:
    client = get_github_client(token=token)
    github_repo = client.get_repo(repo_name)
    repo = GitRepository(
        name=github_repo.name, full_name=github_repo.full_name, url=github_repo.html_url
    )
    branches = github_repo.get_branches()

    return [GitBranch(repository=repo, name=branch.name) for branch in branches]


def get_branch_commits(
    repo_name: str,
    branch_name: Optional[str],
    since: Opt[datetime] = datetime.min,
    until: Opt[datetime] = datetime.max,
    *,
    token: str | None = None,
    page: int = 1,
    per_page: int = DEFAULT_COMMITS_PER_PAGE,
) -> list[GitCommit]:
    page = max(page, 1)
    per_page = min(max(per_page, 1), MAX_COMMITS_PER_PAGE)

    client = get_github_client(token=token, per_page=per_page)
    github_repo = client.get_repo(repo_name)
    repo = GitRepository(
        name=github_repo.name, full_name=github_repo.full_name, url=github_repo.html_url
    )
    commits = (
        github_repo.get_commits(sha=branch_name, since=since, until=until)
        if branch_name
        else github_repo.get_commits(since=since, until=until)
    )
    commit_page = commits.get_page(page - 1)

    return [
        GitCommit(
            repository=repo,
            commit_hash=commit.sha,
            message=commit.commit.message,
            author=commit.commit.author.name if commit.commit.author else "Unknown",
            date=commit.commit.author.date if commit.commit.author else None,
        )
        for commit in commit_page
    ]
