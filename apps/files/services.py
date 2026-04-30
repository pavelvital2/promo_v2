"""Service helpers for TASK-004 file storage, downloads and retention."""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass
from datetime import timedelta
from pathlib import PurePosixPath

from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.base import File
from django.core.files.storage import default_storage
from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from apps.identity_access.services import has_permission

from .models import FileObject, FileVersion, allow_file_pre_operation_metadata_delete


FILE_PHYSICAL_RETENTION_DAYS = 3
DOWNLOAD_PERMISSION_BY_KIND = {
    FileObject.Kind.OUTPUT: "download_output",
    FileObject.Kind.DETAIL_REPORT: "download_detail_report",
    FileObject.Kind.INPUT: "view",
}


class FileUnavailable(Exception):
    """Raised when metadata exists but the physical file cannot be served."""


class FileRetentionExpired(FileUnavailable):
    """Raised when the physical file retention window has elapsed."""


@dataclass(frozen=True)
class RetentionCleanupResult:
    scanned: int
    deleted: int
    missing: int
    dry_run: bool


@dataclass(frozen=True)
class PreOperationDeleteResult:
    file_object_id: int
    version_ids: tuple[int, ...]
    physical_deleted: int
    physical_missing: int
    metadata_deleted: bool


def scenario_marketplace(scenario: str) -> str:
    mapping = {
        FileObject.Scenario.WB_DISCOUNTS_EXCEL: FileObject.Marketplace.WB,
        FileObject.Scenario.WB_DISCOUNTS_API_PRICE_EXPORT: FileObject.Marketplace.WB,
        FileObject.Scenario.WB_DISCOUNTS_API_PROMOTION_EXPORT: FileObject.Marketplace.WB,
        FileObject.Scenario.WB_DISCOUNTS_API_RESULT_EXCEL: FileObject.Marketplace.WB,
        FileObject.Scenario.WB_DISCOUNTS_API_DETAIL_REPORT: FileObject.Marketplace.WB,
        FileObject.Scenario.WB_DISCOUNTS_API_UPLOAD_REPORT: FileObject.Marketplace.WB,
        FileObject.Scenario.OZON_DISCOUNTS_EXCEL: FileObject.Marketplace.OZON,
        FileObject.Scenario.OZON_API_ELASTIC_RESULT_REPORT: FileObject.Marketplace.OZON,
        FileObject.Scenario.OZON_API_ELASTIC_MANUAL_UPLOAD_EXCEL: FileObject.Marketplace.OZON,
        FileObject.Scenario.OZON_API_ELASTIC_UPLOAD_REPORT: FileObject.Marketplace.OZON,
    }
    try:
        return mapping[scenario]
    except KeyError as exc:
        raise ValidationError("Unsupported file scenario.") from exc


def _basename(name: str) -> str:
    cleaned = str(name or "uploaded_file").replace("\\", "/")
    basename = PurePosixPath(cleaned).name.strip()
    return basename or "uploaded_file"


def _safe_extension(original_name: str) -> str:
    suffix = PurePosixPath(_basename(original_name)).suffix.lower()
    if not suffix:
        return ".bin"
    safe = "".join(character for character in suffix if character.isalnum() or character == ".")
    if len(safe) > 16:
        return ".bin"
    return safe or ".bin"


def _storage_path(file_object: FileObject, version_no: int, original_name: str) -> str:
    store_id = file_object.store.visible_id or f"store-{file_object.store_id}"
    suffix = _safe_extension(original_name)
    return (
        f"files/{file_object.scenario}/{store_id}/{file_object.visible_id}/"
        f"v{version_no:06d}/{uuid.uuid4().hex}{suffix}"
    )


def _iter_chunks(uploaded_file):
    if hasattr(uploaded_file, "chunks"):
        yield from uploaded_file.chunks()
        return
    while True:
        chunk = uploaded_file.read(1024 * 1024)
        if not chunk:
            break
        yield chunk


def _store_physical_file(uploaded_file, storage_path: str) -> tuple[int, str]:
    digest = hashlib.sha256()
    size = 0

    class HashingFile(File):
        def chunks(self, chunk_size=None):
            nonlocal size
            for chunk in _iter_chunks(uploaded_file):
                if isinstance(chunk, str):
                    chunk = chunk.encode()
                digest.update(chunk)
                size += len(chunk)
                yield chunk

    if hasattr(uploaded_file, "seek"):
        uploaded_file.seek(0)
    saved_path = default_storage.save(storage_path, HashingFile(uploaded_file))
    if saved_path != storage_path:
        storage_path = saved_path
    if hasattr(uploaded_file, "seek"):
        uploaded_file.seek(0)
    return size, digest.hexdigest()


