# TEST_REPORT_TASK_013_RECHECK

Task: `TASK-013 Stage 2.1 WB API current promotions download`
Recheck target: `DEF-TASK-013-001`
Tester: Codex CLI, tester recheck role
Date: 2026-04-26
Verdict: PASS

## Scope

Rechecked only the corrected blocking defect plus TASK-013 regression:

- dedicated persistence entities for WB API promotions;
- migration presence and migration cleanliness;
- regular and auto promotion persistence behavior;
- store scoping, operation linkage, `current_filter_timestamp` / API window, safe snapshots without secrets;
- existing TASK-013 behavior: current filter, details batching, nomenclatures pagination, Excel schema, classifier, no WB write endpoint;
- Stage 1 WB/Ozon Excel regression;
- full Django suite.

Product code was not changed. Real WB calls and real secrets were not used.

## Results

| Area | Result |
| --- | --- |
| Django model discovery returns `WBPromotion`, `WBPromotionSnapshot`, `WBPromotionProduct`, `WBPromotionExportFile` | PASS |
| Promotions migration is present | PASS |
| `makemigrations --check --dry-run` clean | PASS |
| Regular promotion persists `WBPromotion`, `WBPromotionSnapshot`, `WBPromotionProduct` rows | PASS |
| Regular promotion creates `WBPromotionExportFile` linked to `FileVersion` | PASS |
| Auto promotion persists `WBPromotion` / snapshot linkage | PASS |
| Auto promotion creates no `WBPromotionProduct` rows | PASS |
| Auto promotion creates no fake Excel/export file rows | PASS |
| Store scoping and operation linkage | PASS |
| `current_filter_timestamp`, API window and `allPromo=true` saved | PASS |
| Safe snapshot contains no token/header/API key/bearer/secret-like values | PASS |
| Current filter `startDateTime <= now_utc < endDateTime` | PASS |
| Details batching <=100 unique IDs | PASS |
| Nomenclatures pagination for `inAction=true/false`, `limit=1000`, until empty page | PASS |
| Excel promo schema | PASS |
| Operation classifier `mode=api`, `marketplace=wb`, `step_code=wb_api_promotions_download`, type not check/process | PASS |
| No WB promotions write endpoint | PASS |
| Stage 1 WB/Ozon Excel regression | PASS |
| Full Django suite | PASS |

## Commands And Results

```bash
git status --short
```

Result before recheck report write: existing implementation changes were present and were not modified by this recheck:

- `apps/discounts/wb_api/client.py`
- `apps/operations/models.py`
- `config/settings.py`
- `apps/discounts/wb_api/promotions/`
- `apps/operations/migrations/0004_allow_multiple_operation_outputs_per_kind.py`
- `docs/testing/TEST_REPORT_TASK_013.md`

```bash
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py check
```

Result: PASS. `System check identified no issues (0 silenced).`

```bash
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py shell -c "from django.apps import apps; print([apps.get_model('promotions', name).__name__ for name in ['WBPromotion','WBPromotionSnapshot','WBPromotionProduct','WBPromotionExportFile']])"
```

Result: PASS. Output:

```text
['WBPromotion', 'WBPromotionSnapshot', 'WBPromotionProduct', 'WBPromotionExportFile']
```

```bash
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py makemigrations --check --dry-run
```

Result: PASS. `No changes detected`.

```bash
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test apps.discounts.wb_api.promotions --verbosity 2 --noinput
```

Result: PASS. Ran 9 tests.

Covered:

- model discovery;
- regular promotion persistence and export link;
- auto promotion without product/export rows;
- current filter boundaries;
- API window / `allPromo=true` / `current_filter_timestamp`;
- details batching;
- nomenclatures pagination;
- Excel schema;
- access and active connection;
- operation classifier;
- secret redaction;
- no WB promotions upload endpoint reference.

```bash
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test apps.discounts.wb_api apps.operations apps.files apps.stores apps.audit apps.techlog apps.identity_access --verbosity 2 --noinput
```

Result: PASS. Ran 100 tests.

```bash
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test apps.discounts.wb_excel apps.discounts.ozon_excel --verbosity 2 --noinput
```

Result: PASS. Ran 21 tests.

```bash
set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py test --verbosity 1 --noinput
```

Result: PASS. Ran 141 tests.

```bash
rg -n "calendar/promotions/upload|promotions/upload|api/v1/calendar/promotions/upload|method=\"POST\"|method='POST'|\.post\(" apps/discounts/wb_api apps -g '*.py'
```

Result: PASS for TASK-013 no-write scan. No `calendar/promotions/upload` / WB promotions upload reference was found. `.post(` hits were unrelated Django view tests outside WB API promotions client/use case code.

## Recheck Evidence

`DEF-TASK-013-001` is closed.

Evidence:

- `apps.discounts.wb_api.promotions` is installed in Django settings.
- Migration `apps/discounts/wb_api/promotions/migrations/0001_initial.py` creates `WBPromotion`, `WBPromotionSnapshot`, `WBPromotionProduct`, `WBPromotionExportFile`.
- Runtime model introspection resolves all four required model names.
- Focused tests verify regular current promotion persistence into dedicated promotion/snapshot/product/export-link entities.
- Focused tests verify auto promotions persist promotion/snapshot linkage without invented products and without fake Excel/export rows.
- Focused tests verify snapshot/store/operation linkage, API window, `current_filter_timestamp`, and safe contours without token/header/API key/bearer/secret-like values.

## Findings

No new findings.

No new GAP was opened. The previous blocking defect was an implementation defect and is now verified closed.

## Audit Readiness

Ready for audit as PASS for TASK-013 recheck.

## Changed Files

- `docs/testing/TEST_REPORT_TASK_013_RECHECK.md`

