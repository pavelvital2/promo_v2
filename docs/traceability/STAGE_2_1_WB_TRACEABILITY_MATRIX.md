# STAGE_2_1_WB_TRACEABILITY_MATRIX.md

Трассировка: `tz_stage_2.1.txt` §2-§18.

| Requirement | Документ | Tests/Acceptance | ADR/GAP |
| --- | --- | --- | --- |
| Stage 2 split 2.1 WB / 2.2 Ozon | `docs/stages/stage-2/STAGE_2_SCOPE.md` | General checklist | ADR-0016 |
| Excel Stage 1 remains штатный/резервный | `STAGE_2_SCOPE.md`, `WB_DISCOUNTS_API_SPEC.md` | Stage 1 regression | ADR-0016 |
| 2.1.1 download prices/read-only | `WB_API_PRICE_EXPORT_SPEC.md` | 2.1.1 checklist | ADR-0017 |
| `GET /api/v2/list/goods/filter` pagination/rate | `WB_API_PRICE_EXPORT_SPEC.md` | Prices API mocks | ADR-0017 |
| Price Excel required columns | `WB_API_PRICE_EXPORT_SPEC.md`, `FILE_CONTOUR.md` | File generation tests | ADR-0017 |
| Product directory update | `WB_API_PRICE_EXPORT_SPEC.md`, `DATA_MODEL.md` | DB integration tests | ADR-0017 |
| Size price conflict blocks upload | `WB_API_PRICE_EXPORT_SPEC.md`, `WB_DISCOUNTS_API_SPEC.md` | Size conflict tests | ADR-0020 |
| 2.1.2 current promotions definition | `WB_API_PROMOTIONS_EXPORT_SPEC.md` | Current filter tests | ADR-0018 |
| Promotions details/nomenclatures | `WB_API_PROMOTIONS_EXPORT_SPEC.md` | Promotions API mocks | ADR-0018 |
| Auto promotions without nomenclatures | `WB_API_PROMOTIONS_EXPORT_SPEC.md`, `UI_SPEC.md` | Auto promo tests | ADR-0018 |
| Promo Excel files | `WB_API_PROMOTIONS_EXPORT_SPEC.md`, `FILE_CONTOUR.md` | File generation tests | ADR-0017 |
| 2.1.3 same WB logic as Stage 1 | `WB_DISCOUNTS_API_SPEC.md`, `WB_DISCOUNTS_EXCEL_SPEC.md` | Golden comparison | ADR-0017 |
| Result Excel manual upload file | `WB_DISCOUNTS_API_SPEC.md`, `FILE_CONTOUR.md` | Result Excel tests | ADR-0017 |
| Explicit upload confirmation | `WB_DISCOUNTS_API_SPEC.md`, `UI_SPEC.md` | Upload UI tests | ADR-0019 |
| Pre-upload drift check | `WB_DISCOUNTS_API_SPEC.md` | Drift tests | ADR-0019 |
| Price drift blocks upload | `WB_DISCOUNTS_API_SPEC.md` | Drift tests | ADR-0019 |
| Batch upload <=1000/uploadID per batch | `WB_DISCOUNTS_API_SPEC.md`, `DATA_MODEL.md` | Upload mocks | ADR-0019 |
| Status polling, not HTTP 200 | `WB_DISCOUNTS_API_SPEC.md` | Status tests | ADR-0019 |
| Partial errors -> warnings | `WB_DISCOUNTS_API_SPEC.md`, `UI_SPEC.md` | Status 5 tests | ADR-0019 |
| Quarantine shown separately | `WB_DISCOUNTS_API_SPEC.md`, `UI_SPEC.md` | Quarantine tests | ADR-0019 |
| API secrets protected | `API_CONNECTIONS_SPEC.md`, `AUDIT_AND_TECHLOG_SPEC.md` | Secret redaction tests | ADR-0019 |
| Stage 2.1 reason/result codes | `WB_DISCOUNTS_API_SPEC.md`, `DATA_MODEL.md` | Code catalog tests | ADR-0020 |
| WB API UI master | `UI_SPEC.md` | UI acceptance | ADR-0017 |
| WB API permissions | `PERMISSIONS_MATRIX.md` | Rights tests | ADR-0019 |
| Implementation task-scoped docs | `docs/tasks/implementation/stage-2/*` | Audit of task files | none |

## GAP status

No open Stage 2.1 GAP as of 2026-04-26. Evaluated candidates are documented in `docs/gaps/GAP_REGISTER.md` and ADR-0017..ADR-0020.
