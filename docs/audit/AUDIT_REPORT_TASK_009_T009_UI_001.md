# AUDIT_REPORT_TASK_009_T009_UI_001

Дата аудита: 2026-04-25.

Роль: аудитор Codex CLI. Область: узкий аудит исправления дефекта TASK-009 / T009-UI-001 из `docs/testing/TEST_REPORT_TASK_009.md`.

## status

PASS

## scope

Проверены только task-scoped материалы:

- `docs/testing/TEST_REPORT_TASK_009.md`;
- `templates/web/operation_card.html`;
- `apps/web/views.py`;
- `apps/web/tests.py`;
- `docs/product/PERMISSIONS_MATRIX.md`;
- связанные route/download/permission helpers: `apps/web/urls.py`, `apps/files/services.py`, `apps/identity_access/services.py`, `apps/identity_access/seeds.py`, `apps/operations/models.py`.

Полное итоговое ТЗ не перечитывалось.

## findings

Нет findings уровня BLOCKER/MAJOR/MINOR.

## audit evidence

1. Detail report UI action теперь отделён от output workbook UI action.

   - Матрица прав требует отдельные права для `download_output` и `download_detail_report`: `docs/product/PERMISSIONS_MATRIX.md:61`-`62`.
   - View вычисляет `can_download_output` по `*_discounts_excel.download_output` и `can_download_detail` по `*_discounts_excel.download_detail_report`: `apps/web/views.py:714`-`723`.
   - Эти флаги передаются в шаблон раздельно: `apps/web/views.py:752`-`754`.
   - В шаблоне `detail_report` проверяется через `can_download_detail`: `templates/web/operation_card.html:46`-`47`.
   - Остальные output links проверяются через `can_download_output`: `templates/web/operation_card.html:48`-`49`.

2. Пользователь без `download_detail_report` не видит ссылку detail report.

   - Регрессионный тест создаёт пользователя с `view_check_result` + `download_detail_report`, но без `download_output`, и ожидает отсутствие output link и наличие detail link: `apps/web/tests.py:210`-`283`.
   - Затем тест деактивирует `download_detail_report`, выдаёт `download_output` и ожидает наличие output link и отсутствие detail link: `apps/web/tests.py:285`-`299`.

3. Прямой download route и permission model не расширены этим UI-исправлением.

   - URL скачивания остаётся прежним route на `download_file`: `apps/web/urls.py:18`.
   - `download_file` делегирует проверку `open_file_version_for_download`: `apps/web/views.py:840`-`844`.
   - File service по-прежнему маппит `FileObject.Kind.OUTPUT` на `download_output`, а `FileObject.Kind.DETAIL_REPORT` на `download_detail_report`: `apps/files/services.py:24`-`28`.
   - `download_permission_code` строит scenario permission из kind, а `assert_can_download_file_version` проверяет его через `has_permission`: `apps/files/services.py:204`-`223`.
   - Seed-набор сохраняет отдельные WB/Ozon permission codes для output и detail report: `apps/identity_access/seeds.py:54`-`55`, `apps/identity_access/seeds.py:67`-`68`.

4. Бизнес-логика расчётов, модель прав и доступов, маршруты операций и output model в проверенной области не изменялись по смыслу исправления.

   - Исправление в UI соответствует исходному дефекту: тестовый отчёт фиксировал, что прямой detail download работал по `download_detail_report`, но карточка скрывала ссылку из-за проверки только `can_download_output`: `docs/testing/TEST_REPORT_TASK_009.md:72`-`88`.
   - В проверенных файлах не найдено расширения доступа, которое позволяло бы `download_output` открывать detail report или `download_detail_report` открывать основной output workbook.

## sanity checks

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
Ran 13 tests in 16.119s

OK
Destroying test database for alias 'default'...
```

## limitations

- `git status --short` недоступен: `/home/pavel/projects/promo_v2` не является git repository. Вывод об отсутствии расширения scope сделан по task-scoped inspection перечисленных файлов.
- Аудит не выполнял роль тестировщика и не проводил полный TASK-009 regression вне `apps.web`.

## recommendation

Можно передавать тестировщику. Минимальная повторная проверка со стороны тестировщика: сценарии карточки операции для пользователей с `download_detail_report` only, `download_output` only, both rights и neither right.
