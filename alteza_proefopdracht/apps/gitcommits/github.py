from github import Github, Auth
from github.Branch import Branch
from github.Repository import Repository
from github.PaginatedList import PaginatedList
from django.conf import settings
from typing import Optional

def get_github_client() -> Github:
    # Load the GitHub API key from environment variables
    api_key = settings.GITHUB_API_KEY

    # Create a GitHub client using the API key
    auth = Auth.Token(api_key)
    github_client = Github(auth=auth)

    return github_client

def get_repository(repo_name: str) -> Optional[Repository]:
    github_client = get_github_client()
    try:
        repo = github_client.get_repo(repo_name)
        return repo
    except Exception as e:
        print(f"Error fetching repository: {e}")
        return None
    
def get_branches(repo: Repository) -> Optional[PaginatedList[Branch]]:
    try:
        branches = repo.get_branches()
        return branches
    except Exception as e:
        print(f"Error fetching branches: {e}")
        return None
    
def get_branch_commits(repo: Repository, branch_name: str) -> Optional[PaginatedList]:
    try:
        commits = repo.get_commits(sha=branch_name)
        return commits
    except Exception as e:
        print(f"Error fetching commits for branch {branch_name}: {e}")
        return None