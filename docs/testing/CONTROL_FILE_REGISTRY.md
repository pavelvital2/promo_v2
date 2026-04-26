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
| WB-REAL-001 | WB | real working output comparison | `test_files/WB/1_processed.xlsx` | `0c2f5302fe7381c74c1bdf0e1ffae90e756299466648310fb6a383172f5a6420` | `test_files/WB/1_red.xlsx` (`cd7078199dcb5a242d588fa23ed2596dfc8004cb4095fcc786c765acc593683c`) | workbook values equal to old program result | `Новая скидка` values equal, all other workbook values unchanged | none | accepted |
| OZ-REAL-001 | Ozon | real working output comparison | `test_files/Ozon/products-1977747_25.04.26_processed.xlsx` | `756fe1f97febb0b1432c2d7caf23c4f1eb3b781ae63b7b5e77f2e5ded39a4ddf` | `test_files/Ozon/products-1977747_25.04.26_red.xlsx` (`df85860f203365d2d6cb42a2befdccd788610e2bac957f5ef164642d2d842846`) | workbook values equal to old program result | K/L values equal, all other workbook values unchanged; K values valid (`Да` or blank), L values valid (number or blank) | none | accepted |
| TBD-WB-EDGE-001 | WB | edge cases by ТЗ | optional future customer artifact delivery | pending | not applicable | covered by automated tests; optional artifact pending | covered by automated tests; optional artifact pending | by ТЗ | optional_future_artifact |
| TBD-OZ-EDGE-001 | Ozon | edge cases by ТЗ | optional future customer artifact delivery | pending | not applicable | covered by automated tests; optional artifact pending | covered by automated tests; optional artifact pending | by ТЗ | optional_future_artifact |

## Registered Accepted Sets

### WB-REAL-001

Set ID: WB-REAL-001  
Marketplace: WB  
Scenario: real working output comparison  
Source: customer real result from current platform output compared against old program result  
Input/output files:

- Current platform result: `test_files/WB/1_processed.xlsx`
- Old program result: `test_files/WB/1_red.xlsx`

Checksums:

- `test_files/WB/1_processed.xlsx`: `0c2f5302fe7381c74c1bdf0e1ffae90e756299466648310fb6a383172f5a6420`
- `test_files/WB/1_red.xlsx`: `cd7078199dcb5a242d588fa23ed2596dfc8004cb4095fcc786c765acc593683c`

Expected summary: workbook values equal to old program result.  
Expected row-level results: `Новая скидка` values equal.  
Expected output workbook checks: sheet names equal, dimensions `432 x 14`, total value diffs `0`, target column diffs `0`, non-target diffs `0`.  
Allowed differences: none.  
Disallowed differences: any workbook value difference, row/column count difference, or non-target cell value change.  
Related requirements: `ACC-WB-001`, `ACC-WB-006`, `ACC-WB-007`, `ACC-OPS-001`, `ACC-FILE-001`.  
Status: accepted.  
Registered by: Codex CLI with customer-provided artifacts.  
Registered at: 2026-04-26T10:47:01+03:00.

### OZ-REAL-001

Set ID: OZ-REAL-001  
Marketplace: Ozon  
Scenario: real working output comparison  
Source: customer real result from current platform output compared against old program result  
Input/output files:

- Current platform result: `test_files/Ozon/products-1977747_25.04.26_processed.xlsx`
- Old program result: `test_files/Ozon/products-1977747_25.04.26_red.xlsx`

Checksums:

- `test_files/Ozon/products-1977747_25.04.26_processed.xlsx`: `756fe1f97febb0b1432c2d7caf23c4f1eb3b781ae63b7b5e77f2e5ded39a4ddf`
- `test_files/Ozon/products-1977747_25.04.26_red.xlsx`: `df85860f203365d2d6cb42a2befdccd788610e2bac957f5ef164642d2d842846`

Expected summary: workbook values equal to old program result.  
Expected row-level results: K/L values equal.  
Expected output workbook checks: sheet names equal, dimensions `Описание 11 x 19` and `Товары и цены 547 x 56`, total value diffs `0`, K/L diffs `0`, non-target diffs `0`, invalid K values `0`, invalid L values `0`.  
Allowed differences: none.  
Disallowed differences: any workbook value difference, row/column count difference, non-target cell value change, invalid K/L value.  
Related requirements: `ACC-OZ-001`, `ACC-OZ-004`, `ACC-OZ-005`, `ACC-OPS-001`, `ACC-FILE-001`.  
Status: accepted.  
Registered by: Codex CLI with customer-provided artifacts.  
Registered at: 2026-04-26T10:47:01+03:00.

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
