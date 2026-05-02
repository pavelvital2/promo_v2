# TEST_REPORT_TASK_PC_009_STAGE_3_ACCEPTANCE

Date: 2026-05-02
Role: Stage 3 / TASK-PC-009 tester
Verdict: PASS

Production code was not changed. Only this test report was created.

## Input Evidence

- Documentation audit gate: `docs/audit/AUDIT_REPORT_STAGE_3_PRODUCT_CORE_DOCUMENTATION.md` is `AUDIT PASS`.
- Implementation audit reports TASK-PC-001..008: all present and `AUDIT PASS` / pass with closed re-audit notes.
- Open Product Core spec-blocking GAP: none found in checked Stage 3 scope; `GAP-0023` is resolved/customer_decision.

## Commands

| Command | Result |
| --- | --- |
| `POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres .venv/bin/python manage.py check` | PASS: `System check identified no issues (0 silenced).` |
| `POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres .venv/bin/python manage.py makemigrations --check --dry-run` | PASS: `No changes detected`. |
| `git diff --check` | PASS. |
| `POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres .venv/bin/python manage.py test apps.product_core apps.marketplace_products apps.identity_access apps.audit apps.techlog apps.operations apps.web apps.discounts.wb_excel apps.discounts.ozon_excel apps.discounts.wb_api.prices apps.discounts.wb_api.promotions apps.discounts.wb_api.upload apps.discounts.ozon_api --verbosity=2` | PASS: 209 tests, OK, 206.643s. |
| `POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres .venv/bin/python manage.py migrate --verbosity=2` | PASS: applied pending local runtime DB migrations through `product_core.0003`, `identity_access.0011`, `audit.0010`, `techlog.0009`. |
| `POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres .venv/bin/python manage.py shell -c "from apps.marketplace_products.services import validate_legacy_product_listing_backfill; print(validate_legacy_product_listing_backfill())"` | PASS after migrate: `{'legacy_products': 1929, 'missing_listing_product_ids': [], 'mismatched_mapping_product_ids': []}`. |
| Focused migration/access/secret run for `MarketplaceProductListingCompatibilityTests`, `ProductCoreSyncFoundationTests`, Product Core secret contour, listing access and export access tests | PASS: 10 tests, OK, 8.335s. |

Note: before `migrate`, the local runtime DB had pending Stage 3 migrations and the validation helper failed because `product_core_marketplacelisting` did not exist. This was an environment migration state, not a test DB failure. Applying migrations resolved it.

## Protocol Results

