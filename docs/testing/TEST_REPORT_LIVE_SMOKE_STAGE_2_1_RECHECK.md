# TEST_REPORT_LIVE_SMOKE_STAGE_2_1_RECHECK

Role: live smoke recheck tester after Stage 2.1 WB API migrations and gunicorn restart  
Date: 2026-04-26 18:05 MSK  
Environment: production-like gunicorn on `0.0.0.0:8080`; checks executed against `http://127.0.0.1:8080`  
Verdict: PASS WITH REMAINING DATA LIMITATION

## Scope

Performed safe live UI/HTTP recheck only:

- `migrate --check` after live migrations.
- HTTP availability of `/`, `/accounts/login/`, `/health/`.
- Owner login and authenticated navigation for marketplaces, stores, WB Excel, operations.
- WB API Stage 2.1 UI routes by GET only.
- Secret/token redaction smoke on fetched UI HTML.

No product code was changed. No commit/push was made. Real WB token files were not read or printed. No real WB write/upload action was executed. No WB upload POST was submitted. The only POST was Django login.

## Commands And Results

Authentication used owner login `pavel`; password is intentionally redacted in this report.

| Check | Command shape | Result |
| --- | --- | --- |
| Git baseline | `git status --short --branch` | `## main...origin/main`; existing untracked primary smoke report present |
| Migration check | `set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py migrate --check` | PASS, exit code `0`, no output |
| Migration status | `set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py showmigrations stores operations marketplace_products files` | PASS; `stores 0003`, `operations 0003`, `operations 0004` are applied |
| Django system check | `set -a; . ./.env.runtime; set +a; .venv/bin/python manage.py check` | PASS, `System check identified no issues` |
| Root unauthenticated | `curl http://127.0.0.1:8080/` | `302` to `/accounts/login/?next=/` |
| Login page | `curl http://127.0.0.1:8080/accounts/login/` | `200` |
| Health | `curl http://127.0.0.1:8080/health/` | `200`, body `{"status": "ok"}` |
| Login owner | `curl -L` with CSRF/cookies and owner credentials | `200`, final URL `/` |
| Marketplaces after login | `curl -b cookies http://127.0.0.1:8080/marketplaces/` | `200`; WB API entry is visible |
| Stores after login | `curl -b cookies http://127.0.0.1:8080/stores/` | `200` |
| Store card | `curl -b cookies http://127.0.0.1:8080/stores/STORE-000001/` | `200` |
| WB Excel route | `curl -b cookies http://127.0.0.1:8080/marketplaces/wb/discounts/excel/` | `200` |
| Operations list API filter | `curl -b cookies 'http://127.0.0.1:8080/operations/?mode=api'` | `200` |
| Operation card | `curl -b cookies http://127.0.0.1:8080/operations/OP-2026-000025/` | `200` |
| WB API master | `curl -b cookies http://127.0.0.1:8080/marketplaces/wb/discounts/api/` | `200` |
| WB API master with store | `curl -b cookies 'http://127.0.0.1:8080/marketplaces/wb/discounts/api/?store=1'` | `200` |
| WB API upload confirm GET without calculation basis | `curl -b cookies 'http://127.0.0.1:8080/marketplaces/wb/discounts/api/upload/confirm/?store=1'` | `404`; expected for missing successful calculation basis id |
| Calculation basis selector | HTML inspection of WB API master with `store=1` | Selector is present and disabled; no `calculation_operation_id` options available |
| Secret/token UI smoke | HTML scan of fetched owner pages | PASS; no `Bearer`, `authorization`, API key/access token/WB token markers found; no raw secret/token printed in checked pages |

## Live UI Evidence

PASS:

- The previous migration blocker is cleared: `migrate --check` passes and Stage 2.1 migrations are applied.
- Owner login works through the Django login form.
- Authenticated home, marketplaces, stores, store card, WB Excel, operation list and operation card are reachable on `127.0.0.1:8080`.
- Marketplace page now shows `WB -> Скидки -> API`.
- `GET /marketplaces/wb/discounts/api/` returns `200`.
- `GET /marketplaces/wb/discounts/api/?store=1` returns `200`.
- WB API master page renders the price basis, promotion basis and calculation basis controls.
- The upload confirmation entry is a GET form with a calculation basis selector; no upload action is performed by opening the master page.
- Checked UI pages do not print a raw WB secret/token.

Remaining data limitation:

- There is no successful WB API calculation basis option available in the current live data. The `calculation_operation_id` selector is disabled and empty.
- Because there is no calculation basis id, the safe upload confirm GET with only `store=1` returns `404`. This does not prove the upload confirmation page with a valid calculation basis, and no POST/upload was attempted.

## Defects / Blockers

No remaining live smoke blocker for Stage 2.1 route availability or migrations.

The following primary-smoke blockers are rechecked as closed:

- `BLOCKER-001`: Live gunicorn now exposes WB API UI routes.
- `BLOCKER-002`: Live DB migrations for Stage 2.1 are now applied.

Not rechecked in this pass:

- nginx endpoint behavior on port `80`; task context specified gunicorn on `0.0.0.0:8080` and `/health/` after restart.

## Safety Notes

- Real WB token file was not opened.
- No WB API upload/destructive/write POST was sent.
- No connection check POST was sent.
- `.env.runtime` was sourced only for Django checks; secrets from it are not included in this report.

## Final Verdict

Live smoke recheck is PASS for migrations, base HTTP availability, owner navigation, WB Excel, operations and WB API route availability on gunicorn `:8080`.

One data limitation remains: upload confirmation could not be opened with a valid `calculation_operation_id` because the live UI currently has no successful calculation basis option. The master page confirms the selector exists and is disabled, and no upload action was performed.
