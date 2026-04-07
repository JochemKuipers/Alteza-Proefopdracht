from github import Github, Auth
from django.conf import settings

def get_github_client() -> Github:
    # Load the GitHub API key from environment variables
    api_key = settings.GITHUB_API_KEY

    # Create a GitHub client using the API key
    auth = Auth.Token(api_key)
    github_client = Github(auth=auth)

    return github_client

def get_branch_commits(repo_name: str, branch_name: str):
    client = get_github_client()
    repo = client.get_repo(repo_name)
    commits = repo.get_commits(sha=branch_name)
    return list(commits)