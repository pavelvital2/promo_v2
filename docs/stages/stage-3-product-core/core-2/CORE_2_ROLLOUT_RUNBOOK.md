# CORE_2_ROLLOUT_RUNBOOK.md

Статус: исполнительная проектная документация CORE-2, подготовлена для audit-gate.

Трассировка: `docs/tasks/design/product-core/TZ_CORE_2_PRODUCT_CORE_INTEGRATION_FOR_CODEX_DESIGNER.md` §§11.16, §14-§15.

## Назначение

Define operational release steps for future CORE-2 implementation. This runbook is not a command to deploy before audit and implementation are complete.

## Preconditions

- CORE-2 documentation audit result: `AUDIT PASS`.
- Implementation tasks accepted by auditor/tester.
- No blocking GAP for implemented slices.
- Target environment selected and recorded.
- Destructive marketplace writes are not part of CORE-2 sync rollout unless separately approved.

## Backup

Before deployment/migration:

1. Run PostgreSQL backup.
2. Run media/file storage backup if file/export data can be affected.
3. Verify backup artifacts are non-empty.
4. Run restore/readability check according to current release runbook.
5. Record:
   - backup path;
   - timestamp;
   - database name;
   - app commit;
   - migration list before deploy.

## Migration

1. Stop or pause user workflows if migration policy requires it.
2. Run Django system checks.
3. Show pending migrations.
4. Apply migrations.
5. Run data backfill/enrichment only through approved command/task.
6. Record counts and conflict summaries.

Validation commands must include equivalents of:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py showmigrations
python manage.py migrate --noinput
```

Exact command names may differ if implementation adds management commands; release report must list actual commands.

## Smoke Checks

Minimum post-deploy smoke:

- login/permissions baseline;
- Product Core internal products list;
- marketplace listings list/card;
- unmatched/conflict page;
- export download with redaction;
- WB Stage 1 Excel route still accessible;
- Ozon Stage 1 Excel route still accessible;
- WB Stage 2.1 API page still accessible;
- Ozon Stage 2.2 Elastic page still accessible;
- operation card with detail rows;
- audit/techlog list access.

UI-facing implementation should include browser or route/static smoke evidence as required by auditor.

## Data Validation

Post-migration checks:

- `MarketplaceProduct` count unchanged unless separate audited task says otherwise;
- `OperationDetailRow.product_ref` non-null/unchanged for existing rows;
- nullable FK count recorded;
- FK store/marketplace mismatch count is zero;
- listing count by marketplace/store recorded;
- sync run failed/active counts reviewed;
- no secret-like values in snapshots/last_values/audit/techlog sample scan.

## Rollback

Rollback depends on implementation slice:

- code rollback to previous release if migrations are backward compatible;
- clear nullable `marketplace_listing_id` values created by failed backfill if needed;
- do not delete legacy `MarketplaceProduct`;
- do not rewrite old operations;
- restore database/files from backup only after operator decision and impact assessment;
- record rollback commands and evidence.

If migration is non-reversible, implementation must document why and provide compensating backup/restore procedure before release.

## Post-Deploy Checks

- Run targeted CORE-2 tests where feasible in target environment.
- Run Stage 1/2 smoke or regression agreed for release.
- Verify secret redaction guard logs have no violations except expected test probes.
- Verify open GAP blocked features remain disabled/unavailable.
- Verify no future ERP working UI appeared.

## Release Report Requirements

Release report must include:

- commit/branch/environment;
- implementation task list;
- migrations applied;
- backup/restore check evidence;
- validation commands and outputs summary;
- row counts before/after;
- sync/backfill conflict summary;
- tests/regression results;
- known limitations;
- open defects/GAP;
- rollback notes;
- final release verdict.
