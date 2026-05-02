# TEST_REPORT_TASK_REL_PC_001_CORE_1_RELEASE_VALIDATION

Date: 2026-05-02
Role: tester
Environment: local project checkout on `42085.koara.live`; staging/production-like status was not independently certified
Branch: `main`
Commit: `f5480f2adc8d42db4dc2d9db5c882533f3553e76`
Database: PostgreSQL `promo_v2` on `127.0.0.1:5432`, Django engine `django.db.backends.postgresql`
Django settings module: `config.settings`
Python version: Python 3.12.3
Postgres version: PostgreSQL 16.13
Validation started at: 2026-05-02T09:37:57+03:00
Validation finished at: 2026-05-02T09:44:17+03:00
Status: PASS WITH NOTES

Production code was not changed. This report is the only intended task artifact.

## 1. Commands

| Command | Result | Notes |
| --- | --- | --- |
| `git branch --show-current` / `git rev-parse HEAD` / `git status --short` | PASS | Branch `main`, commit `f5480f2adc8d42db4dc2d9db5c882533f3553e76`. Existing untracked docs were present before this report and were not modified by this validation. |
| `hostname`, `date -Is`, `.venv/bin/python --version` | PASS | Environment captured. |
| Django settings/database introspection through `.venv/bin/python` | PASS | Settings `config.settings`; DB `promo_v2`; host `127.0.0.1`; port `5432`; secret values were not printed. |
| `pg_dump --version`, `pg_restore --version`, `psql --version` | PASS | PostgreSQL client tools version 16.13. |
| `scripts/backup_postgres.sh` and `scripts/backup_media.sh` with local `BACKUP_DIR` and redacted DB password env | PASS | Created local release-validation backup artifacts. |
| `scripts/restore_check.sh <postgres_dump> <media_tar_gz>` with redacted DB password env | PASS | `restore_check=backup_archives_readable`. |
| `RESTORE_DB=promo_v2_restore_check_202605020939 scripts/restore_check.sh <postgres_dump> <media_tar_gz>` with redacted DB password env | PASS | Restore into separate non-production DB completed. |
| `POSTGRES_USER=postgres POSTGRES_PASSWORD=<set> .venv/bin/python manage.py check` | PASS | `System check identified no issues (0 silenced).` |
| `POSTGRES_USER=postgres POSTGRES_PASSWORD=<set> .venv/bin/python manage.py makemigrations --check --dry-run` | PASS | `No changes detected`. |
| `POSTGRES_USER=postgres POSTGRES_PASSWORD=<set> .venv/bin/python manage.py showmigrations` | PASS | All listed migrations applied, including `product_core.0001`..`0003`, `identity_access.0011`, `audit.0010`, `techlog.0009`. |
| `POSTGRES_USER=postgres POSTGRES_PASSWORD=<set> .venv/bin/python manage.py migrate --noinput --verbosity=2` | PASS | No pending migrations. |
| Repeat `manage.py check` and `makemigrations --check --dry-run` after migrate | PASS | Check passed; no model/migration drift. |
| `POSTGRES_USER=postgres POSTGRES_PASSWORD=<set> .venv/bin/python manage.py shell -c "from apps.marketplace_products.services import validate_legacy_product_listing_backfill; print(validate_legacy_product_listing_backfill())"` | PASS | `{'legacy_products': 1929, 'missing_listing_product_ids': [], 'mismatched_mapping_product_ids': []}`. |
| Runtime count shell for `MarketplaceProduct`, `MarketplaceListing`, unmatched listings, variants | PASS | `legacy_products=1929`, `listings=1929`, `unmatched_without_variant_total=1929`, `with_variant_total=0`. |
| `POSTGRES_USER=postgres POSTGRES_PASSWORD=<set> .venv/bin/python manage.py test apps.product_core apps.marketplace_products apps.identity_access apps.audit apps.techlog apps.operations apps.web apps.discounts.wb_excel apps.discounts.ozon_excel apps.discounts.wb_api.prices apps.discounts.wb_api.promotions apps.discounts.wb_api.upload apps.discounts.ozon_api --verbosity=2` | PASS | 209 tests, OK, 217.537s. |
| Product Core route reverse smoke through `.venv/bin/python manage.py shell` | PASS | Resolved internal product, listing, unmatched, latest-values and mapping-report export routes. |
| `POSTGRES_USER=postgres POSTGRES_PASSWORD=<set> PYTHON_BIN=.venv/bin/python ./scripts/audit_techlog_retention_check.sh` | PASS | `DRY RUN audit_expired=0 techlog_expired=0`. |
| `git diff --check` | PASS | No whitespace errors. |
| Extra ORM count attempt using guessed `legacy_product` relation | COMMAND ERROR | Invalid field name in tester command; corrected with actual model fields. Not a product defect. |
| Extra route reverse attempt using guessed URL names | COMMAND ERROR | Invalid route names in tester command; corrected with `web:*` names. Not a product defect. |
| Initial retention script run without `PYTHON_BIN` | COMMAND ERROR | Local shell had no `python` executable on PATH; corrected with `PYTHON_BIN=.venv/bin/python`. Not a product defect. |

## 2. Backup

| Check | Result | Evidence |
| --- | --- | --- |
| PostgreSQL backup created | PASS | `/home/pavel/projects/promo_v2/tmp/release_validation_backups/postgres/promo_v2_20260502T063817Z.dump`, size 2.7M. |
| Media/files backup created | PASS | `/home/pavel/projects/promo_v2/tmp/release_validation_backups/media/media_20260502T063819Z.tar.gz`, size 9.6M. |
| Backup readability check | PASS | `restore_check=backup_archives_readable`. |
| Restore check in non-production DB | PASS | Restored to `promo_v2_restore_check_202605020939`. |
| Production backup path | NOTE | The validation used local project `tmp/release_validation_backups/*` paths, not `/var/backups/promo_v2/*`, to avoid writing to system production backup locations from this local checkout. |

