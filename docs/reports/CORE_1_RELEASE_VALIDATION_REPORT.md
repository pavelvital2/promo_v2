# CORE_1_RELEASE_VALIDATION_REPORT

Date: 2026-05-02
Environment: local project checkout on `42085.koara.live`; PostgreSQL `promo_v2` on `127.0.0.1:5432`; staging/production-like status not independently certified
Branch: `main`
Commit: `f5480f2adc8d42db4dc2d9db5c882533f3553e76`
Tester report: `docs/testing/TEST_REPORT_TASK_REL_PC_001_CORE_1_RELEASE_VALIDATION.md`
Audit report: `docs/audit/AUDIT_REPORT_TASK_REL_PC_001_CORE_1_RELEASE_VALIDATION.md`

## Final Status

PASS WITH NOTES

## Summary

TASK-REL-PC-001 confirmed CORE-1 Product Core Foundation as an accepted stable foundation for the next design stage. The tester reported `CORE-1 RELEASE VALIDATION: PASS WITH NOTES`, and the auditor accepted the result as `AUDIT PASS WITH NOTES`.

No blocking defects were found. Product code, tests and migrations were not changed by this finalization.

## Validation Matrix

| Area | Status | Evidence |
| --- | --- | --- |
| Backup | PASS WITH NOTES | Local PostgreSQL and media backup artifacts were created under `tmp/release_validation_backups/*`; restore readability and non-production DB restore check passed. The single `scripts/pre_update_backup.sh` wrapper was not run as one command in this local validation. |
| Migrations | PASS | `manage.py check`, `makemigrations --check --dry-run`, `showmigrations` and `migrate --noinput` passed; no pending migrations or model drift. |
| Backfill | PASS | `validate_legacy_product_listing_backfill()` returned `legacy_products=1929`, no missing listings and no mismatched mappings; runtime counts showed `MarketplaceProduct=1929` and `MarketplaceListing=1929`. |
| Stage 1 Regression | PASS | WB Excel and Ozon Excel regression groups passed in the 209-test targeted release suite. |
| Stage 2.1 Regression | PASS | WB API prices, promotions and upload regression groups passed in the 209-test targeted release suite. |
| Stage 2.2 Regression | PASS | Ozon Elastic API regression group passed in the 209-test targeted release suite. |
| Product Core UI | PASS WITH NOTES | Django web tests and route/static smoke covered Product Core UI routes; no separate manual Playwright/browser smoke was performed. |
| Listing UI | PASS WITH NOTES | Django web tests and route/static smoke covered listing, unmatched and export routes; no separate manual Playwright/browser smoke was performed. |
| Mapping | PASS | Product Core and web tests covered manual map/unmap, leave unmatched, needs-review/conflict handling, history and audit creation. |
| Permissions | PASS | Identity access, Product Core and web tests covered store scope, direct deny, role behavior and mapping permission gates. |
| Exports | PASS | Web tests covered internal products, listings, latest values, mapping report and unmatched exports with visible-row filtering and redaction. |
| Audit/Techlog | PASS | Audit/history and techlog tests passed; dry-run retention check returned `audit_expired=0 techlog_expired=0`. |
| Secrets | PASS | Redaction tests passed across UI, logs, audit, techlog, reports, exports and API flows; real token files were not read and secret values were not printed. |

## Open Defects

None.

## Non-blocking Notes

- Validation ran in a local checkout on `42085.koara.live`; the environment was not independently certified as staging or production-like.
- Live destructive WB/Ozon uploads were not executed. Upload behavior was validated by automated tests with mocked clients, permission gates and drift checks.
- Manual Playwright/browser smoke was not performed. UI evidence is from Django web tests and route/static smoke.
- `scripts/pre_update_backup.sh` was not invoked as a single wrapper command because the local validation used separate backup directories; the underlying `backup_postgres.sh`, `backup_media.sh` and `restore_check.sh` scripts were executed and verified.

## Decision

CORE-1 accepted as stable foundation: yes

CORE-2 design allowed: yes

## Next Authorized Step

`docs/tasks/design/product-core/TZ_CORE_2_PRODUCT_CORE_INTEGRATION_FOR_CODEX_DESIGNER.md`

This is only the next authorized input document for CORE-2 design. CORE-2 implementation remains prohibited until its design documentation passes the required audit gate.
