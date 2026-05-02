# TASK_PC2_007_IMPLEMENTATION_AUDIT

Date: 2026-05-02
Role: implementation auditor
Task: TASK-PC2-007 Product Core UI Integration
Verdict: BLOCKED

## Documents Read

- `AGENTS.md`
- `docs/README.md`
- `docs/orchestration/AGENTS.md`
- `docs/reports/TASK_PC2_007_DESIGN_HANDOFF.md`
- `docs/reports/TASK_PC2_007_DESIGN_AUDIT.md`
- `docs/stages/stage-3-product-core/core-2/CORE_2_UI_UX_SPEC.md`
- `docs/stages/stage-3-product-core/core-2/CORE_2_MAPPING_RULES_SPEC.md`
- current `git status --short`
- current `git diff --stat`
- current implementation diff for `apps/web/**` and `templates/web/**`

## Diff Scope Reviewed

Implementation diff is limited to the expected PC2-007 UI surface:

- `apps/web/forms.py`
- `apps/web/tests.py`
- `apps/web/urls.py`
- `apps/web/views.py`
- `templates/web/imported_draft_variant_list.html`
- `templates/web/marketplace_listing_card.html`
- `templates/web/marketplace_listing_list.html`
- `templates/web/operation_card.html`
- `templates/web/product_card.html`
- `templates/web/product_list.html`
- `templates/web/reference_index.html`
- `templates/web/variant_form.html`
- existing handoff/audit report files added in the same worktree

The new required template `templates/web/imported_draft_variant_list.html` is present in the diff.

## Blocking Finding

### BLOCKER-1: imported/draft queue can leak hidden store/listing/operation identifiers through `import_source_context`

`TASK_PC2_007_DESIGN_HANDOFF.md` requires that hidden store/listing data must not leak through imported source context, and that source marketplace/store/listing and source sync run/operation details are shown only when visible.

The implementation correctly filters visible listing links in `_attach_variant_review_context()`, but then independently renders a whitelisted subset of `ProductVariant.import_source_context` for every visible variant review row:

- `apps/web/views.py:2578` includes `sync_run_id`, `operation_id`, `listing_id`, `marketplace`, and `store_id` in `SAFE_VARIANT_SOURCE_KEYS`.
- `apps/web/views.py:2594` to `apps/web/views.py:2604` emits those values without checking whether the user can view the referenced store, listing, sync operation, or operation.
- `apps/web/views.py:2628` to `apps/web/views.py:2630` attaches these items to every row in the imported/draft queue.
- `templates/web/imported_draft_variant_list.html:36` to `templates/web/imported_draft_variant_list.html:39` renders them as `key=value`.

This means a user with `product_core.view + product_variant.view`, but without access to the source store/listing/operation, can still see raw source identifiers such as `store_id`, `listing_id`, `operation_id`, or `sync_run_id` if they are present in `import_source_context`. That violates the PC2-007 access boundary even though visible listing links themselves are filtered.

Required fix: either remove object-identifying source keys from rendered `import_source_context`, or render them only after resolving the referenced object and proving the same object access that would allow the corresponding link/detail. Safe non-object summary fields may remain if they cannot reveal hidden store/listing/operation data.

## Checklist

| Check | Result | Notes |
| --- | --- | --- |
| UI scope matches narrowed PC2-007 and no guessed broad workflow. | PASS | Diff stays in `apps/web` UI/forms/urls/tests and templates; no Product Core services/models/migrations changed. |
| No active mapping-table upload/preview/apply and no `visual_external` UI. | PASS | No new route/template/service for mapping-table workflow; explicit regression test added. Existing manual exact mapping page remains unchanged. |
| No future ERP/production/demand/suppliers/labels/card-field write UI. | PASS | No active future ERP UI or marketplace card-field edit surface introduced in this diff. |
| Linked internal identifiers gated by `product_core.view + product_variant.view`. | PASS | Listing list/card and operation row internal variant display use the combined gate. |
| Imported/draft queue labels `review_state` separately and actions are permission-gated/audited. | BLOCKED | Labels/actions/audit are present, but source context leaks hidden object identifiers as described in BLOCKER-1. |
| Operation row links are read-only, raw `product_ref` unchanged, no FK writes/candidate computation. | PASS | Operation card only attaches display attributes for existing FK links and preserves `product_ref`. |
| Latest/snapshot/export controls permission-gated and no secret/raw payload rendering. | PASS | Snapshot UI is permission-gated; latest export is snapshot-view filtered; raw-safe snapshot details remain technical-view gated. |
| New template included in diff/commit set. | PASS | `templates/web/imported_draft_variant_list.html` is added. |
| Tests meaningful and reported PASS. | PASS | `apps.web apps.product_core` ran 110 tests OK; `check` and `diff-check` passed. |

## Verification Commands

| Command | Result |
| --- | --- |
| `git diff --check` | PASS, no output. |
| `python manage.py check` | Environment command unavailable: `/bin/bash: line 1: python: command not found`. Retried with project venv. |
| `set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py check` | PASS: `System check identified no issues (0 silenced).` |
| `set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py makemigrations --check --dry-run` | PASS: `No changes detected`. |
| `set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test apps.web apps.product_core --verbosity 1 --noinput --keepdb` | PASS: `Ran 110 tests in 82.804s`, `OK`. |

## Final Decision

BLOCKED.

The implementation is close and the test/check baseline is green, but PC2-007 cannot pass while the imported/draft review queue can render source-context object identifiers for stores/listings/operations that the actor may not be allowed to see.
