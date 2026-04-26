"""Identity/access models for TASK-002."""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar

from django.conf import settings
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models.deletion import ProtectedError


OWNER_ROLE_CODE = "owner"
_allow_system_dictionary_mutation = ContextVar(
    "allow_system_dictionary_mutation",
    default=False,
)


@contextmanager
def system_dictionary_mutation():
    token = _allow_system_dictionary_mutation.set(True)
    try:
        yield
    finally:
        _allow_system_dictionary_mutation.reset(token)


def _system_dictionary_mutation_allowed() -> bool:
    return _allow_system_dictionary_mutation.get()


def user_role_codes(user) -> set[str]:
    if not user:
        return set()

    codes = set()
    primary_role = getattr(user, "primary_role", None)
    if getattr(user, "primary_role_id", None) and primary_role:
        codes.add(primary_role.code)

    if getattr(user, "pk", None):
        codes.update(user.roles.values_list("code", flat=True))
    return codes


def is_owner_user(user) -> bool:
    return OWNER_ROLE_CODE in user_role_codes(user)


class GuardedDeleteQuerySet(models.QuerySet):
    def _raise_if_system_update_is_forbidden(self, kwargs):
        if _system_dictionary_mutation_allowed():
            return

        model_name = self.model.__name__
        if model_name in {"Role", "Permission", "SectionAccess"}:
            if self.filter(is_system=True).exists() or kwargs.get("is_system") is True:
                raise ValidationError("System dictionaries are changed only by seed/migration.")
            return

        if model_name in {"RolePermission", "RoleSectionAccess"}:
            targets_system_role = self.filter(role__is_system=True).exists()
            role_value = kwargs.get("role", kwargs.get("role_id"))
            if role_value is not None:
                role_id = getattr(role_value, "pk", role_value)
                if not isinstance(role_id, (int, str)):
                    targets_system_role = True
                elif Role.objects.filter(pk=role_id, is_system=True).exists():
                    targets_system_role = True
            if targets_system_role:
                raise ValidationError("System role composition is changed only by seed/migration.")

    def update(self, **kwargs):
        self._raise_if_system_update_is_forbidden(kwargs)
        return super().update(**kwargs)

    def delete(self):
        count = 0
        with transaction.atomic():
            for obj in self:
                obj.delete()
                count += 1
        return count, {self.model._meta.label: count}


GuardedDeleteManager = models.Manager.from_queryset(GuardedDeleteQuerySet)


class Role(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        INACTIVE = "inactive", "Inactive"
        ARCHIVED = "archived", "Archived"

    code = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=255)
    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    is_system = models.BooleanField(default=False)

    objects = GuardedDeleteManager()

    class Meta:
        ordering = ["code"]

    def __str__(self) -> str:
        return self.name

    @property
    def is_owner_role(self) -> bool:
        return self.code == OWNER_ROLE_CODE

    def _raise_if_system_mutation_is_forbidden(self):
        if _system_dictionary_mutation_allowed():
            return
        if not self.pk:
            if self.is_system:
                raise ValidationError("System roles are changed only by seed/migration.")
            return

        previous = type(self).objects.get(pk=self.pk)
        if previous.is_system and (
            self.code != previous.code
            or self.name != previous.name
            or self.status != previous.status
            or self.is_system != previous.is_system
        ):
            raise ValidationError("System roles are immutable.")

    def save(self, *args, **kwargs):
        self._raise_if_system_mutation_is_forbidden()
        return super().save(*args, **kwargs)

    def delete(self, using=None, keep_parents=False):
        if self.is_system:
            raise ProtectedError("System roles are not deleted.", [self])
        return super().delete(using=using, keep_parents=keep_parents)


