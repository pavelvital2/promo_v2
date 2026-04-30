# TASK-023-ozon-elastic-calculation-reports.md

ID: TASK-023  
Тип задачи: реализация Stage 2.2 calculation  
Агент: разработчик Codex CLI  
Цель: implement shared Ozon calculation engine reuse for API canonical rows and generate result report/calculation artifacts.

Входные документы:
- `AGENTS.md`
- `docs/README.md`
- `docs/DOCUMENTATION_MAP.md`
- `docs/orchestration/AGENTS.md`
- `docs/roles/READING_PACKAGES.md`
- `docs/tasks/implementation/stage-2/TASK-023-ozon-elastic-calculation-reports.md`
- `docs/stages/stage-2/STAGE_2_SCOPE.md`
- `docs/stages/stage-2/STAGE_2_2_OZON_SCOPE.md`
- `docs/product/OZON_API_ELASTIC_BOOSTING_SPEC.md`
- `docs/product/OZON_API_ELASTIC_UI_SPEC.md`
- `docs/product/OZON_DISCOUNTS_EXCEL_SPEC.md`
- `docs/architecture/API_CONNECTIONS_SPEC.md`
- `docs/architecture/DATA_MODEL.md`
- `docs/architecture/FILE_CONTOUR.md`
- `docs/product/OPERATIONS_SPEC.md`
- `docs/architecture/AUDIT_AND_TECHLOG_SPEC.md`
- `docs/product/PERMISSIONS_MATRIX.md`
- `docs/testing/STAGE_2_2_OZON_TEST_PROTOCOL.md`
- `docs/testing/STAGE_2_2_OZON_ACCEPTANCE_CHECKLISTS.md`
- `docs/gaps/GAP_REGISTER.md`
- `docs/adr/ADR_LOG.md`

Связанные GAP/ADR:
- ADR-0022, ADR-0025, ADR-0028, ADR-0029, ADR-0030, ADR-0031, ADR-0032.
- `GAP-0021` resolved 2026-04-30: `candidate_and_active` rows are treated as active for write planning and retain collision details in result rows/report.
- `GAP-0015` resolved 2026-04-30: canonical J is `/v3/product/info/list` `min_price`; absent/non-numeric `min_price` uses existing reason `missing_min_price`.
- `GAP-0016` resolved 2026-04-30: canonical R is summed `present` across all `/v4/product/info/stocks` rows, including FBO + FBS, without subtracting `reserved`; absent stock info or summed `present <= 0` uses existing reason `no_stock`.
- `GAP-0017` resolved 2026-04-30: manual upload Excel uses Stage 1-compatible Ozon Excel template/format as secondary artifact with accepted compatibility risk; actual file generation is post-acceptance in TASK-024.

Разрешённые файлы / области изменения:
- `apps/discounts/ozon_excel/` only for safe extraction/reuse of shared decision engine without changing behavior.
- future `apps/discounts/ozon_shared/`, `apps/discounts/ozon_api/calculation*`, file/report writers, tests.

Запрещённые файлы / области изменения:
- Changing Ozon Excel output behavior or rule order.
- Upload/deactivate implementation.
- Generating `ozon_api_elastic_manual_upload_excel` before TASK-024 acceptance.
- Changing Stage 1 Ozon Excel business rules or template behavior while preparing reusable manual-upload writer/guard code for post-acceptance generation.

Ожидаемый результат:
- `ozon_api_elastic_calculation` operation.
- Calculation basis uses saved selected `action_id` from the store/account workflow context.
- API canonical fixture and equivalent Excel fixture produce same decisions.
- Result groups add/update/deactivate/skip/blocked are persisted.
- Result report scenario `ozon_api_elastic_result_report` generated.
- Calculation artifacts/snapshots include the data needed by TASK-024 to generate post-acceptance manual upload Excel, but TASK-023 does not create `ozon_api_elastic_manual_upload_excel`.
- Candidate/active collision rows are reported as `candidate_and_active`; upload_ready -> `update_action_price`, not_upload_ready -> `deactivate_from_action`.

Обязательные проверки:
- all 7 Ozon rules;
- absent/non-numeric `min_price` produces existing reason `missing_min_price`;
- missing stock info or summed `present <= 0` produces existing reason `no_stock`;
- golden API-vs-Excel decision parity;
- active + not_upload_ready -> deactivate_required with mandatory reason;
- candidate_and_active + upload_ready -> update_action_price, no duplicate add;
- candidate_and_active + not_upload_ready -> deactivate_required with mandatory reason;
- candidate + not_upload_ready -> skip_candidate;
- calculation artifacts expose add/update/deactivate rows and required deactivate reasons for TASK-024 post-acceptance manual upload Excel generation;
- no `ozon_api_elastic_manual_upload_excel` file exists before result acceptance;
- no write endpoints called.

Получатель результата:
- orchestrator Stage 2.2 and auditor.
