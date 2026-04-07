from django.db.models.query import QuerySet
import pytest

from alteza_proefopdracht.apps.gitcommits.models import GitRepository, GitUser

repo_name = "django/django"
    
@pytest.mark.django_db
def test_git_user_get_repositories():
    user = GitUser(username="JochemKuipers", email="jochem@kuipers.cc")
    repositories = user.get_repositories()
    assert isinstance(repositories, QuerySet)
    assert repositories.count() >= 0
    
@pytest.mark.django_db
def test_git_repository_get_branches():
    repo = GitRepository(name="django", full_name="django/django", url="https://github.com/django/django.git")
    branches = repo.get_branches()
    assert isinstance(branches, QuerySet)
    assert branches.count() >= 0
    
@pytest.mark.django_db
def test_git_repository_get_commits():
    repo = GitRepository(name="django", full_name="django/django", url="https://github.com/django/django.git")
    commits = repo.get_commits()
    assert isinstance(commits, QuerySet)
    assert commits.count() >= 0