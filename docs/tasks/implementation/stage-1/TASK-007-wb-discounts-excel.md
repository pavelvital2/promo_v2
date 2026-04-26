# TASK-007: WB Discounts Excel

## ID

TASK-007-wb-discounts-excel

## Роль агента

Разработчик Codex CLI, WB discounts Excel.

## Цель

Реализовать WB discounts Excel check/process exactly по утверждённой спецификации, включая загрузку 1 price file и 1-20 promo files, нормализацию, расчёт, detail rows, snapshots and output workbook rules.

## Task-scoped входные документы

- `AGENTS.md`
- `docs/tasks/implementation/stage-1/IMPLEMENTATION_TASKS.md`
- `docs/product/WB_DISCOUNTS_EXCEL_SPEC.md`
- `docs/product/OPERATIONS_SPEC.md`
- `docs/architecture/FILE_CONTOUR.md`
- `docs/architecture/DATA_MODEL.md`
- `docs/product/PERMISSIONS_MATRIX.md`
- `docs/stages/stage-1/ACCEPTANCE_TESTS.md`
- `docs/gaps/GAP_REGISTER.md` closed GAP-0002, GAP-0003, GAP-0004, GAP-0008
- `docs/adr/ADR_LOG.md` ADR-0009, ADR-0010, ADR-0011, ADR-0013
- `docs/testing/TEST_PROTOCOL.md`
- `docs/testing/ACCEPTANCE_CHECKLISTS.md`
- `docs/orchestration/DOCUMENTATION_UPDATE_PROTOCOL.md`

## Релевантные разделы ТЗ

- §12
- §14
- §15
- §17
- §23
- §24
- §27

## Разрешённые файлы / области изменения

- WB discounts Excel Django app/module.
- WB-specific parsers, validators, calculation services and templates.
- WB parameter model usage and snapshots.
- Tests for WB rules, including approved defaults, reason/result codes and out-of-range error semantics.
- Documentation updates after approved WB gap closure.

## Запрещённые области

- Changing approved WB default parameter values without new ADR/documentation update.
- Adding, renaming or replacing approved WB reason/result codes without new ADR/documentation update.
- Changing out-of-range WB result semantics from row error/process forbidden without customer decision.
- Modifying any workbook column except `Новая скидка` during process.
- API upload or API calculation mode.

## Зависимости

- TASK-001 through TASK-006.
- ADR-0009, ADR-0010 and ADR-0011 are accepted.

## Expected output

- WB check creates operation result without output workbook.
- WB process creates output workbook and changes only `Новая скидка`.
- Decimal arithmetic and `ceil` rules follow `docs/product/WB_DISCOUNTS_EXCEL_SPEC.md`.
- Applied WB parameters are snapshotted.
- Detail rows use approved reason/result codes only.

## Acceptance criteria

- WB acceptance checklist items are satisfied by automated/synthetic coverage and the accepted real comparison artifact `WB-REAL-001` where applicable.
- Process cannot run on check with errors.
- Confirmable warnings require explicit confirmation.
- Check/process use same normalization and актуальность rules.

## Required checks

- Unit tests for parsing, normalization, aggregation, formula and branch rules.
- Integration tests for check/process operations and file links.
- Workbook immutability/output tests.
- Permission tests for upload/run/download.
- Synthetic edge-case tests where allowed by ТЗ.

## Handoff format

Использовать формат из `docs/tasks/implementation/stage-1/README.md`; include that GAP-0002/0003/0004 are resolved and GAP-0008 real WB/Ozon comparison artifact gate is closed for accepted registered artifacts.

## Gaps/blockers

No open WB implementation gap remains for GAP-0002, GAP-0003 or GAP-0004. Formal real WB comparison for `WB-REAL-001` is accepted; new customer artifacts, if introduced later, must be registered before use.
