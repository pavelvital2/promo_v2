# TEST_REPORT_LIVE_SMOKE_STAGE_2_1

Role: live smoke tester after Stage 2.1 WB API completion  
Date: 2026-04-26 17:52 MSK  
Environment: production-like gunicorn on `0.0.0.0:8080`, nginx present  
Verdict: FAIL / BLOCKED FOR LIVE STAGE 2.1 UI

## Scope

Performed safe live UI/HTTP smoke only:

- HTTP availability of `/`, login page and authenticated owner session.
- Marketplace/store navigation after login.
- WB API master entry/route, GET-only operation list/card checks.
- Safe Django checks using `.env.runtime`.

No product code was changed. No commit/push was made. Real WB token files were not read or printed. No WB upload/destructive/write UI action was submitted.

## Commands And Results

Authentication used owner login `pavel`; password is intentionally redacted in this report.

| Check | Command shape | Result |
| --- | --- | --- |
| Git baseline | `git status --short --branch` | `## main...origin/main`, no working tree changes before report |
| Root unauthenticated | `curl http://127.0.0.1:8080/` | `302` to `/accounts/login/?next=/` |
| Login page | `curl http://127.0.0.1:8080/accounts/login/` | `200` |
| Health | `curl http://127.0.0.1:8080/health/` | `200`, body `{"status": "ok"}` |
| Login owner | `curl -L` with CSRF/cookies and owner credentials | `200`, final URL `/` |
| Marketplaces after login | `curl -b cookies http://127.0.0.1:8080/marketplaces/` | `200` |
| Stores after login | `curl -b cookies http://127.0.0.1:8080/stores/` | `200` |
| WB Excel route | `curl -b cookies http://127.0.0.1:8080/marketplaces/wb/discounts/excel/` | `200` |
| WB store card | `curl -b cookies http://127.0.0.1:8080/stores/STORE-000001/` | `200` |
| Operations list API filter | `curl -b cookies 'http://127.0.0.1:8080/operations/?mode=api'` | `200` |
| Operation card | `curl -b cookies http://127.0.0.1:8080/operations/OP-2026-000025/` | `200` |
| WB API master | `curl -b cookies http://127.0.0.1:8080/marketplaces/wb/discounts/api/` | `404` |
| WB API master with store | `curl -b cookies 'http://127.0.0.1:8080/marketplaces/wb/discounts/api/?store=1'` | `404` |
| WB API upload confirm GET | `curl -b cookies 'http://127.0.0.1:8080/marketplaces/wb/discounts/api/upload/confirm/?store=1'` | `404` |
| Django system check | `set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py check` | PASS, no issues |
| Migration check | `set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py migrate --check` | FAIL, exit code `1` |
| Migration status | `set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py showmigrations web stores operations` | `stores 0003`, `operations 0003`, `operations 0004` are unapplied |

Additional nginx observations:

- `curl http://localhost/` returned `303` to `http://localhost/login`.
- `curl http://localhost/accounts/login/` returned `404`.
- `curl http://localhost/health/` returned `307`.
- Direct gunicorn/public port `http://23.26.193.117:8080/` returned `302` to `/accounts/login/?next=/`.

## Live UI Evidence

PASS:

- Owner login works through Django login form.
- Authenticated home, marketplaces, stores, WB Excel, store card, operation list and operation card are reachable on `127.0.0.1:8080`.
- Store list shows active WB store `STORE-000001 Vital Shevron` and active Ozon store `STORE-000002 Vital Shevron`.
- Operation list/card GET pages are reachable and show existing Stage 1 Excel operations.

FAIL / BLOCKED:

- Marketplace page after login shows `WB -> Скидки -> Excel` and `Ozon -> Скидки -> Excel`, but does not show a `WB -> Скидки -> API` entry.
- `GET /marketplaces/wb/discounts/api/` returns Django debug `404 Page not found`.
- `GET /marketplaces/wb/discounts/api/?store=1` also returns `404`.
- `GET /marketplaces/wb/discounts/api/upload/confirm/?store=1` also returns `404`.
- The live 404 URL resolver output does not list the WB API routes, while the current working tree contains them in `apps/web/urls.py`. This indicates the running gunicorn process is not serving the current Stage 2.1 UI code.
- Database schema is not upgraded for current Stage 2.1 code: `operations_operation.step_code` is absent, and `manage.py shell` query against `Operation.step_code` failed with `django.db.utils.ProgrammingError`.

## Defects / Blockers

### BLOCKER-001: Live gunicorn does not expose WB API UI routes

Expected: owner can open Stage 2.1 master at `/marketplaces/wb/discounts/api/` after login.  
Actual: route returns `404`; marketplace page has no WB API entry.  
Impact: Stage 2.1 WB API live UI smoke cannot proceed beyond route discovery. Prices/promotions/calculation/upload UI cards cannot be safely checked.

### BLOCKER-002: Live DB migrations for Stage 2.1 are unapplied

Expected: live DB schema supports Stage 2.1 operation classifier and UI queries.  
Actual: `migrate --check` exits `1`; `stores 0003`, `operations 0003`, `operations 0004` are unapplied; `operations_operation.step_code` does not exist.  
Impact: even if the live process were reloaded, current Stage 2.1 UI/code would likely fail against the live DB schema.

### BLOCKER-003: nginx endpoint on port 80 does not proxy the Django app paths checked here

Expected: nginx path to app should make root/login/health behavior consistent with the production-like app.  
Actual: `localhost:80` returns `/login` redirects and `404` for `/accounts/login/`, while gunicorn on `:8080` serves Django login.  
Impact: smoke via nginx is inconclusive or misconfigured for this app; Stage 2.1 live checks were performed directly against gunicorn `:8080`.

## Safety Notes

- Real WB token file was not opened.
- No POST was sent to WB API master, WB API upload confirmation, connection check, upload or destructive actions.
- The only POST was Django login.
- `.env.runtime` was sourced for Django checks; secrets from it are not included in this report.

## Final Verdict

Live smoke is failed/blocked. Basic platform navigation works, but Stage 2.1 WB API is not live on the running service and the live DB schema is not migrated for Stage 2.1.
