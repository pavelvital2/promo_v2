# FILE_CONTOUR.md

Трассировка: ТЗ §13, §17, §22, §24, §27.

## Файл как сущность

Файл - самостоятельная сущность с метаданными, сроком хранения, версиями и связями с операциями. В UI главным рабочим объектом остаётся operation, а не файловый реестр.

## Что хранится

На этапе 1 хранятся:

- входные файлы;
- выходные файлы;
- метаданные файлов;
- версии файлов;
- связи файлов с run и operations;
- сроки хранения.

Физические `.xlsx` и отчёты хранятся в серверном файловом хранилище. PostgreSQL хранит метаданные, идентификаторы/пути, checksum, version links и retention data.

## Версионность

Повторная загрузка исправленного файла, даже с тем же именем, создаёт новую file version. Завершённые операции остаются связанными с конкретной старой версией.

Обработка старой версии допустима только если:

- у старой версии есть допустимая проверка;
- пользователь явно выбирает старую версию и конкретную проверку;
- UI явно показывает, что обработка выполняется не по последней версии.

## Сроки хранения

- Физические файлы: 3 дня.
- История и метаданные операций: 90 дней, если не утверждён более длительный срок.

После истечения срока хранения файла:

- operation не удаляется;
- связь с file entity остаётся исторической;
- UI показывает, что срок хранения файла истёк;
- скачивание физического файла недоступно.

Implementation hook TASK-004: регламентная очистка физических файлов выполняется management command `cleanup_file_retention`. Команда удаляет только physical storage object после истечения 3 дней и сохраняет `FileObject` / `FileVersion` metadata, checksum, version number and operation/run placeholder references. Storage path формируется server-side без пользовательского пути: `files/<scenario>/<store_visible_id>/<file_visible_id>/vNNNNNN/<uuid>.<ext>`.

## Удаление и архивирование файлов

Файловый контур следует общей политике `docs/architecture/DELETION_ARCHIVAL_POLICY.md`:

- ошибочная загрузка может быть физически удалена только до запуска operation и только если нет связанных audit/techlog/history records;
- повторная загрузка исправленного файла создаёт новую `FileVersion`, а не перезаписывает старую;
- metadata `FileObject` и `FileVersion`, связанные с operation, не удаляются обычным пользовательским или административным действием;
- физический файл удаляется по сроку хранения 3 дня, но operation, checksum, version metadata и историческая связь сохраняются;
- UI показывает недоступность скачивания после истечения срока хранения вместо удаления operation/file history.

## Права скачивания

Скачать output file или detail report можно только при наличии:

- права на скачивание для конкретного сценария;
- объектного доступа к магазину/кабинету;
- доступного срока хранения файла;
- отсутствия индивидуального запрета.

Скачивание итогового файла может фиксироваться в аудите, если это включено как контролируемое действие.

## Резервное копирование

В backup обязательно входят:

- PostgreSQL;
- серверное файловое хранилище.

Backup policy этапа 1:

- daily PostgreSQL backup;
- daily server file storage backup;
- backup retention 14 days;
- mandatory backup before production update;
- restore check by documented manual procedure after setup and before important releases.

Восстановление должно проверять:

- наличие metadata в БД;
- доступность физических файлов, срок которых не истёк;
- целостность связей operation -> file version;
- отсутствие потери snapshot параметров и detail rows.

## Запреты

Нельзя:

- подменять файл завершённой operation;
- перезаписывать file version;
- удалять metadata operation при удалении физического файла по сроку;
- использовать файл без проверки объектного доступа;
- считать имя файла уникальным идентификатором версии.

## Stage 2.1 WB API file scenarios

Трассировка: `docs/source/stage-inputs/tz_stage_2.1.txt` §12.

Stage 2.1 использует тот же `FileObject/FileVersion/OperationInputFile/OperationOutputFile`, checksum, retention и download rights. Физические файлы остаются 3 дня, metadata и operation history сохраняются.

| Scenario | Kind | Создаётся | Используется как input |
| --- | --- | --- | --- |
| `wb_discounts_api_price_export` | output | 2.1.1 | 2.1.3 calculation |
| `wb_discounts_api_promotion_export` | output | 2.1.2, отдельный file per regular current promotion | 2.1.3 calculation |
| `wb_discounts_api_result_excel` | output | 2.1.3 | 2.1.4 upload basis и manual download |
| `wb_discounts_api_detail_report` | output | 2.1.1-2.1.4 when detail export requested | не является business input |
| `wb_discounts_api_upload_report` | output | 2.1.4 | не является business input |

Связи:

- 2.1.1 output связывается с 2.1.3 через `OperationInputFile` role `api_price_export`.
- 2.1.2 outputs связываются с 2.1.3 через `OperationInputFile` role `api_promotion_export`.
- 2.1.3 result связывается с 2.1.4 через `OperationInputFile` role `api_result_excel`.
- 2.1.4 upload report связывается с upload operation as output.

Promo files Stage 2.1 создаются отдельными `.xlsx` по акции. Zip/package не входит в обязательный scope и требует отдельного file scenario before implementation.

Download rights:

- price export: `wb.api.prices.file.download`;
- promotion export: `wb.api.promotions.file.download`;
- result Excel/detail: `wb.api.discounts.result.download`;
- upload report: `wb.api.operation.view` plus explicit download right if added.

Файлы и snapshots не содержат WB API tokens, authorization headers или secret-like values.

## Stage 2.2 Ozon API file scenarios

Трассировка: `docs/product/OZON_API_ELASTIC_BOOSTING_SPEC.md`.

Stage 2.2 uses the same `FileObject/FileVersion/OperationInputFile/OperationOutputFile`, checksum, retention and download rights. Physical files remain available for 3 days; metadata and operation history remain according to common rules.

| Scenario | Kind | Создаётся | Используется как input |
| --- | --- | --- | --- |
| `ozon_api_elastic_result_report` | output | `ozon_api_elastic_calculation` | control report; not upload source of truth |
| `ozon_api_elastic_manual_upload_excel` | output | TASK-024 post-acceptance generation from accepted Stage 2.2 calculation result, by ADR-0032 Stage 1-compatible template decision | secondary manual Ozon cabinet upload/control by user |
| `ozon_api_elastic_upload_report` | output | `ozon_api_elastic_upload` | not business input |
| `ozon_api_elastic_detail_report` | output | any Stage 2.2 step when detail export requested | not business input |

Upload source of truth is immutable accepted calculation snapshot. Downloaded Excel files cannot be edited and re-uploaded back into the API flow as accepted basis.

Manual upload Excel uses the current Stage 1 Ozon Excel template/format as a Stage 1-compatible manual upload file by customer decision 2026-04-30 / ADR-0032. It must be explicitly marked as manual upload Excel по Stage 1-compatible template, generated only after TASK-024 result acceptance from the immutable accepted Stage 2.2 calculation snapshot, and must not modify Stage 1 Ozon Excel business rules. Add/update rows write K=`Да` and L=`calculated_action_price`. Deactivate rows must remain visible; if the Stage 1-compatible template cannot directly represent deactivate action, the workbook/report includes a separate sheet/section `Снять с акции` with row-level reasons.

Download right: `ozon.api.elastic.files.download` plus object access and retention availability.

Ozon files and snapshots must not contain Client-Id, Api-Key, authorization headers, bearer/API key values or raw sensitive API responses.
