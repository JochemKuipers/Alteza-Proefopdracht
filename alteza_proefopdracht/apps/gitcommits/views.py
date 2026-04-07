from __future__ import annotations

from datetime import datetime, time, timezone
from typing import cast

from django import forms
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.views import View
from django.views.generic import TemplateView

from allauth.socialaccount.models import SocialToken
from rest_framework.authentication import SessionAuthentication
from rest_framework.response import Response
from rest_framework.views import APIView

from . import github
from .forms import CommitSearchApiForm, CommitSearchForm
from .services.commits import (
    get_author_filtered_commits,
    get_flat_commits,
    get_grouped_by_author,
)

DEFAULT_COMMITS_PER_PAGE = 25
# GitHub commit listing allows up to 100 per page; cap client requests for safety.
MAX_COMMITS_PER_PAGE = 100


def _get_github_oauth_token(user) -> str | None:
    if not user or not getattr(user, "is_authenticated", False):
        return None
    try:
        token = (
            SocialToken.objects.select_related("account")
            .filter(account__user=user, account__provider="github")
            .order_by("-id")
            .first()
        )
        return token.token if token else None
    except Exception:
        return None


class RepoSuggestView(View):
    def get(self, request, *args, **kwargs):
        q = request.GET.get("q", "")
        try:
            items = github.search_repositories(
                q, token=_get_github_oauth_token(request.user)
            )
        except Exception:
            items = []
        return JsonResponse({"items": items})


class CommitsView(APIView):
    """
    DRF paginated endpoint.

    Query params:
    - repo (required): owner/repo
    - branch (optional)
    - start_date / end_date (optional, YYYY-MM-DD)
    - author (optional, exact match)
    - page (default 1)
    - per_page (optional, default 25, max 100)
    """

    authentication_classes = [SessionAuthentication]
    permission_classes: list = []

    def get(self, request, *args, **kwargs):
        repo_name = (request.query_params.get("repo") or "").strip()
        if not repo_name:
            return Response({"detail": "Missing repo"}, status=400)

        form = CommitSearchApiForm(request.query_params)
        if not form.is_valid():
            return Response({"detail": "Invalid parameters", "errors": form.errors}, status=400)

        page, per_page = self._parse_pagination(request)
        since, until = self._parse_dates(form)

        branch = (form.cleaned_data.get("branch") or "").strip() or None
        author = (form.cleaned_data.get("author") or "").strip() or None
        group_by_author = bool(form.cleaned_data.get("group_by_author") or False)
        token = _get_github_oauth_token(request.user)

        try:
            if group_by_author:
                result = get_grouped_by_author(
                    repo_name, branch, since, until, token, page, per_page
                )
            elif author:
                result = get_author_filtered_commits(
                    repo_name,
                    branch,
                    since,
                    until,
                    token,
                    page,
                    per_page,
                    author,
                )
            else:
                result = get_flat_commits(
                    repo_name, branch, since, until, token, page, per_page
                )
        except Exception as exc:  # noqa: BLE001 - surface API errors to UI
            return Response({"detail": str(exc)}, status=502)

        return Response(
            {
                "grouped": result.grouped,
                "count": result.count,
                "next": self._page_url(request, page + 1, per_page)
                if result.has_next
                else None,
                "previous": self._page_url(request, page - 1, per_page)
                if result.has_prev
                else None,
                "results": result.results,
                "page": result.page,
                "per_page": result.per_page,
            }
        )

    def _parse_pagination(self, request):
        try:
            page = int(request.query_params.get("page") or "1")
        except ValueError:
            page = 1
        try:
            per_page = int(
                request.query_params.get("per_page") or str(DEFAULT_COMMITS_PER_PAGE)
            )
        except ValueError:
            per_page = DEFAULT_COMMITS_PER_PAGE

        page = max(page, 1)
        per_page = min(max(per_page, 1), MAX_COMMITS_PER_PAGE)
        return page, per_page

    def _parse_dates(self, form):
        start_date = form.cleaned_data.get("start_date")
        end_date = form.cleaned_data.get("end_date")
        since = (
            datetime.combine(start_date, time.min, tzinfo=timezone.utc)
            if start_date
            else datetime.min.replace(tzinfo=timezone.utc)
        )
        until = (
            datetime.combine(end_date, time.max, tzinfo=timezone.utc)
            if end_date
            else datetime.max.replace(tzinfo=timezone.utc)
        )
        return since, until

    def _page_url(self, request, new_page: int, per_page: int) -> str:
        q = request.query_params.copy()
        q["page"] = str(new_page)
        q["per_page"] = str(per_page)
        base = request.build_absolute_uri(request.path)
        return f"{base}?{q.urlencode()}"


class IndexView(TemplateView):
    template_name = "index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        query = self.request.GET if self.request.method == "GET" else None
        form = CommitSearchForm(query or None)
        context["form"] = form

        context["commits"] = []
        context["branches"] = []
        context["authors"] = []
        context["grouped_commits"] = []
        context["error"] = None
        context["repo_loaded"] = False

        if not query:
            return context

        repo_name = (query.get("repo") or "").strip()
        if not repo_name:
            form.is_valid()  # populate field errors for template rendering
            return context

        token = _get_github_oauth_token(self.request.user)

        try:
            branches = github.get_repository_branches(repo_name, token=token)
        except Exception as exc:  # noqa: BLE001 - surface API errors to UI
            context["error"] = str(exc)
            context["branches"] = []
            return context

        branch_names = [b.name for b in branches]
        context["branches"] = branch_names
        context["repo_loaded"] = True

        branch_field = cast(forms.ChoiceField, form.fields["branch"])

        branch_field.choices = [
            ("", "All branches"),
            *[(b, b) for b in branch_names],
        ]

        if not form.is_valid():
            return context
        context["commits"] = []
        context["authors"] = []
        context["grouped_commits"] = []
        context["group_by_author"] = False

        return context


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = "account/profile.html"
