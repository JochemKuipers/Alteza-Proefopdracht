from __future__ import annotations

from collections import defaultdict
from datetime import datetime, time, timezone
from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.views import View
from django.views.generic import TemplateView

from allauth.socialaccount.models import SocialToken

from . import github
from .forms import CommitSearchForm
from .models import GitUser


def _get_github_oauth_token(user: GitUser) -> str | None:
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
        form.fields["branch"].choices = [
            ("", "All branches"),
            *[(b, b) for b in branch_names],
        ]
        form.fields["author"].choices = [("", "All authors")]

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
        author = form.cleaned_data.get("author") or None

        try:
            commits = github.get_branch_commits(
                repo_name=repo_name,
                branch_name=branch,
                since=since,
                until=until,
                token=token,
                page=1,
                per_page=100,
            )
        except Exception as exc:
            context["error"] = str(exc)
            return context

        # Build authors list for filtering.
        authors = sorted({c.author for c in commits if c.author})
        context["authors"] = authors
        form.fields["author"].choices = [
            ("", "All authors"),
            *[(a, a) for a in authors],
        ]

        if author:
            commits = [c for c in commits if c.author == author]

        # Sort newest first.
        commits.sort(
            key=lambda c: c.date or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        )
        context["commits"] = commits

        group_by_author = bool(form.cleaned_data.get("group_by_author")) or bool(author)
        context["group_by_author"] = group_by_author

        if group_by_author:
            grouped: dict[str, list[Any]] = defaultdict(list)
            for c in commits:
                author_name = getattr(c, "author", None) or "Unknown"
                grouped[str(author_name)].append(c)
            context["grouped_commits"] = [
                {"author": a, "count": len(items), "commits": items}
                for a, items in sorted(
                    grouped.items(), key=lambda kv: (-len(kv[1]), str(kv[0]).lower())
                )
            ]

        return context


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = "account/profile.html"
