from __future__ import annotations

from django import forms

from .models import ConnectionBlock, StoreAccount


class StoreAccountForm(forms.ModelForm):
    class Meta:
        model = StoreAccount
        fields = ["name", "group", "marketplace", "cabinet_type", "status", "comments"]


class ConnectionBlockForm(forms.ModelForm):
    metadata = forms.JSONField(required=False)

    class Meta:
        model = ConnectionBlock
        fields = [
            "module",
            "connection_type",
            "status",
            "metadata",
            "protected_secret_ref",
        ]

    def clean_metadata(self):
        return self.cleaned_data["metadata"] or {}
