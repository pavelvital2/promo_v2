# CONTROL_FILE_REGISTRY.md

Трассировка: ТЗ §24; `GAP-0008`; `ADR-0013`.

## Назначение

Реестр фиксирует фактические контрольные наборы для formal acceptance этапа 1. До передачи заказчиком реальных WB/Ozon файлов, checksums, результатов старой программы, expected summary, row-level expected results и edge-case sets формальная приёмка остаётся `blocked_by_artifact_gate`.

Агенты не создают фиктивные customer files, checksums или expected results.

## Правила регистрации

1. Сохранить customer/control artifacts в отдельном тестовом контуре, не в production uploads.
2. Зафиксировать source, marketplace, scenario и владельца передачи.
3. Посчитать checksum каждого входного файла командой `sha256sum <file>`.
4. Приложить результаты старой программы как отдельный artifact.
5. Заполнить expected summary и expected row-level results только из customer/old-program artifacts или утверждённого edge-case набора.
6. Зафиксировать allowed/disallowed differences до запуска formal comparison.
7. Не менять WB/Ozon бизнес-логику для подгонки под artifact.

## Реестр

| Set ID | Marketplace | Scenario | Source file(s) | Input checksum(s) | Old program result | Expected summary | Expected row-level results | Allowed differences | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TBD-WB-REAL-001 | WB | real working files | pending customer delivery | pending | pending | pending | pending | pending | blocked_by_artifact_gate |
| TBD-OZ-REAL-001 | Ozon | real working file | pending customer delivery | pending | pending | pending | pending | pending | blocked_by_artifact_gate |
| TBD-WB-EDGE-001 | WB | edge cases by ТЗ | pending tester/customer artifact delivery | pending | not applicable | pending | pending | by ТЗ | blocked_by_artifact_gate for formal acceptance until artifacts are provided |
| TBD-OZ-EDGE-001 | Ozon | edge cases by ТЗ | pending tester/customer artifact delivery | pending | not applicable | pending | pending | by ТЗ | blocked_by_artifact_gate for formal acceptance until artifacts are provided |

## Registration Template

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
Status: blocked_by_artifact_gate / ready / executed / accepted / rejected
Defect/GAP links:
Registered by:
Registered at:
```
