# TASK-022-ozon-elastic-product-data-join.md

ID: TASK-022  
Тип задачи: реализация Stage 2.2 data join  
Агент: разработчик Codex CLI  
Цель: реализовать product info/stocks download and canonical Ozon `J/O/P/R` rows for selected action product set.

Входные документы:
- `AGENTS.md`
- `docs/README.md`
- `docs/DOCUMENTATION_MAP.md`
- `docs/orchestration/AGENTS.md`
- `docs/roles/READING_PACKAGES.md`
- `docs/tasks/implementation/stage-2/TASK-022-ozon-elastic-product-data-join.md`
- `docs/stages/stage-2/STAGE_2_SCOPE.md`
- `docs/stages/stage-2/STAGE_2_2_OZON_SCOPE.md`
- `docs/product/OZON_API_ELASTIC_UI_SPEC.md`
- `docs/architecture/API_CONNECTIONS_SPEC.md`
- `docs/product/PERMISSIONS_MATRIX.md`
- `docs/product/OZON_API_ELASTIC_BOOSTING_SPEC.md`
- `docs/product/OZON_DISCOUNTS_EXCEL_SPEC.md`
- `docs/architecture/DATA_MODEL.md`
- `docs/architecture/FILE_CONTOUR.md`
- `docs/product/OPERATIONS_SPEC.md`
- `docs/architecture/AUDIT_AND_TECHLOG_SPEC.md`
- `docs/testing/STAGE_2_2_OZON_TEST_PROTOCOL.md`
- `docs/testing/STAGE_2_2_OZON_ACCEPTANCE_CHECKLISTS.md`
- `docs/gaps/GAP_REGISTER.md`
- `docs/adr/ADR_LOG.md`

Связанные GAP/ADR:
- ADR-0022, ADR-0025, ADR-0029, ADR-0030, ADR-0031, ADR-0034.
- `GAP-0015` resolved 2026-04-30: J uses `/v3/product/info/list` `min_price`; absent/non-numeric `min_price` maps to `missing_min_price`.
- `GAP-0016` resolved 2026-04-30: R uses sum of `present` across all `/v4/product/info/stocks` rows, including FBO + FBS; `reserved` is not subtracted; missing stock info or summed `present <= 0` maps to `no_stock`.
- `GAP-0019` resolved 2026-04-30 by technical/orchestrator decision: read page size/default request chunk `100`, minimum interval `500 ms`, read-only transient retry with bounded backoff.

Разрешённые файлы / области изменения:
- future `apps/discounts/ozon_api/product_data*`, normalizers, snapshots/detail rows, tests.

Запрещённые файлы / области изменения:
- Changing Ozon Excel rules.
- Calculation/upload UI beyond prerequisites.
- Ozon write endpoints.

Ожидаемый результат:
- `ozon_api_elastic_product_data_download` operation builds joined canonical rows.
- Product info and stocks are fetched for union product ids.
- Product info/stocks read pagination/request chunks follow ADR-0034 default `100`, with minimum request interval `500 ms`.
- J is mapped from `/v3/product/info/list` `min_price`; absent/non-numeric `min_price` leaves J absent for existing reason `missing_min_price`.
- R is mapped from `/v4/product/info/stocks` by summing `present` across all stock rows, including FBO + FBS; `reserved` is not subtracted.
- Joined rows remain tied to saved selected `action_id` from the store/account workflow basis.
- Missing fields are visible and coded.
- Action-row stock is not used as sole R source.

Обязательные проверки:
- J mapping from `/v3/product/info/list` `min_price`, including absent/non-numeric `min_price` -> `missing_min_price`;
- R aggregation per ADR-0031, including multiple FBO/FBS stock rows, `reserved` ignored, missing stock info and summed `present <= 0` -> `no_stock`;
- missing product info/stock info;
- page/request chunk default `100`, minimum interval `500 ms`, and read retry only for `429`, `5xx`, timeout/network with bounded backoff;
- safe snapshots and no secret leakage.

Получатель результата:
- orchestrator Stage 2.2 and auditor.