def _validate_file_object(
    file_object: FileObject,
    *,
    store,
    scenario: str,
    kind: str,
):
    if file_object.store_id != store.pk:
        raise ValidationError("File object belongs to another store/cabinet.")
    if file_object.scenario != scenario:
        raise ValidationError("File object belongs to another scenario.")
    if file_object.kind != kind:
        raise ValidationError("File object belongs to another file kind.")
    if file_object.status != FileObject.Status.ACTIVE:
        raise ValidationError("Archived file object cannot receive new versions.")


@transaction.atomic
def create_file_version(
    *,
    store,
    uploaded_by,
    uploaded_file,
    scenario: str,
    kind: str,
    logical_name: str = "",
    module: str = "discounts_excel",
    file_object: FileObject | None = None,
    content_type: str = "",
    operation_ref: str = "",
    run_ref: str = "",
) -> FileVersion:
    """Store a physical file and create historical metadata for one version."""

    original_name = _basename(getattr(uploaded_file, "name", "") or logical_name)
    marketplace = scenario_marketplace(scenario)
    if file_object is None:
        file_object = FileObject.objects.create(
            store=store,
            kind=kind,
            scenario=scenario,
            marketplace=marketplace,
            module=module,
            logical_name=logical_name or original_name,
            original_name=original_name,
            created_by=uploaded_by,
        )
    else:
        file_object = FileObject.objects.select_for_update().get(pk=file_object.pk)
        _validate_file_object(file_object, store=store, scenario=scenario, kind=kind)

    current_max = (
        FileVersion.objects.filter(file=file_object).aggregate(max_version=Max("version_no"))[
            "max_version"
        ]
        or 0
    )
    version_no = current_max + 1
    storage_path = _storage_path(file_object, version_no, original_name)
    size, checksum = _store_physical_file(uploaded_file, storage_path)
    retention_until = timezone.now() + timedelta(days=FILE_PHYSICAL_RETENTION_DAYS)

    version = FileVersion.objects.create(
        file=file_object,
        version_no=version_no,
        original_name=original_name,
        content_type=content_type or getattr(uploaded_file, "content_type", "") or "",
        storage_path=storage_path,
        size=size,
        checksum_sha256=checksum,
        uploaded_by=uploaded_by,
        retention_until=retention_until,
        operation_ref=operation_ref,
        run_ref=run_ref,
    )
    FileObject.objects.filter(pk=file_object.pk).update(updated_at=timezone.now())
    return version


def download_permission_code(file_object: FileObject) -> str:
    scenario_permissions = {
        FileObject.Scenario.WB_DISCOUNTS_API_PRICE_EXPORT: "wb.api.prices.file.download",
        FileObject.Scenario.WB_DISCOUNTS_API_PROMOTION_EXPORT: "wb.api.promotions.file.download",
        FileObject.Scenario.WB_DISCOUNTS_API_RESULT_EXCEL: "wb.api.discounts.result.download",
        FileObject.Scenario.WB_DISCOUNTS_API_DETAIL_REPORT: "wb.api.discounts.result.download",
        FileObject.Scenario.WB_DISCOUNTS_API_UPLOAD_REPORT: "wb.api.discounts.result.download",
        FileObject.Scenario.OZON_API_ELASTIC_RESULT_REPORT: "ozon.api.elastic.files.download",
        FileObject.Scenario.OZON_API_ELASTIC_MANUAL_UPLOAD_EXCEL: "ozon.api.elastic.files.download",
        FileObject.Scenario.OZON_API_ELASTIC_UPLOAD_REPORT: "ozon.api.elastic.files.download",
    }
    if file_object.scenario in scenario_permissions:
        return scenario_permissions[file_object.scenario]
    action = DOWNLOAD_PERMISSION_BY_KIND.get(file_object.kind)
    if action is None:
        raise ValidationError("Unsupported file kind for download.")
    return f"{file_object.scenario}.{action}"


def assert_can_download_file_version(user, version: FileVersion, *, now=None) -> None:
    now = now or timezone.now()
    file_object = version.file
    if file_object.status != FileObject.Status.ACTIVE:
        raise FileUnavailable("File metadata is archived.")
    if version.physical_status != FileVersion.PhysicalStatus.AVAILABLE:
        raise FileUnavailable("Physical file is no longer available.")
    if version.retention_until <= now:
        raise FileRetentionExpired("Physical file retention has expired.")

    permission_code = download_permission_code(file_object)
    if not has_permission(user, permission_code, file_object.store):
        raise PermissionDenied("No permission or object access for this file download.")


