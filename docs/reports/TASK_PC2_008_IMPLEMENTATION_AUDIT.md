# TASK_PC2_008_IMPLEMENTATION_AUDIT

Date: 2026-05-02
Role: implementation auditor
Task: TASK-PC2-008 Permissions, Audit, Techlog, Redaction
Verdict: PASS

## Checked Scope

- `AGENTS.md`
- `docs/README.md`
- `docs/DOCUMENTATION_MAP.md`
- `docs/orchestration/AGENTS.md`
- `docs/roles/READING_PACKAGES.md`
- `docs/reports/TASK_PC2_008_DESIGN_HANDOFF.md`
- `docs/reports/TASK_PC2_008_DESIGN_AUDIT.md`
- `docs/stages/stage-3-product-core/core-2/CORE_2_AGENT_TASKS.md`
- `docs/stages/stage-3-product-core/core-2/CORE_2_READING_PACKAGES.md`
- `docs/stages/stage-3-product-core/core-2/CORE_2_PERMISSIONS_AUDIT_TECHLOG_SPEC.md`
- `docs/product/PERMISSIONS_MATRIX.md`
- `docs/architecture/AUDIT_AND_TECHLOG_SPEC.md`
- `docs/architecture/API_CONNECTIONS_SPEC.md`
- `docs/gaps/GAP_REGISTER.md`
- `docs/adr/ADR_LOG.md`
- current `git status`, `git diff`, migrations and changed tests.

## Audit Result

| Check | Result | Evidence |
| --- | --- | --- |
| No permission seed weakening; new permissions not added silently. | PASS | `apps/identity_access/seeds.py` and identity migrations are unchanged. `apps/identity_access/tests.py` asserts Product Core role defaults, direct deny behavior, and absence of deferred `marketplace_mapping.import_table` / `marketplace_mapping.apply_table`. |
| New audit action codes match handoff/spec and migrations are included. | PASS | `apps/audit/models.py` adds only `product_variant.auto_created_draft`, `operation_detail_row.listing_fk_enriched`, `marketplace_sync.failed`, `marketplace_snapshot.write_failed`. Migration `apps/audit/migrations/0012_alter_auditrecord_action_code.py` is present. |
| New techlog event types match handoff/spec and migrations are included. | PASS | `apps/techlog/models.py` adds `marketplace_sync.api_error`, `marketplace_snapshot.write_error`, `marketplace_mapping.conflict`, `operation_detail_row.enrichment_error`, `product_variant.auto_create_error` with required baseline severities. Migration `apps/techlog/migrations/0011_alter_techlogrecord_event_type.py` is present. |
| Audit/techlog hooks are safe and no secret readback is introduced. | PASS | `create_audit_record()` and `create_techlog_record()` still reject secret-like safe fields. New call sites use safe summaries/failure classes/redacted refs; FK enrichment hashes `product_ref` and does not store raw value. |
| Object access, hidden store denial, and operation row link hiding are preserved. | PASS | Existing object-access services and web tests remain green. Operation row link decoration still filters linked listings through `marketplace_listings_visible_to()` and internal identifiers through Product Core/variant view gates. |
| Deferred mapping-table / `visual_external` workflow is not implemented. | PASS | No permission seed, migration, route, parser, UI workflow or audit action for table preview/apply was added. Existing UI test asserts mapping table controls and `visual_external` are absent. |
| Tests are meaningful and passing. | PASS | Local rerun passed targeted security/regression suites and `apps.discounts`; see commands below. |

## Commands

| Command | Result |
| --- | --- |
| `git diff --check` | PASS, no output. |
| `set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py check` | PASS, `System check identified no issues (0 silenced).` |
| `set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py makemigrations --check --dry-run` | PASS, `No changes detected`. |
| `set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test apps.identity_access apps.audit apps.techlog apps.product_core apps.operations apps.web --verbosity 1 --noinput` | PASS, 173 tests OK. |
| `set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test apps.discounts --verbosity 1 --noinput` | PASS, 103 tests OK. |

Note: an initial parallel test attempt hit a shared PostgreSQL test database creation conflict for `test_promo_v2`; the affected targeted suite was rerun sequentially and passed.

## Residual Risks

1. I did not find a separate TASK-PC2-008 implementation/test closeout report in `docs/` that records the expected `147` and `114` test counts. The audit therefore relies on the local rerun evidence above; actual counts in this workspace are `173` and `103`.
2. `GAP-CORE2-007` remains deferred for the future external mapping table / `visual_external` workflow. Any future implementation of that workflow must reopen permission seed policy, audit actions, techlog events, row/file contract and UI scope through a separate task.
3. New failure hooks intentionally store safe classes/redacted refs instead of raw exception text. This is correct for redaction, but operational diagnosis may require correlating with server logs that also preserve the no-secret rule.

## Blockers

None.

## Final Decision

PASS. TASK-PC2-008 implementation matches the audited handoff and CORE-2 permissions/audit/techlog/redaction scope. No product code changes were made by this audit.
