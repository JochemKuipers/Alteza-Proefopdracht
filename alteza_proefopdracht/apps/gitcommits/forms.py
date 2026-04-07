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
    author = forms.ChoiceField(
        label="Author",
        required=False,
        choices=[],
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    group_by_author = forms.BooleanField(
        label="Group results by author",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "h-4 w-4 rounded border-slate-300"}),
    )

    def clean(self):
        cleaned = super().clean()
        start: date | None = cleaned.get("start_date")
        end: date | None = cleaned.get("end_date")
        if start and end and start > end:
            self.add_error("end_date", "End date must be on or after the start date.")
        return cleaned