class Permission(models.Model):
    class ScopeType(models.TextChoices):
        GLOBAL = "global", "Global"
        STORE = "store", "Store"
        GLOBAL_STORE = "global_store", "Global or store"
        OWNER_ONLY = "owner_only", "Owner only"

    code = models.CharField(max_length=150, primary_key=True)
    name = models.CharField(max_length=255)
    scope_type = models.CharField(max_length=32, choices=ScopeType.choices)
    is_system = models.BooleanField(default=True)

    objects = GuardedDeleteManager()

    class Meta:
        ordering = ["code"]

    def __str__(self) -> str:
        return self.code

    def _raise_if_system_mutation_is_forbidden(self):
        if _system_dictionary_mutation_allowed():
            return
        if self._state.adding:
            if self.is_system:
                raise ValidationError("System permissions are changed only by seed/migration.")
            return

        previous = type(self).objects.get(pk=self.pk)
        if previous.is_system and (
            self.name != previous.name
            or self.scope_type != previous.scope_type
            or self.is_system != previous.is_system
        ):
            raise ValidationError("System permissions are immutable.")

    def save(self, *args, **kwargs):
        self._raise_if_system_mutation_is_forbidden()
        return super().save(*args, **kwargs)

    def delete(self, using=None, keep_parents=False):
        if self.is_system:
            raise ProtectedError("System permissions are immutable.", [self])
        return super().delete(using=using, keep_parents=keep_parents)


class SectionAccess(models.Model):
    class Mode(models.TextChoices):
        VIEW = "view", "View"
        EDIT = "edit", "Edit"

    code = models.CharField(max_length=100, primary_key=True)
    section = models.CharField(max_length=100)
    mode = models.CharField(max_length=16, choices=Mode.choices, default=Mode.VIEW)
    name = models.CharField(max_length=255)
    is_system = models.BooleanField(default=True)

    objects = GuardedDeleteManager()

    class Meta:
        ordering = ["section", "mode", "code"]

    def __str__(self) -> str:
        return self.code

    def _raise_if_system_mutation_is_forbidden(self):
        if _system_dictionary_mutation_allowed():
            return
        if self._state.adding:
            if self.is_system:
                raise ValidationError("System section access is changed only by seed/migration.")
            return

        previous = type(self).objects.get(pk=self.pk)
        if previous.is_system and (
            self.section != previous.section
            or self.mode != previous.mode
            or self.name != previous.name
            or self.is_system != previous.is_system
        ):
            raise ValidationError("System section access is immutable.")

    def save(self, *args, **kwargs):
        self._raise_if_system_mutation_is_forbidden()
        return super().save(*args, **kwargs)

    def delete(self, using=None, keep_parents=False):
        if self.is_system:
            raise ProtectedError("System section access codes are immutable.", [self])
        return super().delete(using=using, keep_parents=keep_parents)


