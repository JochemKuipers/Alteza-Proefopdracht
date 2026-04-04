from django.test import TestCase
import pytest
from .github import get_github_client

repo_name = "JochemKuipers/Alteza-Proefopdracht"

client = get_github_client()

def test_get_repo():
    repo = client.get_repo(repo_name)
    assert repo is not None
    assert repo.full_name == repo_name
    
def test_get_repo_invalid():
    with pytest.raises(Exception):
        client.get_repo("invalid/repo")
    
def test_get_repo_branches():
    repo = client.get_repo(repo_name)
    if repo is None:
        assert False, "Repository should not be None"
    branches = repo.get_branches()
    assert branches is not None
    assert len(list(branches)) > 0
    
def test_get_branch_commits():
    repo = client.get_repo(repo_name)
    if repo is None:
        assert False, "Repository should not be None"
    branches = repo.get_branches()
    if branches is None or len(list(branches)) == 0:
        assert False, "Branches should not be empty"
    branch = branches[0]
    commits = branch.commit
    assert commits is not None
    assert len(list(commits)) > 0
    
def test_get_first_commit_message():
    repo = client.get_repo(repo_name)
    if repo is None:
        assert False, "Repository should not be None"
    branches = repo.get_branches()
    if branches is None or len(list(branches)) == 0:
        assert False, "Branches should not be empty"
    branch_name = branches[0].name
    commits = repo.get_commits(sha=branch_name)
    if commits is None or len(list(commits)) == 0:
        assert False, "Commits should not be empty"
    first_commit = commits[0]
    assert first_commit.commit.message is not None