from __future__ import annotations

from django import forms

from .models import ConnectionBlock, StoreAccount


class StoreAccountForm(forms.ModelForm):
    class Meta:
        model = StoreAccount
        fields = ["name", "group", "marketplace", "cabinet_type", "status", "comments"]


class ConnectionBlockForm(forms.ModelForm):
    metadata = forms.JSONField(required=False)
    protected_secret_ref = forms.CharField(
        required=False,
        label="Protected secret reference",
        help_text=(
            "Write-only. Leave blank to keep the existing protected secret reference. "
            "Local TASK-011 resolver format: env://ENV_VAR_NAME."
        ),
        widget=forms.PasswordInput(render_value=False),
    )

    class Meta:
        model = ConnectionBlock
        fields = [
            "metadata",
            "protected_secret_ref",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["protected_secret_ref"].initial = ""
        if self.instance and self.instance.pk:
            self.initial["protected_secret_ref"] = ""

    def clean_metadata(self):
        return self.cleaned_data["metadata"] or {}

    def clean_protected_secret_ref(self):
        value = self.cleaned_data.get("protected_secret_ref", "")
        return value.strip()
