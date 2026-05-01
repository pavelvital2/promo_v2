# OZON_ELASTIC_UI_READING_PACKAGE.md

Статус: task-scoped reading package for future Ozon Elastic UI implementation.

## Назначение

Пакет чтения для будущей задачи реализации UI-приведения страницы:

```text
Маркетплейсы / Ozon / Акции / API / Эластичный бустинг
```

в целевое состояние Stage 0. Пакет не разрешает писать продуктовый код сам по себе; реализация стартует только отдельной задачей после audit pass проектной документации.

## Обязательные документы

Будущий UI-исполнитель читает:

- `AGENTS.md`
- `docs/README.md`
- `docs/DOCUMENTATION_MAP.md`
- `docs/orchestration/AGENTS.md`
- `docs/orchestration/DOCUMENTATION_UPDATE_PROTOCOL.md`
- `docs/tasks/implementation/stage-0/OZON_ELASTIC_UI_READING_PACKAGE.md`
- `docs/tasks/design/stage-0/STAGE_0_OZON_ELASTIC_UI_TZ.md`
- `docs/reports/WEB_PANEL_UX_AUDIT_2026-04-30.md`
- `docs/product/OZON_API_ELASTIC_UI_SPEC.md`
- `docs/testing/STAGE_0_OZON_ELASTIC_UI_ACCEPTANCE_CHECKLIST.md`
- `docs/product/PERMISSIONS_MATRIX.md`
- `docs/product/OPERATIONS_SPEC.md`
- `docs/architecture/FILE_CONTOUR.md`
- `docs/architecture/AUDIT_AND_TECHLOG_SPEC.md`
- `docs/gaps/GAP_REGISTER.md`
- `docs/adr/ADR_LOG.md`

## Профильные разделы обязательны

В `docs/product/OZON_API_ELASTIC_UI_SPEC.md` обязательно читать полностью:

- `Инварианты Stage 0`;
- `Page Structure`;
- `Permissions`;
- `Tab Рабочий процесс`;
- `Seven Operator Steps`;
- `Tab Результат`;
- `Tab Диагностика`;
- `Operation Card Amendment`;
- `Marketplace Navigation Amendment`.

В `docs/product/OZON_API_ELASTIC_BOOSTING_SPEC.md` читать только связанные разделы:

- `Каноническое правило расчёта`;
- `Step codes`;
- `Workflow`;
- `Closed Stage 2.2 planning/status catalogs`;
- `API-level reason/result codes`;
- `Secret and snapshot safety`.

В `docs/stages/stage-2/STAGE_2_2_OZON_SCOPE.md` читать только:

- `Назначение`;
- `Реализуемый scope`;
- `Не входит в scope`;
- `Навигационная иерархия`;
- `Workflow кнопок`;
- `Phase gates`.

## ADR/GAP для destructive upload/deactivate и manual Excel

Обязательные ADR:

- ADR-0023: Ozon Elastic Boosting UI workflow and deactivate safety;
- ADR-0026: Ozon Elastic active not-upload-ready rows are removed from action;
- ADR-0027: Ozon Elastic result review is calculation result state;
- ADR-0028: Ozon Elastic candidate/active collision handling;
- ADR-0029: Ozon Elastic Boosting action identification;
- ADR-0032: Ozon Elastic manual upload Excel uses Stage 1-compatible template;
- ADR-0033: Ozon Elastic live activate/deactivate payload policy;
- ADR-0034: Ozon API conservative configurable rate/batch/retry policy;
- ADR-0035: Ozon API connection check uses read-only actions endpoint.

Обязательные GAP checks:

- `GAP-0014`..`GAP-0022` current statuses before coding;
- any new open Stage 0/UI gap added after this package.

## Документы, которые не перечитываются целиком

Не перечитывать целиком без отдельного указания оркестратора:

- `itogovoe_tz_platforma_marketplace_codex.txt`;
- all Stage 1 implementation tasks;
- all Stage 2.1 WB implementation tasks;
- full `docs/architecture/DATA_MODEL.md`, unless implementation touches data model;
- full `docs/product/OZON_DISCOUNTS_EXCEL_SPEC.md`, unless calculation behavior or Excel regression is explicitly in task scope;
- historical test reports.

If a fact is needed from these documents and is not already in the required package, ask the orchestrator or record a gap instead of inferring UX/functionality.

## Implementation Boundaries

Allowed in a future implementation task only if explicitly listed by that task:

- Ozon Elastic page templates/views/components;
- marketplace navigation UI;
- operation card UI rendering for long values;
- focused UI tests and acceptance report.

Forbidden without separate approved task:

- changing Ozon Elastic calculation logic;
- adding, renaming or deleting reason/result codes;
- changing permission codes or seed roles;
- changing file scenarios, retention or version links;
- changing operation step codes or making review a separate operation;
- changing audit action codes or techlog event types;
- using raw secrets or raw sensitive API responses in UI/tests/reports;
- implementing future planned marketplace sections as working features.

## Questions Route

The implementation agent must not decide UX/functionality gaps independently.

Escalate through orchestrator to customer when a required behavior is absent, contradictory or ambiguous for:

- what the operator can do from workflow/result tabs;
- which data is shown or hidden in workflow versus diagnostics;
- deactivate confirmation behavior;
- manual Excel representation;
- marketplace navigation behavior for inactive future sections;
- operation card default visibility if it would change audit/debug exposure;
- mobile behavior that changes functional access rather than presentation.

Record such questions in `docs/gaps/GAP_REGISTER.md` when they block implementation or acceptance.
