# AUDIT_REPORT_TASK_003

Дата: 2026-04-25

Роль: Аудитор Codex CLI TASK-003 stores/cabinets/connections.

## status

FAIL

Причина: найдено major-нарушение в контуре protected secret metadata. API-блок в целом реализован как подготовка этапа 2 и не подменяет Excel-сценарии, но metadata validation не закрывает вложенные secret-like ключи, а карточка магазина выводит metadata как raw value.

## checked scope

- Root/orchestration: `AGENTS.md`, `docs/README.md`, `docs/orchestration/AGENTS.md`, `docs/roles/READING_PACKAGES.md`.
- Task: `docs/tasks/implementation/stage-1/TASK-003-stores-cabinets-connections.md`.
- Architecture/product specs: `docs/architecture/DATA_MODEL.md`, `docs/product/PERMISSIONS_MATRIX.md`, `docs/product/UI_SPEC.md`, `docs/architecture/DELETION_ARCHIVAL_POLICY.md`, `docs/product/modules/README.md`, `docs/adr/ADR_LOG.md`.
- Prior context: `docs/audit/AUDIT_REPORT_TASK_002_ROUND_3.md`, `docs/testing/TEST_REPORT_TASK_002.md`.
- Code: `apps/stores/**`, `apps/identity_access/**` only for TASK-002 object access helpers, `config/urls.py`.
- Process artifact: `docs/testing/TEST_REPORT_TASK_003.md`.

Audit did not change product code. Only this audit report was created.

## audit method

- Compared TASK-003 implementation against task boundaries and acceptance criteria: groups/stores/connections/history/object access/API-stage-2-only.
- Reviewed model fields/migrations against `DATA_MODEL.md` required entities and visible id rules.
- Reviewed views/templates for object access checks, API-block messaging, secret exposure, and absence of API discount scenarios.
- Reviewed TASK-002 helpers usage for owner/global/local/object access behavior.
- Reviewed delete/archive protections against `DELETION_ARCHIVAL_POLICY.md`.
- Searched stores scope for WB/Ozon discount logic, API calls, and overreach.
- Ran minimal sanity commands requested by orchestration.
- Existing tests were read only for coverage awareness; this audit is not a tester pass.

## findings

### blocker

None found.

### major

1. Nested secret-like metadata keys are not rejected and can be exposed in UI/history.

   Required behavior: TASK-003 requires protected secret handling without exposing protected secrets and explicitly allows only protected references (`docs/tasks/implementation/stage-1/TASK-003-stores-cabinets-connections.md:44`-`50`, `docs/tasks/implementation/stage-1/TASK-003-stores-cabinets-connections.md:65`-`70`, `docs/tasks/implementation/stage-1/TASK-003-stores-cabinets-connections.md:83`-`85`). `DATA_MODEL.md` requires API-block/connection metadata history without protected secret disclosure (`docs/architecture/DATA_MODEL.md:88`-`99`). UI spec requires API secrets hidden without right (`docs/product/UI_SPEC.md:274`-`289`).

   Evidence: `ConnectionBlock.clean()` checks only first-level metadata keys (`apps/stores/models.py:176`-`187`). The history sanitizer also checks only first-level keys (`apps/stores/services.py:73`-`89`). The store card renders `connection.metadata` directly (`apps/stores/templates/stores/store_card.html:49`-`53`). A payload like `{"integration": {"api_token": "..."}}` is not rejected by the current key scan and would be displayed as raw metadata on the store card and serialized into history through `connection.metadata`.

   Impact: this violates the explicit protected secret / metadata requirement for a nested JSON metadata shape. Return to developer to make metadata secret-key validation and redaction recursive, or otherwise constrain metadata to a flat schema and document/enforce that constraint.

### minor

1. `StoreAccount.visible_id` stability is enforced by UI/admin convention, not by model-level immutability.

   Required behavior: visible identifiers must be stable after creation (`docs/architecture/DATA_MODEL.md:221`-`240`) and TASK-003 expects `STORE-NNNNNN` records (`docs/tasks/implementation/stage-1/TASK-003-stores-cabinets-connections.md:57`-`63`).

   Evidence: `StoreAccount.save()` generates `STORE-{pk:06d}` when the field is empty (`apps/stores/models.py:103`-`107`), and forms/admin do not expose normal editing (`apps/stores/forms.py:8`-`12`, `apps/stores/admin.py:21`-`35`). However the model has no guard against later assignment and save of a different `visible_id`.

   Impact: not observed through current UI paths, but the model does not fully enforce the architectural invariant. Recommended to add a model-level immutability guard in developer follow-up.

