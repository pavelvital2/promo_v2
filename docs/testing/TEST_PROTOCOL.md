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

Фактические контрольные файлы не входят в этот документ и должны быть добавлены в отдельный тестовый контур после передачи заказчиком.

Проектное решение по контрольным файлам закрыто: заказчик передаёт реальные WB/Ozon файлы и результаты старой программы, а тестовый контур должен дополнительно содержать edge-case наборы. До фактической передачи файлов, checksums и expected results formal acceptance остаётся `blocked_by_artifact_gate`; тестировщик не заменяет эти артефакты синтетическими данными.

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

Если нет контрольных файлов, тестировщик не придумывает их как замену реальным. Он может подготовить synthetic edge-case files по ТЗ, но отсутствие реальных файлов фиксирует как `blocked_by_artifact_gate` для formal acceptance.
