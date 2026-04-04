from github import Github
from github import GithubIntegration
from github import Auth
from github.Repository import Repository
from django.conf import settings

def get_github_client() -> Github:
    # Load the GitHub API key from environment variables
    api_key = settings.GITHUB_API_KEY

    # Create a GitHub client using the API key
    auth = Auth.Token(api_key)
    github_client = Github(auth=auth)

    return github_client

def get_repository(repo_name: str) -> Repository | None:
    github_client = get_github_client()
    try:
        repo = github_client.get_repo(repo_name)
        return repo
    except Exception as e:
        print(f"Error fetching repository: {e}")
        return None