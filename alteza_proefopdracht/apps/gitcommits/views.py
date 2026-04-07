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
from .forms import CommitSearchForm
from .models import GitUser

DEFAULT_COMMITS_PER_PAGE = 6
MAX_COMMITS_PER_PAGE = 6


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
    - per_page is fixed at 5
    """

    # Use session auth so `request.user` is populated for logged-in users.
    # Without this, we always fall back to unauthenticated GitHub requests (low rate limits).
    authentication_classes = [SessionAuthentication]
    permission_classes: list = []

    def get(self, request, *args, **kwargs):
        repo_name = (request.query_params.get("repo") or "").strip()
        if not repo_name:
            return Response({"detail": "Missing repo"}, status=400)

        form = CommitSearchForm(request.query_params)
        if not form.is_valid():
            return Response({"detail": "Invalid parameters", "errors": form.errors}, status=400)

        try:
            page = int(request.query_params.get("page") or "1")
        except ValueError:
            page = 1
        per_page = DEFAULT_COMMITS_PER_PAGE

        page = max(page, 1)
        per_page = min(max(per_page, 1), MAX_COMMITS_PER_PAGE)

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

        branch = form.cleaned_data.get("branch") or None
        author = (form.cleaned_data.get("author") or "").strip() or None

        token = _get_github_oauth_token(request.user)
        try:
            commits, total = github.get_branch_commits_with_total(
                repo_name=repo_name,
                branch_name=branch,
                since=since,
                until=until,
                token=token,
                page=page,
                per_page=per_page,
            )
        except Exception as exc:  # noqa: BLE001 - surface API errors to UI
            return Response({"detail": str(exc)}, status=502)

        if author:
            commits = [c for c in commits if (c.author or "").strip() == author]
            # total becomes "unknown" after filtering client-side; keep it conservative.
            total = len(commits) if page == 1 else total

        commits.sort(
            key=lambda c: c.date or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        )

        results = [
            {
                "sha": c.commit_hash,
                "sha7": (c.commit_hash or "")[:7],
                "message": c.message,
                "author": c.author or "Unknown",
                "date": c.date.isoformat() if getattr(c, "date", None) else None,
            }
            for c in commits
        ]

        def build_page_url(new_page: int) -> str:
            q = request.query_params.copy()
            q["page"] = str(new_page)
            q["per_page"] = str(per_page)
            base = request.build_absolute_uri(request.path)
            return f"{base}?{q.urlencode()}"

        next_url = build_page_url(page + 1) if page * per_page < total else None
        prev_url = build_page_url(page - 1) if page > 1 else None

        return Response(
            {
                "count": total,
                "next": next_url,
                "previous": prev_url,
                "results": results,
                "page": page,
                "per_page": per_page,
            }
        )


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

        if not form.is_valid():
            return context

        repo_name = form.cleaned_data["repo"].strip()
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

        # Populate branch/author choices now that we know the repo.
        branch_field = cast(forms.ChoiceField, form.fields["branch"])

        branch_field.choices = [
            ("", "All branches"),
            *[(b, b) for b in branch_names],
        ]
        # Commits are loaded client-side via the DRF paginated endpoint.
        context["commits"] = []
        context["authors"] = []
        context["grouped_commits"] = []
        context["group_by_author"] = False

        return context


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = "account/profile.html"
