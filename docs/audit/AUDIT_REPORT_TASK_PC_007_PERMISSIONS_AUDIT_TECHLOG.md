# AUDIT_REPORT_TASK_PC_007_PERMISSIONS_AUDIT_TECHLOG.md

Дата аудита: 2026-05-01

Задача: TASK-PC-007 Permissions, Audit, Techlog

Статус: AUDIT PASS

## Scope

Повторно проверены документы и task-scoped пакет:

- `AGENTS.md`
- `docs/README.md`
- `docs/orchestration/AGENTS.md`
- `docs/DOCUMENTATION_MAP.md`
- `docs/stages/stage-3-product-core/STAGE_3_PRODUCT_CORE_AGENT_READING_PACKAGES.md`
- `docs/tasks/implementation/stage-3-product-core/TASK-PC-007-permissions-audit-techlog.md`
- `docs/product/PERMISSIONS_MATRIX.md`
- `docs/architecture/AUDIT_AND_TECHLOG_SPEC.md`
- `docs/architecture/DATA_MODEL.md`
- `docs/product/OPERATIONS_SPEC.md`
- `docs/gaps/GAP_REGISTER.md`
- `docs/adr/ADR_LOG.md`

Повторно проверены фактические изменения в зоне аудита:

- `apps/identity_access/seeds.py`
- `apps/identity_access/migrations/0011_seed_product_core_permissions.py`
- `apps/identity_access/tests.py`
- `apps/audit/models.py`
- `apps/audit/migrations/0010_alter_auditrecord_action_code.py`
- `apps/techlog/models.py`
- `apps/techlog/migrations/0009_alter_techlogrecord_event_type.py`
- `apps/product_core/services.py`
- `apps/product_core/tests.py`

## Re-audit Result

Первичный blocker `PC-007-BLOCKER-001` закрыт.

`docs/product/PERMISSIONS_MATRIX.md` требует для Stage 3 local admin: listing/snapshot `view/export/sync/map/unmap` only in assigned stores; product create/update/archive only if separately granted. Фактическая реализация теперь соответствует этому требованию:

- `marketplace_listing.archive` остаётся в permission catalog, что соответствует матрице как отдельное право;
- `apps/identity_access/seeds.py` исключает `marketplace_listing.archive` из `PRODUCT_CORE_LOCAL_ADMIN_CODES`;
- `apps/identity_access/migrations/0011_seed_product_core_permissions.py` не включает `marketplace_listing.archive` в `LOCAL_ADMIN_PERMISSIONS`;
- `apps/identity_access/tests.py` проверяет отсутствие `marketplace_listing.archive` у `ROLE_LOCAL_ADMIN` и отрицательный `has_permission(local_admin, "marketplace_listing.archive", store)`.

Новых blocking findings в проверенном scope не обнаружено.

## Passed Checks

- Owner/global admin protections в проверенной зоне не ослаблены: `users.owner.manage` не выдаётся global/local admin, owner bypass сохранён, direct deny для owner запрещён моделью.
- Direct user deny still wins: `has_permission()` сначала проверяет direct deny; Product Core/identity tests покрывают deny на Product Core listing permission.
- Store object access enforced for listings/snapshots: Product Core helpers проверяют права через конкретный `StoreAccount`; tests покрывают видимость только доступного store и блокировку чужого store.
- Audit catalog расширен кодами Product Core из `AUDIT_AND_TECHLOG_SPEC.md`; mapping helper пишет `ProductMappingHistory` and audit records для map/unmap/review/conflict.
- Techlog catalog расширен Stage 3 sync/migration event types with baseline severity; Product Core tests покрывают sync started and migration failed severity normalization.
- Sensitive contour: audit/techlog helpers and Product Core mapping helper вызывают `assert_no_secret_like_values`; tests покрывают secret rejection for audit, techlog and Product Core mapping context.
- Stage 1/2 permission semantics в проверенном diff не изменяются, кроме additive Product Core rights.

## Verification

Команды выполнены аудитором локально с `POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres`:

- `.venv/bin/python manage.py check` - OK.
- `.venv/bin/python manage.py makemigrations --check --dry-run` - OK, no changes detected.
- `git diff --check` - OK.
- `.venv/bin/python manage.py test apps.identity_access apps.product_core apps.operations --verbosity=1` - OK, 45 tests.
- `.venv/bin/python manage.py test apps.identity_access apps.audit apps.techlog apps.product_core --verbosity=1` - OK, 42 tests.

## Gaps

Новых GAP не зарегистрировано. Проверенный blocker был несоответствием реализации утверждённой матрице и закрыт исправлением seed/migration/tests.

## Final Decision

TASK-PC-007 Permissions, Audit, Techlog passes re-audit for the checked scope. Product Core local admin default seed no longer grants `marketplace_listing.archive`, and no new blockers were found.