## 3. Migration And Backfill

| Check | Result | Evidence |
| --- | --- | --- |
| Django system check before migration | PASS | `System check identified no issues (0 silenced).` |
| Model/migration drift before migration | PASS | `No changes detected`. |
| Migration state | PASS | `showmigrations` showed all current migrations applied. |
| Runtime migrate | PASS | `No migrations to apply.` |
| Django system check after migration | PASS | `System check identified no issues (0 silenced).` |
| Model/migration drift after migration | PASS | `No changes detected`. |
| Backfill validation helper | PASS | `legacy_products=1929`; no missing listings; no mismatched mapping rows. |
| Backfilled listing state | PASS | `listings=1929`; `unmatched_without_variant_total=1929`; `with_variant_total=0`. |
| Legacy compatibility | PASS | Regression tests for `MarketplaceProductListingCompatibilityTests` passed; `OperationDetailRow.product_ref` preservation covered. |

## 4. Regression

| Area | Result | Evidence |
| --- | --- | --- |
| Stage 1 WB Excel | PASS | `apps.discounts.wb_excel` tests passed in the 209-test suite; includes check/process behavior, output rules, reason codes, parameter snapshots and file handling. |
| Stage 1 Ozon Excel | PASS | `apps.discounts.ozon_excel` tests passed in the 209-test suite; includes check/process behavior, output rules, permissions and detail rows. |
| Stage 2.1 WB API | PASS | `apps.discounts.wb_api.prices`, `apps.discounts.wb_api.promotions`, `apps.discounts.wb_api.upload` tests passed; includes connection gating, download/export, calculation/upload contracts, drift checks and redaction. |
| Stage 2.2 Ozon Elastic | PASS | `apps.discounts.ozon_api` tests passed; includes actions/product data/review/calculation/upload, drift checks, API client policy, permissions and redaction. |

## 5. UI / Permissions / Exports

| Area | Result | Evidence |
| --- | --- | --- |
| Product Core UI | PASS | `apps.web` tests passed for internal product list/card, create/update/archive flows, product/variant operations and Product Core boundary on Excel pages. |
| MarketplaceListing UI | PASS | `apps.web` tests passed for listing list/card, filters, latest values, raw-safe visibility and unmatched listing views. Route reverse smoke confirmed `/references/marketplace-listings/`, card route pattern and export endpoints. |
| Mapping workflow | PASS | `apps.product_core` and `apps.web` tests passed for manual map/unmap, leave unmatched, needs-review/conflict handling, history and audit creation. |
| Permissions/object access | PASS | `apps.identity_access`, `apps.product_core` and `apps.web` tests passed for owner/admin/manager/observer-style permissions, store scope, direct deny, hidden listing details and mapping permission gates. |
| Exports | PASS | `apps.web` tests passed for internal products export, marketplace listings export, latest-values export, mapping report export and unmatched export with visible-row filtering and secret redaction. Route reverse smoke resolved all release-runbook Product Core CSV export URLs. |
| Manual browser smoke | NOTE | No separate Playwright/browser session or running production web service was available in this validation turn. UI evidence is from Django web tests and static route smoke. |

## 6. Audit / Techlog / Secrets

| Area | Result | Evidence |
| --- | --- | --- |
| Audit | PASS | Product Core mapping/history/audit tests passed; audit immutability and access scope tests passed. Runtime DB has `audit_records=134`. |
| Techlog | PASS | Product Core sync/migration techlog catalog tests passed; general techlog immutability/access/redaction tests passed. Runtime DB has `techlog_records=5`. |
| Retention dry-run | PASS | `audit_techlog_retention_check.sh` with venv Python returned `DRY RUN audit_expired=0 techlog_expired=0`. |
| Secrets | PASS | Redaction tests passed across Product Core, WB API, Ozon API, audit, techlog, operations summaries, snapshots, files/reports and web pages. Real token files were not read. Secret env values were not printed in this report. |

## 7. Defects

| ID | Severity | Description | Blocking | Owner |
| --- | --- | --- | --- | --- |
| - | - | No product defects found during this validation run. | no | - |

## 8. Limitations

- The environment is a local checkout on `42085.koara.live` with PostgreSQL `promo_v2`; it was not independently certified as staging or production-like beyond the available runtime DB and test data.
- Live destructive marketplace operations were not executed. WB/Ozon upload/API write behavior was validated by automated tests with mocked clients, permission gates and drift checks.
- Manual browser/Playwright validation was not performed in this turn; Product Core UI, permissions and exports were validated by Django web tests and route/static smoke.
- The runbook `pre_update_backup.sh` was not invoked as a single wrapper because its child scripts share one `BACKUP_DIR` variable while this validation kept PostgreSQL and media backups in separate local directories. The same underlying scripts, `backup_postgres.sh`, `backup_media.sh` and `restore_check.sh`, were executed.
- A temporary restore-check database `promo_v2_restore_check_202605020939` was created for validation evidence.

## 9. Tester Verdict

CORE-1 RELEASE VALIDATION: PASS WITH NOTES.

All mandatory automated gates that were safe in this environment passed: backup and restore check, Django checks, migrations, backfill validation, Stage 1/2 regression suites, Product Core UI/web tests, permissions, exports, audit/techlog and secret-redaction coverage. No blocking defects were found.
