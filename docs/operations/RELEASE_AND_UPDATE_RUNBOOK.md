# RELEASE_AND_UPDATE_RUNBOOK.md

Трассировка: ТЗ §22, §27.

## Production baseline

Этап 1 разворачивается на Ubuntu VPS как Django application с PostgreSQL, nginx, systemd и server-rendered web UI. Docker не является обязательным условием baseline.

TASK-001 deployment skeleton использует nginx listen port `8080` в `deploy/nginx/promo_v2.conf.example`, так как на текущем сервере порт `80` уже занят действующим `nginx.service`. Перед production rollout порт нужно повторно проверить на целевом сервере.

## Перед обновлением

1. Зафиксировать версию релиза и список изменений.
2. Проверить отсутствие незавершённых критичных операций или зафиксировать план обработки.
3. Сделать backup PostgreSQL.
4. Сделать backup серверного файлового хранилища.
5. Проверить, что backup читается и имеет ожидаемый размер.
6. Подготовить rollback plan.

Команды pre-update backup для текущего Django-проекта:

```bash
cd /opt/promo_v2
. .venv/bin/activate
set -a && . /etc/promo_v2/env && set +a
POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres ./scripts/pre_update_backup.sh
```

Скрипт `scripts/pre_update_backup.sh` вызывает:

- `scripts/backup_postgres.sh` - `pg_dump --format=custom` в `${BACKUP_DIR:-/var/backups/promo_v2/postgres}` с retention 14 дней;
- `scripts/backup_media.sh` - архив `${DJANGO_MEDIA_ROOT:-/var/lib/promo_v2/media}` в `${BACKUP_DIR:-/var/backups/promo_v2/media}` с retention 14 дней.

Pre-update backup является отдельным release gate и выполняется перед каждым production update независимо от ежедневного расписания backup.

## Применение обновления

Команды baseline deployment/update:

```bash
cd /opt/promo_v2
sudo systemctl stop promo_v2
# Apply the approved release artifact prepared outside production.
# Example for unpacked artifact:
rsync -a --delete --exclude '.venv' --exclude 'media' <release-dir>/ /opt/promo_v2/
. .venv/bin/activate
python -m pip install -r requirements.txt
set -a && . /etc/promo_v2/env && set +a
POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres python manage.py migrate --noinput
python manage.py collectstatic --noinput
sudo systemctl start promo_v2
sudo nginx -t
sudo systemctl reload nginx
BASE_URL=http://127.0.0.1:8080 POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres ./scripts/deployment_smoke_check.sh
```

`deploy/systemd/promo_v2.service.example` запускает Django через `gunicorn config.wsgi:application` на `127.0.0.1:8000`. `deploy/nginx/promo_v2.conf.example` проксирует nginx на этот upstream и слушает port `8080`; port `80` не занимать без отдельного решения, потому что на текущем сервере он занят существующим `nginx.service`.

### Stage 3.0 Product Core release notes

Stage 3.0 / CORE-1 adds `apps.product_core` migrations and additive Product Core permissions/audit/techlog catalogs. Production rollout must apply migrations before runtime acceptance or Product Core tables such as `product_core_marketplacelisting` will be absent.

After `python manage.py migrate --noinput`, run the legacy listing backfill validation:

```bash
POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres python manage.py shell -c "from apps.marketplace_products.services import validate_legacy_product_listing_backfill; print(validate_legacy_product_listing_backfill())"
```

Expected release gate:

- `missing_listing_product_ids` is empty;
- `mismatched_mapping_product_ids` is empty;
- legacy `MarketplaceProduct` rows remain intact and existing Stage 1/2 `OperationDetailRow.product_ref` history remains raw/compatible.

Product Core routes introduced by Stage 3:

- `/references/product-core/products/` - internal products and variants;
- `/references/marketplace-listings/` - marketplace listings;
- `/references/marketplace-listings/unmatched/` - unmatched/review/conflict listing subset;
- `/references/marketplace-listings/<id>/mapping/` - manual mapping workflow.

Legacy `/references/products/` remains the `MarketplaceProduct` compatibility view. Do not use it as an `InternalProduct` route.

Product Core CSV exports:

- `/references/product-core/products/export.csv`;
- `/references/marketplace-listings/export.csv`;
- `/references/marketplace-listings/latest-values.csv`;
- `/references/marketplace-listings/mapping-report.csv`;
- `/references/marketplace-listings/unmatched/export.csv`.

Excel boundary after Stage 3: WB/Ozon Excel upload/check/process remains a Stage 1 operation flow. It must not be treated as an automatic import source for `InternalProduct`/`ProductVariant` records, confirmed mappings or `ProductMappingHistory`. Existing legacy `MarketplaceProduct` compatibility sync may still mirror operation `product_ref` values into unmatched `MarketplaceListing` compatibility records.

## Проверка после обновления

- `python manage.py check`;
- `curl -fsS http://127.0.0.1:8080/health/`;
- вход владельца;
- доступ главной;
- список операций;
- legacy product list/card at `/references/products/`;
- Product Core internal products at `/references/product-core/products/`;
- marketplace listings at `/references/marketplace-listings/`;
- unmatched listings and mapping page access for a test listing where available;
- Product Core CSV export links for an authorized user;
- загрузка тестового `.xlsx` в безопасном тестовом контуре или dry-run, если реализован;
- доступ к audit/tech log;
- отсутствие новых critical system notifications;
- проверка версии приложения.

## Откат