## conforming observations

- `BusinessGroup`, `StoreAccount`, `ConnectionBlock`, `StoreAccountChangeHistory` are present with the required core fields and migrations (`apps/stores/models.py:26`-`238`, `apps/stores/migrations/0001_initial.py:15`-`44`, `apps/stores/migrations/0002_businessgroup_comments_businessgroup_updated_at_and_more.py:16`-`70`).
- `STORE-NNNNNN` visible id is generated for `StoreAccount` (`apps/stores/models.py:103`-`107`) and shown/searchable in list/card templates (`apps/stores/templates/stores/store_list.html:8`-`56`, `apps/stores/templates/stores/store_card.html:3`-`8`).
- API-block is marked as stage 2 preparation via `API_STAGE_2_NOTICE` (`apps/stores/services.py:18`) and displayed in list/card/form templates (`apps/stores/templates/stores/store_list.html:33`, `apps/stores/templates/stores/store_card.html:28`-`30`, `apps/stores/templates/stores/connection_form.html:7`-`8`). `ConnectionBlock.is_stage1_used` is default false/editable false with DB check and model validation (`apps/stores/models.py:154`-`170`, `apps/stores/models.py:176`-`191`).
- No real WB/Ozon API calls, API discount execution, workbook processing, or TASK-004+ discount business logic was found in `apps/stores/**`; references are limited to store metadata, API-block labels, and permission codes.
- Secret reference values are redacted in store card and connection history through `[ref-set]` / `[empty]` for the normal product path (`apps/stores/templates/stores/store_card.html:52`, `apps/stores/services.py:69`-`90`, `apps/stores/services.py:177`-`218`).
- Store change history is recorded for store fields, connection fields, and StoreAccess changes through service/admin/signal paths (`apps/stores/services.py:93`-`112`, `apps/stores/services.py:153`-`218`, `apps/stores/admin.py:36`-`62`, `apps/stores/admin.py:88`-`108`, `apps/stores/signals.py:20`-`34`).
- Object access/action checks use TASK-002 helpers: `visible_stores_queryset()` and `require_store_permission()` delegate to `has_permission()` (`apps/stores/services.py:122`-`141`), and views apply those checks before card/edit/history/connection actions (`apps/stores/views.py:24`-`157`). TASK-002 helper logic preserves owner/global/direct-deny/store-scope semantics (`apps/identity_access/services.py:38`-`132`).
- Delete/archive protections are present for used stores, connection blocks, and store history (`apps/stores/models.py:51`-`54`, `apps/stores/models.py:109`-`131`, `apps/stores/models.py:193`-`207`, `apps/stores/models.py:237`-`238`) and admin delete buttons are hidden for protected stores/connections/history (`apps/stores/admin.py:63`-`66`, `apps/stores/admin.py:110`-`138`).

## process findings

### minor

1. `docs/testing/TEST_REPORT_TASK_003.md` was created with role `Разработчик Codex CLI TASK-003` (`docs/testing/TEST_REPORT_TASK_003.md:1`-`6`).

   This is a process issue, not a product-code defect. The developer may report developer sanity checks, but a document under `docs/testing/` named as a test report must not be treated as an independent tester acceptance artifact. It should either be superseded by a tester-created TASK-003 test report or reclassified by the orchestrator as developer handoff/check output.

## sanity commands/results

| Command | Result |
| --- | --- |
| `.venv/bin/python manage.py check` | PASS: `System check identified no issues (0 silenced).` |
| `.venv/bin/python manage.py makemigrations --check --dry-run` | PASS for model diff: `No changes detected`; emitted environment warning because PostgreSQL credential/history check could not authenticate to `127.0.0.1:5432` as user `promo_v2`. |
| `.venv/bin/python manage.py test apps.stores` | SANITY ONLY / BLOCKED BY ENV: Django found 8 tests but failed before execution because PostgreSQL rejected password authentication for user `promo_v2` on `127.0.0.1:5432`. This is not a tester pass. |

## environment limitations

- Default database settings target local PostgreSQL as `promo_v2`; authentication failed in migration-history and test-database checks.
- I did not use SQLite override for this audit, to avoid turning the audit into a tester pass.
- Product code was not changed.
- This report is an architectural/task-boundary audit only; it does not replace a separate tester run.

## decision

TASK-003 is not accepted at audit level. Return to developer for the major secret metadata finding and the minor visible-id immutability hardening.

## recommendation

Separate tester is required after developer fixes and re-audit. The existing developer-created `docs/testing/TEST_REPORT_TASK_003.md` must not be used as the formal tester acceptance report.
