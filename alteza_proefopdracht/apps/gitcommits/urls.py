from django.urls import path

from .views import IndexView, RepoSuggestView

urlpatterns = [
    path("", IndexView.as_view(), name="index"),
    path("api/repo-suggest/", RepoSuggestView.as_view(), name="repo_suggest"),
]