Если обновление неуспешно:

1. Остановить приложение.
2. Вернуть предыдущую версию кода.
3. Восстановить БД из backup, если миграции несовместимы.
4. Восстановить файловое хранилище при необходимости.
5. Запустить приложение.
6. Проверить целостность operations/files.
7. Зафиксировать инцидент в техжурнале и отчёте релиза.

## Восстановление после сбоя

При сбое приложения/сервера/БД/files:

- перезапустить сервисы;
- проверить доступность БД и файлового хранилища;
- проверить web UI;
- найти operations в `created`/`running`, прерванные сбоем;
- перевести их в `interrupted_failed`;
- не возобновлять автоматически;
- уведомить пользователей через системные уведомления.

## Backup policy этапа 1

Обязательные объекты:

- PostgreSQL;
- серверное файловое хранилище.

Утверждённая политика:

- PostgreSQL backup выполняется ежедневно.
- Backup серверного файлового хранилища выполняется ежедневно.
- Retention backup: 14 дней.
- Перед production update backup PostgreSQL и серверного файлового хранилища обязателен независимо от ежедневного расписания.
- Restore check выполняется по документированной ручной процедуре после setup и перед важными релизами.

## Daily backup setup

Ежедневный backup должен запускать оба объекта backup: PostgreSQL и серверное файловое хранилище. Retention 14 дней остаётся в `scripts/backup_postgres.sh` и `scripts/backup_media.sh` через `BACKUP_RETENTION_DAYS:-14`.

Baseline systemd setup:

```bash
cd /opt/promo_v2
sudo install -d -o www-data -g www-data -m 0750 /var/backups/promo_v2/postgres /var/backups/promo_v2/media
sudo install -m 0644 deploy/systemd/promo_v2-daily-backup.service.example /etc/systemd/system/promo_v2-daily-backup.service
sudo install -m 0644 deploy/systemd/promo_v2-daily-backup.timer.example /etc/systemd/system/promo_v2-daily-backup.timer
sudo systemctl daemon-reload
sudo systemctl enable --now promo_v2-daily-backup.timer
systemctl list-timers promo_v2-daily-backup.timer
```

Ручной smoke запуск после setup:

```bash
sudo systemctl start promo_v2-daily-backup.service
sudo systemctl status --no-pager promo_v2-daily-backup.service
```

Проверка наличия свежих backup PostgreSQL и media/file storage:

```bash
find /var/backups/promo_v2/postgres -maxdepth 1 -type f -name 'promo_v2_*.dump' -mtime -1 -size +0 -print
find /var/backups/promo_v2/media -maxdepth 1 -type f -name 'media_*.tar.gz' -mtime -1 -size +0 -print
```

Обе команды должны вывести хотя бы один непустой файл после успешного ежедневного или ручного запуска. Если используется нестандартный `POSTGRES_DB`, имя PostgreSQL dump соответствует `${POSTGRES_DB}_*.dump`.

Cron fallback, если systemd timer не используется:

```cron
15 2 * * * cd /opt/promo_v2 && set -a && . /etc/promo_v2/env && set +a && ./scripts/backup_postgres.sh && ./scripts/backup_media.sh
```

## Manual restore check procedure

Проверка восстановления выполняется в безопасном тестовом контуре, не поверх production:

1. Выбрать актуальный backup PostgreSQL и backup серверного файлового хранилища.
2. Поднять временную БД/тестовый контур восстановления.
3. Восстановить PostgreSQL backup.
4. Восстановить серверное файловое хранилище в тестовый storage path.
5. Запустить приложение или диагностическую команду в тестовом контуре.
6. Проверить наличие ключевых metadata: users, stores, operations, file versions, parameter snapshots, audit/techlog links.
7. Проверить доступность физических файлов, срок хранения которых не истёк.
8. Проверить целостность связей operation -> file version -> storage path/checksum.
9. Зафиксировать дату, источник backup, результат и найденные проблемы в release/update журнале.

Базовая проверка читаемости архивов и опциональное восстановление в отдельную БД:

```bash
cd /opt/promo_v2
. .venv/bin/activate
set -a && . /etc/promo_v2/env && set +a
POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres \
  ./scripts/restore_check.sh /var/backups/promo_v2/postgres/<dump>.dump /var/backups/promo_v2/media/<media>.tar.gz

# Для фактического restore check в непроизводственную БД:
POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres RESTORE_DB=promo_v2_restore_check_$(date +%Y%m%d%H%M%S) \
  ./scripts/restore_check.sh /var/backups/promo_v2/postgres/<dump>.dump /var/backups/promo_v2/media/<media>.tar.gz
```

Если restore check неуспешен, production update или важный release не проводится до устранения причины и успешной повторной проверки.

## Audit/techlog retention check

Audit records и techlog records хранятся 90 дней. Очистка выполняется только регламентной non-UI процедурой, не через обычный UI:

```bash
cd /opt/promo_v2
. .venv/bin/activate
set -a && . /etc/promo_v2/env && set +a
POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres ./scripts/audit_techlog_retention_check.sh

# Применение cleanup только по регламенту:
POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres APPLY_CLEANUP=1 ./scripts/audit_techlog_retention_check.sh
```

Команда вызывает `python manage.py cleanup_audit_techlog --dry-run`, а при `APPLY_CLEANUP=1` - фактическую очистку записей с истёкшим `retention_until`. Очистка не удаляет operations, file metadata, parameter snapshots, detail rows или historical links.
