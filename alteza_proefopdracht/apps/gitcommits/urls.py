from django.urls import path

from .views import CommitsView, IndexView, RepoSuggestView

urlpatterns = [
    path("", IndexView.as_view(), name="index"),
    path("api/repo-suggest/", RepoSuggestView.as_view(), name="repo_suggest"),
    path("api/commits/", CommitsView.as_view(), name="api_commits"),
]
