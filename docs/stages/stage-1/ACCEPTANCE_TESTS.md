# ACCEPTANCE_TESTS.md

Трассировка: ТЗ §24.

## Принцип приёмки

Приёмка этапа 1 выполняется по комбинированному набору:

- реальные рабочие файлы WB/Ozon;
- результаты старой программы как источник контрольных результатов;
- специально подготовленные тестовые файлы с крайними случаями;
- ожидаемые результаты по каждому тесту;
- список допустимых и недопустимых расхождений.

Итоговым эталоном являются правила итогового ТЗ и исполнительной документации. Если старая программа расходится с ТЗ, расхождение фиксируется отдельно как ошибка ТЗ, ошибка старой программы или осознанное отличие новой платформы.

## Обязательные группы тестов

Проектное решение по `GAP-0008` закрыто: заказчик передаёт реальные контрольные WB/Ozon файлы и результаты старой программы, дополнительно должны быть edge-case наборы. Фактические контрольные файлы, checksums и expected results пока не переданы; это не заменяется синтетическими данными и остаётся acceptance artifact gate. До получения и фиксации этих артефактов формальная приёмка этапа 1 имеет статус `blocked_by_artifact_gate`, даже если разработческие и synthetic edge-case tests выполнены.

| ID | Группа | Покрытие |
| --- | --- | --- |
| ACC-WB-001 | Корректные WB-файлы | валидный price file, 1-20 promo files, output `Новая скидка` |
| ACC-WB-002 | Колонки WB | отсутствие обязательных колонок price/promo |
| ACC-WB-003 | Workbook WB | повреждённый `.xlsx`, невозможность записи |
| ACC-WB-004 | Нормализация WB | пробелы, NBSP, запятые, `.0`, пустые и нечисловые значения |
| ACC-WB-005 | Дубли WB | дубли `Артикул WB` в price file |
| ACC-WB-006 | Товары без акций WB | ветка `fallback_no_promo_percent` |
| ACC-WB-007 | Превышение порога WB | ветка `fallback_over_threshold_percent` |
| ACC-WB-008 | Диапазон скидки | значения вне 0-100 являются row error `wb_discount_out_of_range`, check с ошибками, process запрещён |
| ACC-OZ-001 | Корректный Ozon-файл | лист `Товары и цены`, строки с 4-й |
| ACC-OZ-002 | Колонки Ozon | J/K/L/O/P/R по буквам |
| ACC-OZ-003 | Workbook Ozon | повреждённый файл, невозможность сохранить |
| ACC-OZ-004 | Все ветки Ozon | 7 decision rules |
| ACC-OZ-005 | Запрет изменения колонок | меняются только K и L |
| ACC-OPS-001 | Check/process | отдельные operations, связь process -> check |
| ACC-OPS-002 | Актуальность check | файлы, версии, параметры, logic version |
| ACC-FILE-001 | Версии файлов | повторная загрузка создаёт новую версию |
| ACC-FILE-002 | Retention | файлы 3 дня, metadata 90 дней |
| ACC-SEC-001 | Права | роли, объектные ограничения, запреты |
| ACC-AUD-001 | Аудит/техжурнал | раздельные контуры и карточки |

## Реестр фактических контрольных наборов

Этот раздел заполняется только после передачи файлов заказчиком и результатов старой программы. До этого строки имеют статус `blocked_by_artifact_gate`, а agents не создают фиктивные контрольные файлы, checksums или expected results от имени заказчика.

| Set ID | Marketplace | Scenario | Source file(s) | Input checksum(s) | Old program result | Expected summary | Expected row-level results | Allowed differences | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TBD-WB-REAL-001 | WB | real working files | pending customer delivery | pending | pending | pending | pending | pending | blocked_by_artifact_gate |
| TBD-OZ-REAL-001 | Ozon | real working file | pending customer delivery | pending | pending | pending | pending | pending | blocked_by_artifact_gate |
| TBD-WB-EDGE-001 | WB | synthetic edge cases by ТЗ | pending tester creation after implementation plan | pending | not applicable | pending | pending | by ТЗ | pending tester creation; formal acceptance still blocked_by_artifact_gate until real files arrive |
| TBD-OZ-EDGE-001 | Ozon | synthetic edge cases by ТЗ | pending tester creation after implementation plan | pending | not applicable | pending | pending | by ТЗ | pending tester creation; formal acceptance still blocked_by_artifact_gate until real files arrive |

## Шаблон карточки контрольного набора

```md
Set ID:
Marketplace:
Scenario:
Source: customer_real_file / old_program_result / synthetic_edge_case
Input files:
Input checksums:
Related old program output:
Expected summary:
Expected row-level results:
Expected output workbook checks:
Allowed differences:
Disallowed differences:
Related requirements:
Status: blocked / ready / executed / accepted / rejected
GAP/defect links:
```

## Правила сравнения output workbook

WB:

- сравнивается только разрешённая колонка `Новая скидка` и неизменность остальных колонок/строк;
- порядок строк должен сохраниться;
- формулы и пригодность workbook не должны разрушаться;
- расчёт выполняется decimal + ceil.

Ozon:

- сравниваются K и L;
- J, O, P, R, остальные колонки, листы и служебные области не меняются;
- K содержит только `Да` или пусто;
- L содержит число или пусто.

## Допустимые расхождения

Допустимы только расхождения, явно классифицированные в протоколе:

- старая программа ошибалась относительно ТЗ;
- ТЗ признано требующим исправления;
- новая система имеет осознанное отличие, утверждённое заказчиком.

## Недопустимые расхождения

Недопустимы:

- отличие от формул и порядка правил ТЗ;
- изменение запрещённых колонок;
- объединение check/process;
- потеря связи operation с file version;
- отсутствие snapshot параметров;
- отсутствие detail audit/reason code;
- игнорирование object access;
- подмена Excel-режима API-режимом.

## Протокол фиксации расхождений

```md
ID расхождения:
Дата:
Файл/набор:
Сценарий:
Ожидаемый результат:
Фактический результат:
Сравнение со старой программой:
Классификация:
Решение:
Ответственный:
Статус:
```

## Критерий принятия этапа 1

Этап 1 готов к эксплуатационной приёмке, если:

- acceptance artifact gate закрыт: переданы реальные WB/Ozon файлы, checksums, результаты старой программы и expected results;
- все обязательные группы тестов выполнены;
- критические расхождения закрыты;
- открытые расхождения классифицированы и не блокируют замену текущего Excel-сценария;
- backup/restore/update runbook проверен;
- аудит прав, операций, файлов и WB/Ozon логики имеет статус pass или pass with accepted remarks.
