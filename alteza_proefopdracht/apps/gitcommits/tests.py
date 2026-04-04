from django.test import TestCase
import pytest
from .github import get_repository

repo_name = "JochemKuipers/Alteza-Proefopdracht"

def test_get_repo():
    repo = get_repository(repo_name)
    assert repo is not None
    assert repo.full_name == repo_name