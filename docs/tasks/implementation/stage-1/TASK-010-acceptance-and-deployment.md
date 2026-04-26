# TASK-010: Acceptance and Deployment

## ID

TASK-010-acceptance-and-deployment

## Роль агента

Разработчик/тестировщик Codex CLI, acceptance and deployment readiness.

## Цель

Подготовить formal acceptance, deployment/runbook execution, backup/restore checks and production readiness package for этап 1.

## Task-scoped входные документы

- `AGENTS.md`
- `docs/tasks/implementation/stage-1/IMPLEMENTATION_TASKS.md`
- `docs/stages/stage-1/ACCEPTANCE_TESTS.md`
- `docs/testing/ACCEPTANCE_CHECKLISTS.md`
- `docs/testing/TEST_PROTOCOL.md`
- `docs/operations/RELEASE_AND_UPDATE_RUNBOOK.md`
- `docs/architecture/FILE_CONTOUR.md`
- `docs/product/OPERATIONS_SPEC.md`
- `docs/architecture/AUDIT_AND_TECHLOG_SPEC.md`
- `docs/gaps/GAP_REGISTER.md` closed GAP-0007, GAP-0008, GAP-0009
- `docs/adr/ADR_LOG.md` ADR-0012, ADR-0013, ADR-0014
- `docs/orchestration/DOCUMENTATION_UPDATE_PROTOCOL.md`

## Релевантные разделы ТЗ

- §22
- §24
- §25-§27

## Разрешённые файлы / области изменения

- Test/acceptance suites.
- Deployment scripts/config examples for Django/nginx/systemd.
- Release/update runbook updates.
- Acceptance data registry after customer files are provided.
- Documentation updates required for handoff.

## Запрещённые области

- Inventing customer control files or expected results.
- Weakening approved backup frequency/depth without new ADR/documentation update.
- Implementing audit/techlog cleanup through ordinary UI.
- Changing WB/Ozon logic to match tests instead of specs.

## Зависимости

- TASK-001 through TASK-009.
- ADR-0012 and ADR-0014 accepted for production readiness policy.
- Customer acceptance artifact gate for real WB/Ozon output comparison is closed before stage 2 development: `WB-REAL-001` and `OZ-REAL-001` are provided, checksummed, compared and recorded.
- Future new customer artifacts, if introduced, must be registered before formal comparison for that new set.

## Expected output

- Executable acceptance test plan.
- Control file registry populated with accepted `WB-REAL-001` / `OZ-REAL-001`; future artifacts added after customer delivery.
- Deployment and rollback procedure verified for Django stack.
- Backup/restore check procedure implemented according to ADR-0012.
- Audit/techlog retention cleanup procedure implemented according to ADR-0014, if included in release scope.

## Acceptance criteria

- All stage 1 acceptance checklists pass or have explicit accepted remarks.
- WB/Ozon formal real comparison areas reference accepted registered artifacts, not stale `blocked_by_artifact_gate` placeholders.
- Backup and restore are tested according to approved policy.
- Release/update runbook commands match actual Django project.
- Formal WB/Ozon file comparison uses customer-provided expected results only.

## Required checks

- Full automated test suite.
- Acceptance tests with registered control files.
- Backup/restore test according to approved policy.
- Deployment smoke test.
- Audit/techlog retention check according to approved 90-day non-UI policy.

## Handoff format

Использовать формат из `docs/tasks/implementation/stage-1/README.md`; include pass/fail/blocked table for every acceptance area.

## Gaps/blockers

Production policy decisions for GAP-0007 and GAP-0009 are resolved, and GAP-0008 has a resolved project decision. The real WB/Ozon comparison artifact gate is closed for `WB-REAL-001` / `OZ-REAL-001`. Agents must not invent files or expected results for future new artifacts.
