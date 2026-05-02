# TASK_PC2_007_IMPLEMENTATION_RECHECK

Date: 2026-05-02
Role: implementation auditor recheck
Task: TASK-PC2-007 Product Core UI Integration
Verdict: PASS

## Documents And Scope Read

- `AGENTS.md`
- `docs/README.md`
- `docs/orchestration/AGENTS.md`
- `docs/roles/READING_PACKAGES.md`
- `docs/reports/TASK_PC2_007_IMPLEMENTATION_AUDIT.md`
- `docs/reports/TASK_PC2_007_DESIGN_HANDOFF.md`
- `docs/reports/TASK_PC2_007_DESIGN_AUDIT.md`
- `docs/stages/stage-3-product-core/core-2/CORE_2_UI_UX_SPEC.md`
- `docs/stages/stage-3-product-core/core-2/CORE_2_MAPPING_RULES_SPEC.md`
- current implementation diff for `apps/web/**` and `templates/web/**`

## Recheck Result

The prior blocker is fixed.

`apps/web/views.py` no longer includes `store_id`, `listing_id`, `operation_id`, or `sync_run_id` in `SAFE_VARIANT_SOURCE_KEYS`. The imported/draft queue now keeps only non-object safe context summary keys in `variant.safe_import_source_items`.

Object-identifying source context is handled separately by `_variant_visible_source_context()`:

- `store_id` is resolved to `StoreAccount` and rendered only when `marketplace_listing.view` is allowed for that store;
- `listing_id` is resolved through `marketplace_listings_visible_to(user)`;
- `operation_id` is resolved and rendered only when `_can_view_operation(user, operation)` passes;
- `sync_run_id` is resolved and rendered as a safe source/status label only when the actor has listing view access to the sync run store.

`templates/web/imported_draft_variant_list.html` renders only:

- whitelisted non-object `key=value` source summary items;
- visible store safe label;
- visible listing link;
- visible operation link;
- visible sync run safe source/status label.

Hidden source store/listing/operation/sync-run identifiers are blank/hidden rather than rendered as raw `key=value`.

## Checklist

| Check | Result | Notes |
| --- | --- | --- |
| Imported/draft queue no longer renders raw `store_id`, `listing_id`, `operation_id`, `sync_run_id` from `import_source_context` without object access. | PASS | Object-id keys are removed from safe summary whitelist and are resolved through access-aware helpers before display. |
| Visible objects show safe label/link; invisible objects are blank/hidden. | PASS | Store/listing/operation/sync-run source context uses explicit visibility checks before rendering labels or links. |
| Regression test covers hidden source IDs. | PASS | `test_imported_draft_queue_hides_inaccessible_source_context_object_ids` asserts raw IDs and hidden labels/links are absent. |
| No new scope creep. | PASS | Current web diff remains within PC2-007 UI/forms/urls/tests/templates; no Product Core model/service/migration changes. |
| Mapping-table / `visual_external` still hidden. | PASS | No active route/view/form/template found for mapping-table upload/preview/apply or `visual_external`; regression test asserts the controls are absent. |

## Verification Commands

| Command | Result |
| --- | --- |
| `POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres POSTGRES_DB=promo_v2 POSTGRES_HOST=127.0.0.1 .venv/bin/python manage.py test apps.web apps.product_core --keepdb` | PASS: `Ran 111 tests in 78.008s`, `OK`. |
| `git diff --check` | PASS, no output. |

## Residual Risks

1. The positive visible-object path is covered by implementation inspection and the broader imported/draft queue test for visible listing output, but the new hidden-ID regression focuses mainly on the denial path.
2. Future changes to `import_source_context` must keep object identifiers out of the safe summary whitelist unless each value is resolved and access-checked before rendering.
3. The broader CORE-2 docs still describe future mapping-table / `visual_external` behavior; for scoped TASK-PC2-007 this remains deferred under the audited handoff boundary.

## Final Decision

PASS.
