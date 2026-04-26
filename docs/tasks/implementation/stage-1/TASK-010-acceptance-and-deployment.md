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
- Customer acceptance artifact gate closed before formal acceptance / production acceptance sign-off: real WB/Ozon control files, input checksums, old program results, expected summary, row-level expected results and edge-case sets are provided and recorded.
- This artifact gate does not block implementation of the stage 1 platform scaffold or development/synthetic edge-case testing.

## Expected output

- Executable acceptance test plan.
- Control file registry populated after customer delivery.
- Deployment and rollback procedure verified for Django stack.
- Backup/restore check procedure implemented according to ADR-0012.
- Audit/techlog retention cleanup procedure implemented according to ADR-0014, if included in release scope.

## Acceptance criteria

- All stage 1 acceptance checklists not waiting for customer artifacts pass.
- WB/Ozon formal acceptance areas waiting for customer artifacts have explicit `blocked_by_artifact_gate` status as an artifact gate, not as an unresolved GAP blocker.
- Backup and restore are tested according to approved policy.
- Release/update runbook commands match actual Django project.
- Formal WB/Ozon file comparison uses customer-provided expected results only.

## Required checks

- Full automated test suite.
- Acceptance tests with control files after artifact delivery.
- Backup/restore test according to approved policy.
- Deployment smoke test.
- Audit/techlog retention check according to approved 90-day non-UI policy.

## Handoff format

Использовать формат из `docs/tasks/implementation/stage-1/README.md`; include pass/fail/blocked table for every acceptance area.

## Gaps/blockers

Production policy decisions for GAP-0007 and GAP-0009 are resolved, and GAP-0008 has a resolved project decision. Remaining gate is an acceptance artifact gate: formal acceptance / production acceptance stays `blocked_by_artifact_gate` until real WB/Ozon control files, checksums, old program results, expected summary, row-level expected results and edge-case sets are provided and recorded. Agents must not invent these files or expected results.
