# TASK-PC-009-tests-and-acceptance.md

ID: TASK-PC-009  
Тип задачи: тестирование Stage 3.0 / acceptance  
Агент: тестировщик Codex CLI  
Цель: execute and report Stage 3 Product Core test protocol and acceptance checklists.

## Источник Истины

- `docs/testing/STAGE_3_PRODUCT_CORE_TEST_PROTOCOL.md`
- `docs/testing/STAGE_3_PRODUCT_CORE_ACCEPTANCE_CHECKLISTS.md`
- `docs/stages/stage-3-product-core/STAGE_3_PRODUCT_CORE_ACCEPTANCE_TESTS.md`
- `docs/traceability/STAGE_3_PRODUCT_CORE_TRACEABILITY_MATRIX.md`

## Входные Документы

- package TASK-PC-009 from `STAGE_3_PRODUCT_CORE_AGENT_READING_PACKAGES.md`
- implementation reports from TASK-PC-001..TASK-PC-008

## Разделы ТЗ Для Чтения

- task source §14, §22

## Связанные ADR/GAP

- all Stage 3 ADR entries
- open gaps affecting implemented slice

## Разрешённые Файлы / Области Изменения

- tests
- test reports under `docs/testing/`
- defects/gap updates if required by protocol

## Запрещённые Файлы / Области Изменения

- production code changes unless a separate fix task is issued
- changing specs to match defects
- synthetic replacement for required regression artifacts

## Ожидаемый Результат

- Test execution report.
- Acceptance checklist status.
- Defects or gaps for failed/blocked tests.
- Regression evidence for Stage 1/2.

## Критерии Завершённости

- All mandatory test groups pass or have explicit defect/gap.
- No secret redaction failure remains open.
- No spec-blocking issue is hidden in test notes.

## Обязательные Проверки

- full or orchestrator-approved test suite
- migration validation checks
- UI permission/access checks
- Stage 1/2 regression groups

## Формат Отчёта

Use protocol format: Test ID, scenario, expected, actual, status, defect/GAP link, notes.

## Получатель Результата

Оркестратор -> аудитор/release decision.

Нужен аудит: да.  
Нужны тесты: да.  
Нужен техрайтер: да, after final pass.

