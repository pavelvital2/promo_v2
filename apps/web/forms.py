from __future__ import annotations

import json

from django import forms

from apps.product_core.models import (
    InternalProduct,
    Marketplace,
    MarketplaceListing,
    ListingSource,
    ProductCategory,
    ProductStatus,
    ProductVariant,
)
from apps.stores.models import StoreAccount


class JsonTextareaField(forms.CharField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("required", False)
        kwargs.setdefault("widget", forms.Textarea(attrs={"rows": 5}))
        super().__init__(*args, **kwargs)

    def prepare_value(self, value):
        if isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=False, indent=2)
        return value

    def clean(self, value):
        value = super().clean(value)
        if not value:
            return {}
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError as exc:
            raise forms.ValidationError("Введите корректный JSON.") from exc
        if not isinstance(parsed, dict):
            raise forms.ValidationError("JSON должен быть объектом.")
        return parsed


class InternalProductForm(forms.ModelForm):
    attributes_json = JsonTextareaField(label="Attributes JSON")

    class Meta:
        model = InternalProduct
        fields = ["internal_code", "name", "product_type", "category", "status", "comments"]
        labels = {
            "internal_code": "Внутренний код",
            "name": "Название",
            "product_type": "Тип товара",
            "category": "Категория",
            "status": "Статус",
            "comments": "Комментарии",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].queryset = ProductCategory.objects.exclude(
            status=ProductStatus.ARCHIVED,
        )
        self.fields["category"].required = False
        self.fields["attributes_json"].initial = self.instance.attributes if self.instance.pk else {}

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.attributes = self.cleaned_data["attributes_json"]
        if commit:
            instance.save()
            self.save_m2m()
        return instance


class ProductVariantForm(forms.ModelForm):
    variant_attributes_json = JsonTextareaField(label="Variant attributes JSON")

    class Meta:
        model = ProductVariant
        fields = ["internal_sku", "name", "barcode_internal", "status"]
        labels = {
            "internal_sku": "Внутренний SKU",
            "name": "Название варианта",
            "barcode_internal": "Внутренний barcode",
            "status": "Статус",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["variant_attributes_json"].initial = (
            self.instance.variant_attributes if self.instance.pk else {}
        )

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.variant_attributes = self.cleaned_data["variant_attributes_json"]
        if commit:
            instance.save()
            self.save_m2m()
        return instance


class MarketplaceListingFilterForm(forms.Form):
    q = forms.CharField(label="Поиск", required=False)
    marketplace = forms.ChoiceField(
        label="Маркетплейс",
        required=False,
        choices=[("", "Все"), *Marketplace.choices],
    )
    store = forms.ModelChoiceField(
        label="Магазин / кабинет",
        required=False,
        queryset=StoreAccount.objects.none(),
        empty_label="Все",
    )
    listing_status = forms.ChoiceField(
        label="Статус листинга",
        required=False,
        choices=[("", "Все"), *MarketplaceListing.ListingStatus.choices],
    )
    mapping_status = forms.ChoiceField(
        label="Статус сопоставления",
        required=False,
        choices=[("", "Все"), *MarketplaceListing.MappingStatus.choices],
    )
    source = forms.ChoiceField(
        label="Источник",
        required=False,
        choices=[("", "Все"), *ListingSource.choices],
    )
    category = forms.CharField(label="Категория", required=False)
    brand = forms.CharField(label="Бренд", required=False)
    stock = forms.ChoiceField(
        label="Остаток",
        required=False,
        choices=[
            ("", "Все"),
            ("present", "Есть остаток"),
            ("missing", "Нет остатка"),
        ],
    )
    updated_from = forms.DateField(label="Обновлено с", required=False)
    updated_to = forms.DateField(label="Обновлено по", required=False)

    def __init__(self, *args, stores=None, categories=None, brands=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["store"].queryset = stores or StoreAccount.objects.none()
        if categories is not None:
            self.fields["category"] = forms.ChoiceField(
                label="Категория",
                required=False,
                choices=[("", "Все"), *((value, value) for value in categories if value)],
            )
        if brands is not None:
            self.fields["brand"] = forms.ChoiceField(
                label="Бренд",
                required=False,
                choices=[("", "Все"), *((value, value) for value in brands if value)],
            )


class ExistingVariantMappingForm(forms.Form):
    variant = forms.ModelChoiceField(
        label="Вариант",
        queryset=ProductVariant.objects.none(),
        required=True,
        empty_label=None,
    )
    reason_comment = forms.CharField(
        label="Комментарий",
        required=False,
        widget=forms.Textarea(attrs={"rows": 2}),
    )

    def __init__(self, *args, variants=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["variant"].queryset = variants or ProductVariant.objects.none()


class NewVariantUnderProductMappingForm(ProductVariantForm):
    product = forms.ModelChoiceField(
        label="Внутренний товар",
        queryset=InternalProduct.objects.none(),
        required=True,
        empty_label=None,
    )
    reason_comment = forms.CharField(
        label="Комментарий",
        required=False,
        widget=forms.Textarea(attrs={"rows": 2}),
    )

    def __init__(self, *args, products=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["product"].queryset = products or InternalProduct.objects.none()


class MappingMarkerForm(forms.Form):
    reason_comment = forms.CharField(
        label="Комментарий",
        required=False,
        widget=forms.Textarea(attrs={"rows": 2}),
    )


class UnmapListingForm(forms.Form):
    mapping_status_after = forms.ChoiceField(
        label="Статус после снятия связи",
        choices=[
            (MarketplaceListing.MappingStatus.UNMATCHED, "Unmatched"),
            (MarketplaceListing.MappingStatus.NEEDS_REVIEW, "Needs review"),
            (MarketplaceListing.MappingStatus.CONFLICT, "Conflict"),
        ],
    )
    reason_comment = forms.CharField(
        label="Комментарий",
        required=False,
        widget=forms.Textarea(attrs={"rows": 2}),
    )