class UserManager(BaseUserManager.from_queryset(GuardedDeleteQuerySet)):
    use_in_migrations = True

    def create_user(self, login: str, password: str | None = None, **extra_fields):
        if not login:
            raise ValueError("The login field is required.")
        login = self.normalize_email(login) if "@" in login else login.strip()
        user = self.model(login=login, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, login: str, password: str | None = None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self.create_user(login, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        BLOCKED = "blocked", "Blocked"
        ARCHIVED = "archived", "Archived"

    visible_id = models.CharField(max_length=32, unique=True, null=True, blank=True)
    login = models.CharField(max_length=150, unique=True)
    display_name = models.CharField(max_length=255)
    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    primary_role = models.ForeignKey(
        Role,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="primary_users",
    )
    roles = models.ManyToManyField(Role, through="UserRole", related_name="users", blank=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "login"
    REQUIRED_FIELDS = ["display_name"]

    class Meta:
        ordering = ["visible_id", "id"]

    def __str__(self) -> str:
        return f"{self.visible_id or 'USR-new'} {self.login}"

    @property
    def is_active(self) -> bool:
        return self.status == self.Status.ACTIVE

    @property
    def is_owner(self) -> bool:
        return is_owner_user(self)

    def has_physical_delete_usage(self) -> bool:
        if not self.pk:
            return False
        if self.last_login is not None or self.primary_role_id:
            return True
        return any(
            (
                self.roles.exists(),
                self.permission_overrides.exists(),
                self.section_overrides.exists(),
                self.store_access.exists(),
                self.change_history.exists(),
                self.block_history.exists(),
                self.user_changes_made.exists(),
                self.user_blocks_made.exists(),
            ),
        )

    def can_be_physically_deleted(self) -> bool:
        return not self.is_owner and not self.has_physical_delete_usage()

    def clean(self):
        super().clean()
        if self.pk:
            previous = type(self).objects.select_related("primary_role").get(pk=self.pk)
            if previous.is_owner:
                if self.status != self.Status.ACTIVE:
                    raise ValidationError("Owner cannot be blocked or archived.")
                if not (self.primary_role and self.primary_role.is_owner_role):
                    raise ValidationError("Owner primary role cannot be changed.")

    def save(self, *args, **kwargs):
        if self.pk:
            self.full_clean()
        super().save(*args, **kwargs)
        if not self.visible_id:
            self.visible_id = f"USR-{self.pk:06d}"
            super().save(update_fields=["visible_id"])

    def delete(self, using=None, keep_parents=False):
        if self.is_owner:
            raise ProtectedError("Owner user is protected from deletion.", [self])
        if self.has_physical_delete_usage():
            raise ProtectedError(
                "Used users are blocked or archived instead of physically deleted.",
                [self],
            )
        return super().delete(using=using, keep_parents=keep_parents)


class UserRole(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    role = models.ForeignKey(Role, on_delete=models.PROTECT)
    assigned_at = models.DateTimeField(auto_now_add=True)

    objects = GuardedDeleteManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "role"], name="uniq_identity_user_role"),
        ]

    def delete(self, using=None, keep_parents=False):
        raise ProtectedError(
            "User role assignments are deactivated or superseded, not deleted.",
            [self],
        )


class RolePermission(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="role_permissions")
    permission = models.ForeignKey(
        Permission,
        on_delete=models.PROTECT,
        related_name="role_permissions",
    )

    objects = GuardedDeleteManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["role", "permission"],
                name="uniq_identity_role_permission",
            ),
        ]

    def _raise_if_system_role_composition_is_forbidden(self):
        if _system_dictionary_mutation_allowed():
            return
        role_id = self.role_id
        if self.pk:
            previous = type(self).objects.select_related("role").get(pk=self.pk)
            if previous.role.is_system:
                raise ValidationError("System role permissions are immutable.")
            role_id = self.role_id or previous.role_id
        if role_id and Role.objects.filter(pk=role_id, is_system=True).exists():
            raise ValidationError("System role permissions are immutable.")

    def save(self, *args, **kwargs):
        self._raise_if_system_role_composition_is_forbidden()
        return super().save(*args, **kwargs)

    def delete(self, using=None, keep_parents=False):
        if self.role.is_system:
            raise ProtectedError("System role permissions are immutable.", [self])
        return super().delete(using=using, keep_parents=keep_parents)


class RoleSectionAccess(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="role_sections")
    section_access = models.ForeignKey(
        SectionAccess,
        on_delete=models.PROTECT,
        related_name="role_sections",
    )

    objects = GuardedDeleteManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["role", "section_access"],
                name="uniq_identity_role_section",
            ),
        ]

    def _raise_if_system_role_composition_is_forbidden(self):
        if _system_dictionary_mutation_allowed():
            return
        role_id = self.role_id
        if self.pk:
            previous = type(self).objects.select_related("role").get(pk=self.pk)
            if previous.role.is_system:
                raise ValidationError("System role section access is immutable.")
            role_id = self.role_id or previous.role_id
        if role_id and Role.objects.filter(pk=role_id, is_system=True).exists():
            raise ValidationError("System role section access is immutable.")

    def save(self, *args, **kwargs):
        self._raise_if_system_role_composition_is_forbidden()
        return super().save(*args, **kwargs)

    def delete(self, using=None, keep_parents=False):
        if self.role.is_system:
            raise ProtectedError("System role section access is immutable.", [self])
        return super().delete(using=using, keep_parents=keep_parents)


