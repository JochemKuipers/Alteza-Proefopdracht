from django.utils import timezone

import pytest
from alteza_proefopdracht.apps.gitcommits.github import (
    get_branch_commits,
    get_github_client,
    get_repository,
    get_repository_branches,
)

repo_name = "django/django"

client = get_github_client()


@pytest.mark.django_db
def test_get_repo():
    repo = get_repository(repo_name)
    assert repo is not None
    assert repo.full_name == repo_name


@pytest.mark.django_db
def test_get_repo_invalid():
    with pytest.raises(Exception):
        get_repository("invalid/repo")


@pytest.mark.django_db
def test_get_repo_branches():
    repo = get_repository(repo_name)
    if repo is None:
        assert False, "Repository should not be None"
    branches = get_repository_branches(repo_name)
    assert branches is not None
    assert len(branches) > 0


@pytest.mark.django_db
def test_get_branch_commits():
    repo = get_repository(repo_name)
    if repo is None:
        assert False, "Repository should not be None"
    branches = get_repository_branches(repo_name)
    if branches is None or len(branches) == 0:
        assert False, "Branches should not be empty"
    branch = branches[0]
    commits, _ = get_branch_commits(repo_name, branch.name)
    assert commits is not None
    assert len(list(commits)) > 0


@pytest.mark.django_db
def test_get_first_commit_message():
    repo = get_repository(repo_name)
    if repo is None:
        assert False, "Repository should not be None"
    branches = get_repository_branches(repo_name)
    if branches is None or len(branches) == 0:
        assert False, "Branches should not be empty"
    branch_name = branches[0].name
    commits, _ = get_branch_commits(repo_name, branch_name)
    if commits is None or len(list(commits)) == 0:
        assert False, "Commits should not be empty"
    first_commit = commits[0]
    assert first_commit.message is not None


@pytest.mark.django_db
def test_get_first_commit_author():
    repo = get_repository(repo_name)
    if repo is None:
        assert False, "Repository should not be None"
    branches = get_repository_branches(repo_name)
    if branches is None or len(branches) == 0:
        assert False, "Branches should not be empty"
    branch_name = branches[0].name
    commits, _ = get_branch_commits(repo_name, branch_name)
    if commits is None or len(list(commits)) == 0:
        assert False, "Commits should not be empty"
    first_commit = commits[0]
    assert first_commit.author is not None


@pytest.mark.django_db
def test_get_first_commit_date():
    repo = get_repository(repo_name)
    if repo is None:
        assert False, "Repository should not be None"
    branches = get_repository_branches(repo_name)
    if branches is None or len(branches) == 0:
        assert False, "Branches should not be empty"
    branch_name = branches[0].name
    commits, _ = get_branch_commits(repo_name, branch_name)
    if commits is None or len(list(commits)) == 0:
        assert False, "Commits should not be empty"
    first_commit = commits[0]
    assert first_commit.date is not None


@pytest.mark.django_db
def test_get_commits_since_date():
    repo = get_repository(repo_name)
    if repo is None:
        assert False, "Repository should not be None"
    branches = get_repository_branches(repo_name)
    if branches is None or len(branches) == 0:
        assert False, "Branches should not be empty"
    branch_name = branches[0].name
    since_date = timezone.now().replace(year=2024, month=1, day=1)
    commits, _ = get_branch_commits(repo_name, branch_name, since=since_date)
    assert commits is not None
    for commit in commits:
        assert commit.date > since_date


@pytest.mark.django_db
def test_get_commits_until_date():
    repo = get_repository(repo_name)
    if repo is None:
        assert False, "Repository should not be None"
    branches = get_repository_branches(repo_name)
    if branches is None or len(branches) == 0:
        assert False, "Branches should not be empty"
    branch_name = branches[0].name
    until_date = timezone.now().replace(year=2024, month=1, day=1)
    commits, _ = get_branch_commits(repo_name, branch_name, until=until_date)
    assert commits is not None
    for commit in commits:
        assert commit.date < until_date
