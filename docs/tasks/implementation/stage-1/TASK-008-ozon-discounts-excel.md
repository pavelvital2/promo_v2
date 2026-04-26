# TASK-008: Ozon Discounts Excel

## ID

TASK-008-ozon-discounts-excel

## Роль агента

Разработчик Codex CLI, Ozon discounts Excel.

## Цель

Реализовать Ozon discounts Excel check/process exactly по утверждённой спецификации, включая один `.xlsx`, лист `Товары и цены`, чтение со строки 4, правила 1-7 and process writes only K/L.

## Task-scoped входные документы

- `AGENTS.md`
- `docs/tasks/implementation/stage-1/IMPLEMENTATION_TASKS.md`
- `docs/product/OZON_DISCOUNTS_EXCEL_SPEC.md`
- `docs/product/OPERATIONS_SPEC.md`
- `docs/architecture/FILE_CONTOUR.md`
- `docs/architecture/DATA_MODEL.md`
- `docs/product/PERMISSIONS_MATRIX.md`
- `docs/stages/stage-1/ACCEPTANCE_TESTS.md`
- `docs/gaps/GAP_REGISTER.md` closed GAP-0008
- `docs/adr/ADR_LOG.md` ADR-0013
- `docs/testing/TEST_PROTOCOL.md`
- `docs/testing/ACCEPTANCE_CHECKLISTS.md`
- `docs/orchestration/DOCUMENTATION_UPDATE_PROTOCOL.md`

## Релевантные разделы ТЗ

- §12
- §16
- §17
- §23
- §24
- §27

## Разрешённые файлы / области изменения

- Ozon discounts Excel Django app/module.
- Ozon-specific parser, validator, rule engine and templates.
- Tests for all 7 rules and workbook output.
- Documentation updates directly caused by implementation.

## Запрещённые области

- Changing Ozon 7-rule order.
- Writing any workbook cells except K and L during process.
- Creating Ozon user-managed discount parameters.
- Percent discount as separate result if not in spec.
- API upload or API calculation mode.

## Зависимости

- TASK-001 through TASK-006.

## Expected output

- Ozon check creates operation result without output workbook.
- Ozon process creates output workbook and changes only K/L.
- K contains only `Да` or empty.
- L contains number or empty.
- Process uses допустимая and актуальная check basis.

## Acceptance criteria

- Ozon acceptance checklist items are satisfied by automated/synthetic coverage and the accepted real comparison artifact `OZ-REAL-001` where applicable.
- All 7 decision rules covered by tests.
- File/version links and operation details are stored.
- Permission checks match `docs/product/PERMISSIONS_MATRIX.md`.

## Required checks

- Unit tests for parser, validation and 7 rules.
- Integration tests for check/process and check актуальность.
- Workbook output tests for K/L-only writes.
- Permission tests for upload/run/download.
- Synthetic edge-case tests where allowed by ТЗ.

## Handoff format

Использовать формат из `docs/tasks/implementation/stage-1/README.md`; include that GAP-0008 real WB/Ozon comparison artifact gate is closed for accepted registered artifacts.

## Gaps/blockers

Formal real Ozon comparison for `OZ-REAL-001` is accepted. Do not invent customer expected results for future new artifacts.