def open_file_version_for_download(user, version: FileVersion):
    assert_can_download_file_version(user, version)
    if not default_storage.exists(version.storage_path):
        FileVersion.objects.filter(pk=version.pk).update(
            physical_status=FileVersion.PhysicalStatus.MISSING,
            physical_deleted_at=timezone.now(),
        )
        raise FileUnavailable("Physical file is missing from storage.")
    return default_storage.open(version.storage_path, "rb")


def _assert_pre_operation_delete_allowed(file_object: FileObject, versions: list[FileVersion]):
    if file_object.kind != FileObject.Kind.INPUT:
        raise ValidationError("Only pre-operation input uploads can be deleted.")
    if file_object.status != FileObject.Status.ACTIVE:
        raise ValidationError("Archived file metadata cannot be deleted.")
    if file_object.has_operation_links():
        raise ValidationError("Operation-linked file metadata cannot be deleted.")
    if not versions:
        raise ValidationError("File object has no uploaded versions to delete.")
    for version in versions:
        if version.operation_ref or version.run_ref:
            raise ValidationError("Operation-linked file version cannot be deleted.")
        if version.physical_status != FileVersion.PhysicalStatus.AVAILABLE:
            raise ValidationError("Historical or unavailable file version cannot be deleted.")
        if version.is_retention_expired:
            raise ValidationError(
                "Expired file version cannot be deleted through pre-operation flow."
            )


def _delete_pre_operation_versions(
    *,
    file_object: FileObject,
    versions: list[FileVersion],
    delete_file_object_when_empty: bool,
) -> PreOperationDeleteResult:
    _assert_pre_operation_delete_allowed(file_object, versions)
    physical_deleted = physical_missing = 0
    for version in versions:
        if default_storage.exists(version.storage_path):
            default_storage.delete(version.storage_path)
            physical_deleted += 1
        else:
            physical_missing += 1

    file_object_id = file_object.pk
    version_ids = tuple(version.pk for version in versions)
    with allow_file_pre_operation_metadata_delete():
        for version in versions:
            version.delete()
        if delete_file_object_when_empty and not file_object.versions.exists():
            file_object.delete()

    return PreOperationDeleteResult(
        file_object_id=file_object_id,
        version_ids=version_ids,
        physical_deleted=physical_deleted,
        physical_missing=physical_missing,
        metadata_deleted=True,
    )


@transaction.atomic
def delete_pre_operation_file_upload(file_object: FileObject) -> PreOperationDeleteResult:
    """Delete an erroneous input upload before it is attached to an operation/run."""

    locked_file = FileObject.objects.select_for_update().get(pk=file_object.pk)
    versions = list(locked_file.versions.select_for_update().order_by("version_no", "id"))
    return _delete_pre_operation_versions(
        file_object=locked_file,
        versions=versions,
        delete_file_object_when_empty=True,
    )


@transaction.atomic
def delete_pre_operation_file_version(version: FileVersion) -> PreOperationDeleteResult:
    """Delete one erroneous input version before any version of its file is used."""

    locked_version = FileVersion.objects.select_for_update().select_related("file").get(
        pk=version.pk
    )
    locked_file = FileObject.objects.select_for_update().get(pk=locked_version.file_id)
    return _delete_pre_operation_versions(
        file_object=locked_file,
        versions=[locked_version],
        delete_file_object_when_empty=True,
    )


def cleanup_expired_physical_files(*, now=None, dry_run: bool = False, limit: int | None = None):
    now = now or timezone.now()
    queryset = FileVersion.objects.filter(
        physical_status=FileVersion.PhysicalStatus.AVAILABLE,
        retention_until__lte=now,
    ).order_by("retention_until", "id")
    if limit is not None:
        queryset = queryset[:limit]

    scanned = deleted = missing = 0
    for version in queryset:
        scanned += 1
        exists = default_storage.exists(version.storage_path)
        if dry_run:
            if exists:
                deleted += 1
            else:
                missing += 1
            continue

        if exists:
            default_storage.delete(version.storage_path)
            deleted += 1
            new_status = FileVersion.PhysicalStatus.RETENTION_DELETED
        else:
            missing += 1
            new_status = FileVersion.PhysicalStatus.MISSING

        FileVersion.objects.filter(pk=version.pk).update(
            physical_status=new_status,
            physical_deleted_at=now,
        )

    return RetentionCleanupResult(
        scanned=scanned,
        deleted=deleted,
        missing=missing,
        dry_run=dry_run,
    )
