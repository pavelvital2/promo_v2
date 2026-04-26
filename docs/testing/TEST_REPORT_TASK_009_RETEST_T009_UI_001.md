# TEST_REPORT_TASK_009_RETEST_T009_UI_001

Дата ретеста: 2026-04-25.

Роль проверки: тестировщик Codex CLI. Область: отдельный ретест дефекта TASK-009 / T009-UI-001 после PASS-аудита. Продуктовый код не изменялся.

## status

PASS

Дефект T009-UI-001 не воспроизводится: ссылка на `detail_report` в карточке операции управляется правом `download_detail_report`, ссылки на основные output-файлы управляются правом `download_output`, прямой download detail report разрешается/блокируется согласно отдельному праву.

## checked files

- `docs/testing/TEST_REPORT_TASK_009.md`
- `docs/audit/AUDIT_REPORT_TASK_009_T009_UI_001.md`
- `docs/audit/AUDIT_REPORT_TASK_009_DEFECT_T009_UI_001.md`
- `templates/web/operation_card.html`
- `apps/web/tests.py`
- `apps/web/views.py`

`docs/product/PERMISSIONS_MATRIX.md` не перечитывался: для ретеста хватило аудиторских выводов, шаблона, view context и исполняемых тестов.

## test steps and actual results

| # | Step | Actual result | Status |
| --- | --- | --- | --- |
| 1 | Проверить шаблон карточки операции для output links. | `detail_report` ветвится отдельно и использует `can_download_detail`; остальные output links используют `can_download_output`. | PASS |
| 2 | Проверить view context карточки операции. | `operation_card` вычисляет и передаёт отдельные флаги `can_download_output` и `can_download_detail`. | PASS |
| 3 | Проверить штатный regression `apps.web`. | `apps.web` содержит тест отдельной видимости output/detail download links; весь набор `apps.web` прошёл. | PASS |
| 4 | Пользователь с `download_detail_report`, но без `download_output`, открывает карточку операции. | В одноразовом Django test runner карточка вернула HTTP 200, ссылка detail report присутствовала, ссылка output workbook отсутствовала. | PASS |
| 5 | Тот же пользователь скачивает detail report прямым URL. | Прямой download detail report вернул HTTP 200. | PASS |
| 6 | Пользователь без `download_detail_report`, но с `download_output`, открывает карточку операции. | Карточка вернула HTTP 200, ссылка output workbook присутствовала, ссылка detail report отсутствовала. | PASS |
| 7 | Пользователь без `download_detail_report` скачивает detail report прямым URL. | Прямой download detail report вернул HTTP 403. | PASS |

## commands run/results

```bash
POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres .venv/bin/python manage.py check
```

Result: PASS.

```text
System check identified no issues (0 silenced).
```

```bash
POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres .venv/bin/python manage.py test apps.web
```

Result: PASS.

```text
Found 13 test(s).
Creating test database for alias 'default'...
System check identified no issues (0 silenced).
.............
----------------------------------------------------------------------
Ran 13 tests in 16.593s

OK
Destroying test database for alias 'default'...
```

Additional focused retest runner, without changing product files:

```text
Found 1 test(s).
test_detail_report_ui_and_direct_download_permissions ... ok

----------------------------------------------------------------------
Ran 1 test in 2.384s

OK
Destroying test database for alias 'default' ('test_promo_v2')...
System check identified no issues (0 silenced).
```

Covered assertions:

- detail-only user: operation card HTTP 200, detail link present, output link absent, direct detail download HTTP 200;
- output-only user: operation card HTTP 200, output link present, detail link absent, direct detail download HTTP 403.

## residual risks

- Проверка выполнена через Django test client и статический просмотр task-scoped файлов; ручной браузерный прогон не выполнялся.
- Ретест ограничен дефектом T009-UI-001 и regression `apps.web`; полный TASK-009 regression вне `apps.web` не запускался.
- Обычная БД `promo_v2` в окружении отсутствует; исполняемые проверки выполнялись через Django test database, как и обязательный regression.
