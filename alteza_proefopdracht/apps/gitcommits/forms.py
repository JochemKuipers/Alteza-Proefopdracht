from __future__ import annotations

from datetime import date

from django import forms


class CommitSearchForm(forms.Form):
    repo = forms.CharField(
        label="Repository",
        required=True,
        help_text="Format: owner/repo (e.g. django/django)",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "owner/repo",
                "autocomplete": "off",
                "list": "repo-suggestions",
            }
        ),
    )
    start_date = forms.DateField(
        label="Start date",
        required=False,
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
    )
    end_date = forms.DateField(
        label="End date",
        required=False,
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
    )

    branch = forms.ChoiceField(
        label="Branch",
        required=False,
        choices=[],
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    author = forms.CharField(
        label="Author",
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Any author (optional)",
                "autocomplete": "off",
            }
        ),
    )
    group_by_author = forms.BooleanField(
        label="Group results by author",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "h-4 w-4 rounded border-slate-300"}),
    )

    def clean(self):
        cleaned = super().clean() or {}
        start: date | None = cleaned.get("start_date")
        end: date | None = cleaned.get("end_date")
        if start and end and start > end:
            self.add_error("end_date", "End date must be on or after the start date.")
        return cleaned


class CommitSearchApiForm(forms.Form):
    """
    API-facing validation.

    The HTML form hydrates `branch` as a ChoiceField only after loading repo branches.
    The API endpoint should still accept arbitrary branch strings (e.g. `stable/6.0.x`)
    and let GitHub decide whether the ref exists.
    """

    repo = forms.CharField(required=True)
    start_date = forms.DateField(required=False)
    end_date = forms.DateField(required=False)
    branch = forms.CharField(required=False)
    author = forms.CharField(required=False)
    group_by_author = forms.BooleanField(required=False)

    def clean(self):
        cleaned = super().clean() or {}
        start: date | None = cleaned.get("start_date")
        end: date | None = cleaned.get("end_date")
        if start and end and start > end:
            self.add_error("end_date", "End date must be on or after the start date.")
        return cleaned
