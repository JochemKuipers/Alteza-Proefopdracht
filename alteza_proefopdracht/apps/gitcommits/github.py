from datetime import datetime
from typing import Optional

from github import Github, Auth
from django.conf import settings
from github.GithubObject import Opt

from alteza_proefopdracht.apps.gitcommits.models import GitBranch, GitRepository, GitCommit

DEFAULT_COMMITS_PER_PAGE = 30
MAX_COMMITS_PER_PAGE = 100

def get_github_client(per_page: int = DEFAULT_COMMITS_PER_PAGE) -> Github:
    # Load the GitHub API key from environment variables
    api_key = settings.GITHUB_API_KEY

    # Create a GitHub client using the API key
    auth = Auth.Token(api_key)
    github_client = Github(auth=auth, per_page=per_page)

    return github_client

def get_repository(repo_name: str) -> GitRepository:
    client = get_github_client()
    try:
        repo = client.get_repo(repo_name)
        return GitRepository(name=repo.name, full_name=repo.full_name, url=repo.html_url)
    except Exception as e:
        print(f"Error fetching repository: {e}")
        raise

def get_user_repositories() -> list[GitRepository]:
    client = get_github_client()
    user = client.get_user()
    repositories = user.get_repos()
    
    return [GitRepository(name=repo.name, full_name=repo.full_name, url=repo.html_url) for repo in repositories]

def get_repository_branches(repo_name: str) -> list[GitBranch]:
    client = get_github_client()
    github_repo = client.get_repo(repo_name)
    repo = GitRepository(name=github_repo.name, full_name=github_repo.full_name, url=github_repo.html_url)
    branches = github_repo.get_branches()

    return [GitBranch(repository=repo, name=branch.name) for branch in branches]

def get_branch_commits(
    repo_name: str,
    branch_name: Optional[str],
    since: Opt[datetime] = datetime.min,
    until: Opt[datetime] = datetime.max,
    page: int = 1,
    per_page: int = DEFAULT_COMMITS_PER_PAGE,
) -> list[GitCommit]:
    page = max(page, 1)
    per_page = min(max(per_page, 1), MAX_COMMITS_PER_PAGE)

    client = get_github_client(per_page=per_page)
    github_repo = client.get_repo(repo_name)
    repo = GitRepository(name=github_repo.name, full_name=github_repo.full_name, url=github_repo.html_url)
    commits = github_repo.get_commits(sha=branch_name, since=since, until=until) if branch_name else github_repo.get_commits(since=since, until=until)
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