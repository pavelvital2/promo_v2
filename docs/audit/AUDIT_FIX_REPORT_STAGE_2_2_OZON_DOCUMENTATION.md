# AUDIT_FIX_REPORT_STAGE_2_2_OZON_DOCUMENTATION.md

Дата: 2026-04-30  
Автор: Stage 2.2 Ozon API designer  
Scope: documentation-only fix after Stage 2.2 documentation audit FAIL.

## Summary

Исправлены 7 blocking issues аудита Stage 2.2 documentation package. Код приложения не менялся; тесты приложения не запускались.

## Fixed audit blockers

1. UX/functionality decisions:
   - Customer decision 2026-04-30 recorded in ADR-0026: active/candidate_and_active + not_upload_ready rows must be removed from action.
   - Customer decision 2026-04-30 recorded in ADR-0027: review is calculation result state, not a separate Operation; `GAP-0020` resolved.
   - Customer decision 2026-04-30 recorded in ADR-0028: candidate/active collision rows merge as `candidate_and_active`, are treated as active for write planning, and remain visible in details/reports; `GAP-0021` resolved.

2. Upload/deactivate preconditions:
   - Removed normal final scenario `deactivate declined -> add/update proceeds`.
   - Upload target result now requires deactivate group confirmation when `deactivate_from_action` rows exist.
   - If group confirmation is absent, upload is blocked/pending; no Ozon write operation is created.

3. Codes:
   - Removed `not_uploaded_user_declined` from the target model.
   - Added/standardized `ozon_api_upload_blocked_deactivate_unconfirmed`, `review_pending_deactivate_confirmation`, `ozon_api_deactivate_group_confirmed`.
   - Added closed catalogs for planned actions, review/display states, deactivate confirmation statuses and allowed deactivate reasons.

4. `GAP-0018`:
   - Expanded from write-only activate/deactivate payload to read-side `/v1/actions/products` and `/v1/actions/candidates` schemas plus write payloads.
   - Updated task dependencies for TASK-021 and implementation index.

5. Ozon connection check endpoint:
   - Added `GAP-0022`.
   - Narrowed TASK-019 to secret-safe scaffolding and mocked check until production endpoint/semantics are approved.

6. `UI_SPEC` operation classification:
   - Updated operation list/card rules to cover Stage 2.1 WB API and Stage 2.2 Ozon API by `step_code`.
   - Stage 2.2 operation cards must show `marketplace=ozon`, `mode=api`, `module=actions`.

7. Reading packages/tasks:
   - Aligned TASK-019..TASK-026 input documents with the Ozon API Stage 2.2 reading package.
   - Added sequential ownership gates to TASK-026: UI implementation -> acceptance/testing -> audit/release handoff.

## Remaining customer GAPs

- `GAP-0014`: stable Elastic Boosting action identification.
- `GAP-0015`: confirm J source as product `min_price`.
- `GAP-0016`: Ozon stock R aggregation rule.
- `GAP-0017`: official manual upload Excel template.
- `GAP-0018`: exact read-side action schemas and activate/deactivate payload.
- `GAP-0019`: batch size, rate limits, retry/idempotency policy.
- `GAP-0022`: approved Ozon API connection check endpoint and semantics.

## Self-check

Used `rg` and `git diff` for documentation self-check. Application tests were intentionally not run.
