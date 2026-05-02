# CORE_2_PERMISSIONS_AUDIT_TECHLOG_SPEC.md

Статус: исполнительная проектная документация CORE-2, подготовлена для audit-gate.

Трассировка: `docs/tasks/design/product-core/TZ_CORE_2_PRODUCT_CORE_INTEGRATION_FOR_CODEX_DESIGNER.md` §§7.8, 7.9, §11.11.

## Назначение

Define permissions, object access, audit, techlog and redaction rules for CORE-2.

## Permissions

CORE-2 reuses Stage 3.0 Product Core permissions where possible.

| Action | Permission | Scope |
| --- | --- | --- |
| View listings | `marketplace_listing.view` | store |
| Run approved listing/snapshot sync | `marketplace_listing.sync` | store |
| Export listings/mapping reports | `marketplace_listing.export` | store |
| Map listing to variant | `marketplace_listing.map` + Product Core/variant view/create/update as needed | store + product core |
| Unmap listing | `marketplace_listing.unmap` | store + product core |
| View snapshots/latest values | `marketplace_snapshot.view` | store |
| View technical raw-safe snapshot details | `marketplace_snapshot.technical_view` + technical permission | store + technical |
| View internal products/variants | `product_core.view`, `product_variant.view` | global with store-filtered linked data |
| Export internal products/variants | `product_core.export` | global with store-filtered linked data |

If `GAP-CORE2-001` approves auto-created imported/draft variants, implementation must add or reuse explicit permission for reviewing/confirming imported variants. This cannot be hidden behind generic view permission.

## Object Access

- `MarketplaceListing` and snapshots inherit access from `StoreAccount`.
- User without store access cannot see the listing, snapshots, related operation links or files.
- Internal product lists may be global, but linked listing details/counts are filtered to visible stores.
- Mapping requires both listing store access and Product Core permission.
- Operation row link visibility requires access to the operation and linked listing.

## Audit Actions

CORE-2 minimum audit catalog:

| Action code | When |
| --- | --- |
| `marketplace_listing.synced` | listing created/updated by approved sync/import/migration |
| `product_variant.auto_created_draft` | draft/imported variant auto-created after `GAP-CORE2-001` approval |
| `marketplace_listing.mapped` | listing linked to variant |
| `marketplace_listing.unmapped` | listing unlinked from variant |
| `marketplace_listing.mapping_conflict_marked` | conflict detected/marked |
| `marketplace_listing.mapping_review_marked` | needs_review detected/marked |
| `operation_detail_row.listing_fk_enriched` | nullable FK written by new row service or backfill |
| `product_core.export_generated` | product/listing/mapping/latest export generated |
| `marketplace_sync.failed` | sync failed with safe summary |
| `marketplace_snapshot.write_failed` | snapshot write failed |

Audit snapshots must contain only safe identifiers, counts, statuses and redacted context.

## Techlog Events

CORE-2 minimum techlog catalog:

| Event type | Severity baseline | When |
| --- | --- | --- |
| `marketplace_sync.api_error` | error | external API failure not covered by marketplace-specific event |
| `marketplace_sync.rate_limited` | warning | rate limit or retry exhaustion |
| `marketplace_sync.response_invalid` | error | schema/JSON/semantic validation failure |
| `marketplace_snapshot.write_error` | error | snapshot persistence failure |
| `marketplace_mapping.conflict` | warning | automatic exact candidate conflict detected |
| `operation_detail_row.enrichment_error` | warning/error | FK enrichment failed or conflict occurred |
| `product_variant.auto_create_error` | error | approved auto-create failed safely |
| `marketplace_sync.secret_redaction_violation` | critical | secret-like value detected in safe contour |

Sensitive details, even when gated, must not contain token, API key, Client-Id, authorization header, bearer value or secret-like payload.

## Redaction

Redaction applies to:

- sync run summaries and error summaries;
- snapshots and `last_values`;
- operation summaries/details/final values;
- audit before/after snapshots;
- techlog safe messages and sensitive refs;
- UI;
- exports/files;
- test output and reports.

Allowed safe fields:

- endpoint code/family;
- HTTP status;
- row counts;
- checksums;
- product/listing ids;
- marketplace action ids when not secret;
- redacted payload fragments.

## Security Tests

Future implementation must test:

- permission denial for sync/map/export/snapshot;
- object access filtering for listing links and counts;
- hidden store listing not exported;
- operation row FK hidden if listing not visible;
- imported/draft review permission if implemented;
- redaction across UI/export/audit/techlog/snapshots;
- secret-like payload rejection in JSON fields;
- no secret values in test reports.
