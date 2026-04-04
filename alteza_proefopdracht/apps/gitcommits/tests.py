from django.test import TestCase
import pytest
from .github import get_branch_commits, get_branches, get_repository

repo_name = "JochemKuipers/Alteza-Proefopdracht"

def test_get_repo():
    repo = get_repository(repo_name)
    assert repo is not None
    assert repo.full_name == repo_name
    
def test_get_repo_invalid():
    repo = get_repository("invalid/repo")
    assert repo is None
    
def test_get_repo_branches():
    repo = get_repository(repo_name)
    if repo is None:
        assert False, "Repository should not be None"
    branches = get_branches(repo)
    assert branches is not None
    assert len(list(branches)) > 0
    
def test_get_branch_commits():
    repo = get_repository(repo_name)
    if repo is None:
        assert False, "Repository should not be None"
    branches = get_branches(repo)
    if branches is None or len(list(branches)) == 0:
        assert False, "Branches should not be empty"
    branch_name = branches[0].name
    commits = get_branch_commits(repo, branch_name)
    assert commits is not None
    assert len(list(commits)) > 0
    
def test_get_first_commit_message():
    repo = get_repository(repo_name)
    if repo is None:
        assert False, "Repository should not be None"
    branches = get_branches(repo)
    if branches is None or len(list(branches)) == 0:
        assert False, "Branches should not be empty"
    branch_name = branches[0].name
    commits = get_branch_commits(repo, branch_name)
    if commits is None or len(list(commits)) == 0:
        assert False, "Commits should not be empty"
    first_commit = commits[0]
    assert first_commit.commit.message is not None