| Test ID | Scenario | Expected | Actual | Status | Defect/GAP | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| PC-DM-001 | Create product, variant, category, identifier with fixed dictionaries | Product Core entities and fixed choices work | Covered by `apps.product_core` model tests | pass | - | Includes identifier/category constraints. |
| PC-DM-002 | Listing uniqueness and store/marketplace constraints | Listing external identity is unique per marketplace/store | Covered by `test_listing_external_identity_is_unique_per_marketplace_and_store` | pass | - | Constraint enforced in test DB. |
| PC-DM-003 | Mapping/listing statuses reject unsupported values | Unsupported matched state without variant is rejected | Covered by listing validation tests | pass | - | Fixed status choices covered. |
| PC-MIG-001 | Backfill all legacy products into listings with `internal_variant_id=null` | No missing listings, no variant auto-created | Runtime validation: 1929 legacy products, no missing or mismatched mappings | pass | - | Local DB was migrated during validation. |
| PC-MIG-002 | Legacy operations remain visible by `product_ref` | `OperationDetailRow.product_ref` remains raw and compatible | Covered by marketplace compatibility tests | pass | - | Stage 1/2 regression suite also passed. |
| PC-MIG-003 | Rollback leaves legacy `MarketplaceProduct` intact | Legacy data is not deleted/truncated | Migration reverse is noop per audit; tests verify compatibility | pass | - | No destructive migration found in test evidence. |
| PC-PERM-001 | User without store access cannot see listing/snapshot | Hidden store listing/snapshot blocked | Covered by Product Core and web access tests | pass | - | Listing list/card access tests passed. |
| PC-PERM-002 | Internal product list does not leak hidden store listing details | Counts/details are store-filtered | Covered by internal product list/card and export tests | pass | - | Hidden listing details excluded. |
| PC-UI-001 | Internal product list/card required columns and filters | Product UI usable with permissions and future hooks disabled/planned | `apps.web` Product Core UI tests passed | pass | - | Create/update/archive flows covered. |
| PC-UI-002 | Listing list/card required columns and filters | Listing UI usable with snapshots/history/related records | `apps.web` listing UI tests passed | pass | - | Raw-safe technical view is separately gated. |
| PC-MAP-001 | Manual map creates audit and mapping history | Mapping writes audit/history | Mapping workflow tests passed | pass | - | Permission checks included. |
| PC-MAP-002 | Manual unmap preserves old mapping in history | Unmap writes audit/history and preserves previous state | Mapping workflow and leave-unmatched tests passed | pass | - | Includes already-unmatched case from re-audit. |
| PC-MAP-003 | Candidate suggestion cannot create confirmed mapping automatically | Suggestions remain non-authoritative | Product Core and web mapping tests passed | pass | - | No auto-confirmed candidate mapping. |
| PC-MAP-004 | Candidate suggestions are exact only | Only exact seller article/barcode/external id candidates | Product Core candidate tests passed | pass | - | Fuzzy/title matching not confirmed. |
| PC-MAP-005 | Multiple/conflicting candidates stay review/conflict | No confirmed link until user resolution | Product Core candidate status tests passed | pass | - | `needs_review` / `conflict` covered. |
| PC-SYNC-001 | Successful sync stores snapshots and updates listing cache | Snapshot rows linked to run/listing/operation; cache updated | Product Core sync tests passed | pass | - | Includes duplicate active run guard. |
| PC-SYNC-002 | Failed sync records techlog and preserves last successful values | Failed sync does not erase last cache | Product Core sync tests passed | pass | - | Safe techlog path covered. |
| PC-XLS-001 | Stage 1 Excel upload does not create internal products | Excel remains operational boundary | Web Excel boundary and WB/Ozon Excel tests passed | pass | - | Existing Excel upload/process unchanged. |
| PC-EXP-001 | Mapping report export respects object access | Exports hide inaccessible store/listing data | Product Core export tests passed | pass | - | Latest-values redaction covered. |
| PC-SEC-001 | Secret redaction across unsafe surfaces | No token/key/Client-Id/auth values in UI/logs/audit/techlog/snapshots/files/reports | Product Core, WB API, Ozon API, audit, techlog and web redaction tests passed | pass | - | Static scan confirmed redaction helpers on checked paths. |
| PC-REG-001 | Stage 1 WB/Ozon regression | WB/Ozon Excel accepted tests still pass | `apps.discounts.wb_excel` and `apps.discounts.ozon_excel` passed in suite | pass | - | Stage 1 regression included. |
| PC-REG-002 | Stage 2.1 WB API regression | WB prices/promotions/upload contracts pass | `apps.discounts.wb_api.prices/promotions/upload` passed in suite | pass | - | Calculation dependency not in orchestrator minimum, but WB API listed groups passed. |
| PC-REG-003 | Stage 2.2 Ozon Elastic regression | Ozon Elastic contracts pass | `apps.discounts.ozon_api` passed in suite | pass | - | Includes client, actions, product data, calculation, review/upload. |

## Acceptance Checklist Summary

| Area | Status | Evidence |
| --- | --- | --- |
| Documentation gate | pass | Documentation audit PASS; TASK-PC-001..008 audit reports PASS; no open Stage 3 spec-blocking GAP found. |
| Data model | pass | Product Core model tests passed; migrations applied and no model diff. |
| Migration | pass | Runtime migration applied; validation returned no missing listings and no mismatched mappings. |
| Mapping | pass | Manual map/unmap, exact candidates, review/conflict and no auto-confirm tests passed. |
| UI | pass | Internal product and listing list/card/access tests passed. |
| Permissions | pass | Object access, Product Core rights, mapping permissions and role seed tests passed. |
| Operations, audit, techlog | pass | Operations immutability, Product Core audit/history, techlog and safe message tests passed. |
| Excel and regression | pass | Stage 1 WB/Ozon Excel and Stage 2.1/2.2 API regression groups passed. |
| Secret safety | pass | Redaction tests across Product Core, WB API, Ozon API, audit, techlog, files/reports and UI passed. |

## Defects, GAPs, Blockers

No open defects or GAPs were created by this TASK-PC-009 run.

Operational note: the local runtime database initially had pending Stage 3 migrations. This was resolved by running `manage.py migrate`; post-migration validation passed. Release/deployment should include the same migration application step before runtime acceptance.

## Final Status

PASS. Stage 3 Product Core acceptance tests and orchestrator-approved regression suite passed with no remaining test blockers.