class AccessEffect(models.TextChoices):
    ALLOW = "allow", "Allow"
    DENY = "deny", "Deny"


class UserPermissionOverride(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="permission_overrides",
    )
    permission = models.ForeignKey(
        Permission,
        on_delete=models.PROTECT,
        related_name="user_overrides",
    )
    effect = models.CharField(max_length=16, choices=AccessEffect.choices)
    store = models.ForeignKey(
        "stores.StoreAccount",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="permission_overrides",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = GuardedDeleteManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "permission", "store", "effect"],
                name="uniq_identity_user_permission_override",
            ),
        ]

    def clean(self):
        super().clean()
        if self.effect == AccessEffect.DENY and self.user_id and self.user.is_owner:
            raise ValidationError("Owner cannot receive direct permission denies.")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def delete(self, using=None, keep_parents=False):
        if self.is_active:
            raise ProtectedError("Active permission overrides are deactivated, not deleted.", [self])
        return super().delete(using=using, keep_parents=keep_parents)


class UserSectionAccessOverride(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="section_overrides",
    )
    section_access = models.ForeignKey(
        SectionAccess,
        on_delete=models.PROTECT,
        related_name="user_overrides",
    )
    effect = models.CharField(max_length=16, choices=AccessEffect.choices)
    store = models.ForeignKey(
        "stores.StoreAccount",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="section_overrides",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = GuardedDeleteManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "section_access", "store", "effect"],
                name="uniq_identity_user_section_override",
            ),
        ]

    def clean(self):
        super().clean()
        if self.effect == AccessEffect.DENY and self.user_id and self.user.is_owner:
            raise ValidationError("Owner cannot receive direct section denies.")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def delete(self, using=None, keep_parents=False):
        if self.is_active:
            raise ProtectedError("Active section overrides are deactivated, not deleted.", [self])
        return super().delete(using=using, keep_parents=keep_parents)


class StoreAccess(models.Model):
    class AccessLevel(models.TextChoices):
        FULL = "full", "Full"
        ADMIN = "admin", "Admin"
        WORK = "work", "Work"
        VIEW = "view", "View"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="store_access",
    )
    store = models.ForeignKey(
        "stores.StoreAccount",
        on_delete=models.PROTECT,
        related_name="user_access",
    )
    access_level = models.CharField(max_length=16, choices=AccessLevel.choices)
    effect = models.CharField(
        max_length=16,
        choices=AccessEffect.choices,
        default=AccessEffect.ALLOW,
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = GuardedDeleteManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "store", "effect"],
                name="uniq_identity_store_access",
            ),
        ]

    def clean(self):
        super().clean()
        if self.effect == AccessEffect.DENY and self.user_id and self.user.is_owner:
            raise ValidationError("Owner cannot receive direct store denies.")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def delete(self, using=None, keep_parents=False):
        if self.is_active:
            raise ProtectedError("Active store access rows are deactivated, not deleted.", [self])
        return super().delete(using=using, keep_parents=keep_parents)


class UserChangeHistory(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="change_history",
    )
    changed_at = models.DateTimeField(auto_now_add=True)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="user_changes_made",
    )
    field_code = models.CharField(max_length=128)
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)
    source = models.CharField(max_length=64, default="system")

    objects = GuardedDeleteManager()

    class Meta:
        ordering = ["-changed_at", "-id"]

    def delete(self, using=None, keep_parents=False):
        raise ProtectedError("User change history is immutable.", [self])


class UserBlockHistory(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="block_history",
    )
    changed_at = models.DateTimeField(auto_now_add=True)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="user_blocks_made",
    )
    old_status = models.CharField(max_length=32)
    new_status = models.CharField(max_length=32)
    reason = models.TextField(blank=True)
    source = models.CharField(max_length=64, default="system")

    objects = GuardedDeleteManager()

    class Meta:
        ordering = ["-changed_at", "-id"]

    def delete(self, using=None, keep_parents=False):
        raise ProtectedError("User block history is immutable.", [self])
