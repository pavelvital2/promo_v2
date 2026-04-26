# TEST_REPORT_STAGE_1_FORMAL_ACCEPTANCE.md

Date: 2026-04-26

Role: Codex CLI executor, formal stage 1 artifact registration and comparison.

## Summary

Formal WB/Ozon real output comparison artifacts were registered and compared against old program results.

Result: PASS.

The stage 1 Excel replacement artifact gate is closed for the registered real WB/Ozon output comparisons:

- `WB-REAL-001`: accepted.
- `OZ-REAL-001`: accepted.

The source Excel artifacts remain local under `test_files/` and are intentionally ignored by git because they may contain commercial data.

## Registered Artifacts

| Set ID | Marketplace | Current platform result | Current checksum | Old program result | Old checksum | Status |
| --- | --- | --- | --- | --- | --- | --- |
| `WB-REAL-001` | WB | `test_files/WB/1_processed.xlsx` | `0c2f5302fe7381c74c1bdf0e1ffae90e756299466648310fb6a383172f5a6420` | `test_files/WB/1_red.xlsx` | `cd7078199dcb5a242d588fa23ed2596dfc8004cb4095fcc786c765acc593683c` | accepted |
| `OZ-REAL-001` | Ozon | `test_files/Ozon/products-1977747_25.04.26_processed.xlsx` | `756fe1f97febb0b1432c2d7caf23c4f1eb3b781ae63b7b5e77f2e5ded39a4ddf` | `test_files/Ozon/products-1977747_25.04.26_red.xlsx` | `df85860f203365d2d6cb42a2befdccd788610e2bac957f5ef164642d2d842846` | accepted |

## Comparison Results

### WB-REAL-001

- Sheet names equal: yes.
- Sheet `Sheet1`: old dimensions `432 x 14`, new dimensions `432 x 14`.
- Total workbook value diffs: `0`.
- Target column `Новая скидка` diffs: `0`.
- Non-target value diffs: `0`.
- Allowed differences: none.
- Result: PASS.

### OZ-REAL-001

- Sheet names equal: yes.
- Sheet `Описание`: old dimensions `11 x 19`, new dimensions `11 x 19`.
- Sheet `Товары и цены`: old dimensions `547 x 56`, new dimensions `547 x 56`.
- Total workbook value diffs: `0`.
- Target K/L diffs: `0`.
- Non-target value diffs: `0`.
- Invalid K values: `0`.
- Invalid L values: `0`.
- Allowed differences: none.
- Result: PASS.

## Commands

```bash
sha256sum \
  test_files/WB/1_red.xlsx \
  test_files/WB/1_processed.xlsx \
  test_files/Ozon/products-1977747_25.04.26_red.xlsx \
  test_files/Ozon/products-1977747_25.04.26_processed.xlsx
```

Workbook comparisons were executed with `openpyxl` using exact cell value comparison across all sheets and cells.

## Remaining Notes

- Automated synthetic coverage for WB/Ozon edge cases remains in the Django test suite.
- Additional customer edge-case artifacts may be registered later, but the real WB/Ozon output comparison gate for replacing the old Excel workflow is accepted for the provided artifacts.
- Production acceptance still depends on deployment mode and operational sign-off; this report covers formal Excel comparison artifacts only.
