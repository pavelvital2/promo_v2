# TEST_PROTOCOL.md

Трассировка: ТЗ §12, §15-§17, §22, §24, §27.

## Уровни тестирования

- unit tests для нормализации, формул, decision rules и прав;
- integration tests для operations/run/files/parameters;
- UI/API tests для сценариев пользователя;
- acceptance tests по контрольным Excel-файлам;
- recovery tests для сбойных operations и backup/restore.

## Минимальные тестовые области этапа 1

| Область | Обязательные проверки |
| --- | --- |
| Auth/access | логин/пароль, роли, запреты, store access, owner protection |
| Stores | карточка, история, API-блок с пометкой этапа 2 |
| Parameters | WB cascade, snapshot, history, отсутствие Ozon params |
| Operations | statuses, check/process split, актуальность check, rerun |
| Files | upload, versions, retention, download rights |
| WB | состав файлов, колонки, нормализация, aggregation, formula, workbook immutability |
| Ozon | лист/колонки, 7 rules, K/L writes only |
| Audit/TechLog | раздельные записи, фильтры, карточки |
| Exports | списки и detail reports |
| Recovery | interrupted_failed, no auto-resume |

## Требования к тестовым данным

Контрольные файлы должны храниться отдельно от production uploads. Для каждого набора фиксируются:

- source;
- marketplace;
- scenario;
- expected summary;
- expected row-level results;
- allowed differences;
- checksum исходного файла.

Фактические контрольные файлы фиксируются в отдельном тестовом контуре и регистрируются в `docs/testing/CONTROL_FILE_REGISTRY.md`.

## Stage 2.1 WB API

Stage 2.1 WB API проверяется по отдельному протоколу `docs/testing/STAGE_2_1_WB_TEST_PROTOCOL.md`.

Общие обязательные правила:

- Stage 1 WB Excel regression не меняется и должен оставаться зелёным.
- Реальные `test_files/secrets` не используются и не модифицируются.
- WB API tests по умолчанию используют mocks/stubs официальных endpoints.
- Secret redaction является обязательной проверкой для TASK-011..TASK-017.

Проектное решение по контрольным файлам закрыто: заказчик передаёт реальные WB/Ozon файлы и результаты старой программы, а тестовый контур может дополнительно содержать edge-case наборы. На 2026-04-26 реальные WB/Ozon comparison artifacts зарегистрированы как `WB-REAL-001` и `OZ-REAL-001` со статусом `accepted`; тестировщик не заменяет будущие customer artifacts синтетическими данными.

## Протокол результата теста

```md
Test ID:
Scenario:
Input files/checksums:
Expected:
Actual:
Status: pass / fail / blocked
Defect/GAP link:
Notes:
```

## Блокеры тестирования

Если для нового marketplace/scenario нет контрольных файлов, тестировщик не придумывает их как замену реальным. Он может подготовить synthetic edge-case files по ТЗ, но отсутствие обязательных customer artifacts фиксирует как `blocked_by_artifact_gate` только для этого нового набора, а не для уже accepted `WB-REAL-001` / `OZ-REAL-001`.
