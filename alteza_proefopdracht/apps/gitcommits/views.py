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

        form = CommitSearchApiForm(request.query_params)
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

        branch = (form.cleaned_data.get("branch") or "").strip() or None
        author = (form.cleaned_data.get("author") or "").strip() or None
        group_by_author = bool(form.cleaned_data.get("group_by_author") or False)

        token = _get_github_oauth_token(request.user)
        def build_page_url(new_page: int) -> str:
            q = request.query_params.copy()
            q["page"] = str(new_page)
            q["per_page"] = str(per_page)
            base = request.build_absolute_uri(request.path)
            return f"{base}?{q.urlencode()}"

        try:
            if group_by_author:
                # Aggregate authors across the full filtered commit set.
                scan_page = 1
                scan_per_page = 100
                total_commits_unfiltered: int | None = None
                max_scan_pages = 200  # safety cap

                author_stats: dict[str, dict] = {}

                while scan_page <= max_scan_pages:
                    batch, batch_total = github.get_branch_commits(
                        repo_name=repo_name,
                        branch_name=branch,
                        since=since,
                        until=until,
                        token=token,
                        page=scan_page,
                        per_page=scan_per_page,
                    )
                    if total_commits_unfiltered is None:
                        total_commits_unfiltered = batch_total

                    if not batch:
                        break

                    for c in batch:
                        a = (c.author or "Unknown").strip() or "Unknown"
                        st = author_stats.get(a)
                        if st is None:
                            st = {
                                "author": a,
                                "count": 0,
                                "latest_date": None,
                                "latest_sha": None,
                                "latest_message": None,
                                "recent": [],
                            }
                            author_stats[a] = st
                        st["count"] += 1
                        if getattr(c, "date", None) and (st["latest_date"] is None or c.date > st["latest_date"]):
                            st["latest_date"] = c.date
                            st["latest_sha"] = c.commit_hash
                            st["latest_message"] = c.message
                        # GitHub returns commits newest→oldest; first 5 we see are the 5 most recent.
                        if len(st["recent"]) < 5:
                            st["recent"].append(
                                {
                                    "sha": c.commit_hash,
                                    "sha7": (c.commit_hash or "")[:7],
                                    "message": c.message,
                                    "date": c.date.isoformat() if getattr(c, "date", None) else None,
                                }
                            )

                    if (
                        total_commits_unfiltered is not None
                        and scan_page * scan_per_page >= total_commits_unfiltered
                    ):
                        break
                    scan_page += 1

                # Sort authors by commit count desc, then name.
                grouped = sorted(
                    author_stats.values(),
                    key=lambda d: (-int(d["count"]), str(d["author"]).lower()),
                )

                total_groups = len(grouped)
                start = (page - 1) * per_page
                end = start + per_page
                page_items = grouped[start:end]

                results = [
                    {
                        "author": it["author"],
                        "count": it["count"],
                        "latest": {
                            "sha": it["latest_sha"],
                            "sha7": (it["latest_sha"] or "")[:7],
                            "message": it["latest_message"],
                            "date": it["latest_date"].isoformat() if it["latest_date"] else None,
                        },
                        "recent": it.get("recent") or [],
                    }
                    for it in page_items
                ]

                next_url = build_page_url(page + 1) if end < total_groups else None
                prev_url = build_page_url(page - 1) if page > 1 else None
                return Response(
                    {
                        "grouped": True,
                        "count": total_groups,
                        "next": next_url,
                        "previous": prev_url,
                        "results": results,
                        "page": page,
                        "per_page": per_page,
                    }
                )

            if not author:
                commits, total = github.get_branch_commits(
                    repo_name=repo_name,
                    branch_name=branch,
                    since=since,
                    until=until,
                    token=token,
                    page=page,
                    per_page=per_page,
                )
                next_url = build_page_url(page + 1) if page * per_page < total else None
                prev_url = build_page_url(page - 1) if page > 1 else None
                count_value: int | None = total
            else:
                # Author filtering must search beyond the current page; we scan GitHub pages
                # until we have enough matches to serve the requested page.
                author_norm = author.strip().lower()
                want_start = (page - 1) * per_page
                want_end_exclusive = want_start + per_page

                scan_page = 1
                scan_per_page = 100
                matched: list = []
                total_unfiltered: int | None = None

                # Hard cap to prevent runaway scans on extremely sparse matches.
                max_scan_pages = 50

                while len(matched) <= want_end_exclusive and scan_page <= max_scan_pages:
                    batch, batch_total = github.get_branch_commits(
                        repo_name=repo_name,
                        branch_name=branch,
                        since=since,
                        until=until,
                        token=token,
                        page=scan_page,
                        per_page=scan_per_page,
                    )
                    if total_unfiltered is None:
                        total_unfiltered = batch_total

                    if not batch:
                        break

                    for c in batch:
                        # GitHub "author" can be a display name; match case-insensitively.
                        if (c.author or "").strip().lower() == author_norm:
                            matched.append(c)

                    # If we reached the end of the unfiltered set, stop scanning.
                    if total_unfiltered is not None and scan_page * scan_per_page >= total_unfiltered:
                        break

                    scan_page += 1

                commits = matched[want_start:want_end_exclusive]

                # We don't know the true match count without scanning everything; return null.
                count_value = None
                prev_url = build_page_url(page - 1) if page > 1 else None
                next_url = build_page_url(page + 1) if len(matched) > want_end_exclusive else None
        except Exception as exc:  # noqa: BLE001 - surface API errors to UI
            return Response({"detail": str(exc)}, status=502)

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

        return Response(
            {
                "grouped": False,
                "count": count_value,
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

        # Populate branch/author choices now that we know the repo.
        branch_field = cast(forms.ChoiceField, form.fields["branch"])

        branch_field.choices = [
            ("", "All branches"),
            *[(b, b) for b in branch_names],
        ]

        # Now that the branch choices are hydrated, validate the full form so any other
        # errors show up correctly.
        if not form.is_valid():
            return context
        # Commits are loaded client-side via the DRF paginated endpoint.
        context["commits"] = []
        context["authors"] = []
        context["grouped_commits"] = []
        context["group_by_author"] = False

        return context


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = "account/profile.html"
