# STAGE_2_1_WB_ACCEPTANCE_CHECKLISTS.md

Трассировка: `docs/source/stage-inputs/tz_stage_2.1.txt` §15.

## Общий чек-лист

- [ ] Documentation audit passed before implementation.
- [ ] WB Excel Stage 1 remains available and tests pass.
- [ ] Ozon API Stage 2.2 not touched.
- [ ] WB API token stored only via `protected_secret_ref`.
- [ ] No token/header/API key/bearer/secret-like values in metadata, audit, techlog `safe_message`, techlog `sensitive_details_ref`, snapshots, UI, Excel, files, reports or test output.
- [ ] Object access works for stores, operations, files, products, promotions and connection.
- [ ] Stage 2.1 operations have mandatory `step_code`; `Operation.type=check/process` remains only for check/process scenarios and is not used for WB API steps.

## 2.1.1 Prices

- [ ] User with rights can download prices.
- [ ] User without `wb.api.prices.download` cannot download prices.
- [ ] `GET /api/v2/list/goods/filter` pagination continues to empty list.
- [ ] Rate limit policy is applied.
- [ ] Price Excel has required columns.
- [ ] Products are created/updated for selected store.
- [ ] Product history is created.
- [ ] Size conflict is visible and not upload-ready.
- [ ] Operation/audit/techlog are created as applicable.

## 2.1.2 Current Promotions

- [ ] Current filter is `startDateTime <= now_utc < endDateTime`.
- [ ] `now_utc`, API window and `allPromo=true` are stored.
- [ ] Details are requested in batches <=100 IDs.
- [ ] Regular promotion nomenclatures are fetched with pagination.
- [ ] Auto promotions are saved without invented products.
- [ ] Promo Excel files have required columns.
- [ ] Separate file per regular current promotion is downloadable.

## 2.1.3 Calculation

- [ ] Calculation reuses Stage 1 WB logic/core.
- [ ] Decimal + ceil is used; float is not used.
- [ ] Threshold/fallback order matches Stage 1.
- [ ] Result Excel writes only `Новая скидка`.
- [ ] Basis and parameter snapshot are visible.
- [ ] Errors block upload.
- [ ] Recalculation creates new operation/file version.

## 2.1.4 Upload

- [ ] Upload requires rights, object access, active connection and successful calculation.
- [ ] Explicit confirmation is required.
- [ ] Pre-upload drift check runs before POST upload.
- [ ] Price drift blocks upload.
- [ ] Batch size is <=1000.
- [ ] Normal upload payload contains `nmID` + `discount` only and does not contain stale `price`.
- [ ] WB rejection of discount-only payload stops upload safely and does not retry with old price.
- [ ] Implementation does not silently add price from calculation Excel or old price snapshot.
- [ ] `uploadID` is stored per batch.
- [ ] Status polling determines final result.
- [ ] WB status 3/4/5/6 mapping is correct.
- [ ] Partial errors are shown and mapped to `completed_with_warnings`.
- [ ] Quarantine errors are shown separately.
- [ ] 208 already exists is handled without blind resend.
- [ ] 429/rate limit is handled through backoff/safe failure.

## Release readiness

- [ ] TASK-011..TASK-017 reports are complete.
- [ ] Traceability matrix rows are covered.
- [ ] Stage 2.1 audit report has no blocking findings.
- [ ] Backup/restore policy from Stage 1 is still valid for new DB/file entities.
