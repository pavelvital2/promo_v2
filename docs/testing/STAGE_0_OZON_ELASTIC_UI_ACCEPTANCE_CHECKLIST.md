# STAGE_0_OZON_ELASTIC_UI_ACCEPTANCE_CHECKLIST.md

Трассировка: `docs/tasks/design/stage-0/STAGE_0_OZON_ELASTIC_UI_TZ.md`; `docs/product/OZON_API_ELASTIC_UI_SPEC.md`; `docs/reports/WEB_PANEL_UX_AUDIT_2026-04-30.md`.

Статус: Stage 0 UI acceptance package for future implementation.

## Preconditions

- [ ] Project documentation audit for Stage 0 UI design is passed before product code changes.
- [ ] Product code implementation task explicitly references `docs/product/OZON_API_ELASTIC_UI_SPEC.md`.
- [ ] Current `docs/gaps/GAP_REGISTER.md` is checked before implementation; no open spec-blocking UX/functionality gap affects the UI slice.
- [ ] Implementation does not change Ozon Elastic calculation logic, reason/result codes, rights, file contour, audit/techlog or operation contour.
- [ ] Stage 1 Ozon Excel and Stage 2.2 Ozon API non-UI regression checks remain in scope of the release task.

## Page And Tabs

- [ ] Page path remains `Маркетплейсы / Ozon / Акции / API / Эластичный бустинг`.
- [ ] Page has tabs `Рабочий процесс`, `Результат`, `Диагностика`.
- [ ] Default tab is `Рабочий процесс`.
- [ ] User remains on the scenario page after each step, review action, file download action and upload completion.
- [ ] Workflow header uses human-readable labels and does not show raw `basis`, `checksum`, `source_operations`, `step_code` or raw JSON-like data.

## Seven-Step Workflow

- [ ] `Рабочий процесс` shows 7 operator steps in the approved order.
- [ ] Old active/candidate/product-data steps are represented as one operator step `Скачать товары и данные по ним`.
- [ ] The combined operator step still preserves the three underlying operations and their separate `step_code` values.
- [ ] `Скачать Excel результата` is not shown as a main workflow step.
- [ ] `Excel результата` remains available from `Результат`, `Диагностика` and operation card.
- [ ] Completed steps show only compact status, time, primary counts and details link.
- [ ] Technical summary/checksum/source operation details are not visible in `Рабочий процесс`.
- [ ] Combined product/data step can continue after warnings only when enough data exists for calculation.
- [ ] Errors that make calculation impossible block the next step.

## Result Tab

- [ ] `Результат` shows all groups: `Будет обновлено в акции`, `Будет добавлено в акцию`, `Не проходит расчёт сейчас`, `Будет снято с акции`, `Ошибки`.
- [ ] Empty groups are compact and show counter `0`.
- [ ] After upload row rejections, group `Отклонено Ozon` is shown.
- [ ] Tables paginate at 10 rows per page.
- [ ] Filters are human-readable and cover source, action, reason/status and product search.
- [ ] Row shows short human-readable reason.
- [ ] Row expansion shows full human-readable reason and safe details.
- [ ] Candidates that pass calculation appear in `Будет добавлено в акцию`.
- [ ] Candidates that do not pass calculation appear in `Не проходит расчёт сейчас`, not in workflow summary.
- [ ] Active or `candidate_and_active` rows that do not pass calculation appear in `Будет снято с акции`.
- [ ] Result summary explicitly states that both participating products and candidates were calculated.

## Files

- [ ] `Excel для ручной загрузки` is shown in workflow step 6 and in `Результат` files block.
- [ ] `Excel результата` is not shown as a main workflow step.
- [ ] Manual upload Excel is labelled as `Stage 1-compatible template`.
- [ ] Manual upload Excel is presented as secondary to API upload, not as replacement for API upload.
- [ ] Deactivate rows are not silently omitted from manual artifacts.
- [ ] If the template cannot represent deactivate directly, the files block states that workbook/report includes `Снять с акции` sheet/section.
- [ ] File retention/expired download states follow `docs/architecture/FILE_CONTOUR.md`.
- [ ] File versions/checksums remain linked to operations and visible in diagnostics/card, not as workflow noise.

## Diagnostics

- [ ] `Диагностика` is hidden from users outside owner/admin personas and from users without the existing required operation/audit/techlog permissions and object access.
- [ ] `ozon.api.operation.view` alone does not expose `Диагностика`.
- [ ] `Диагностика` uses existing permission codes only; no new permission code is introduced.
- [ ] Diagnostics groups operation evidence, calculation basis, snapshots/checksums, API metadata, audit/techlog links and technical codes.
- [ ] `Диагностика` never exposes Client-Id, Api-Key, authorization headers, bearer/API key values, raw secret-like values or raw sensitive API responses.
- [ ] Large raw values are collapsed by default and displayed in scrollable/preformatted blocks.
- [ ] `techlog.sensitive.view` is required for sensitive technical detail refs; secrets are still not shown.

## Review And Upload

- [ ] `Принять результат` and `Не принять результат` are result-state actions, not separate operations.
- [ ] Before accepting a result with deactivate rows, UI shows counts and reasons for `Будет снято с акции`.
- [ ] Upload requires accepted non-stale result.
- [ ] Add/update confirmation is required when add/update rows exist.
- [ ] Deactivate group confirmation is required when deactivate rows exist.
- [ ] Deactivate confirmation is one group-level confirmation for all `deactivate_from_action` rows.
- [ ] Without deactivate group confirmation, upload is blocked as `review_pending_deactivate_confirmation` / `ozon_api_upload_blocked_deactivate_unconfirmed`.
- [ ] Without deactivate group confirmation, no `ozon_api_elastic_upload` operation is created.
- [ ] Without deactivate group confirmation, add/update does not silently proceed as final upload scenario.
- [ ] Final upload block after success shows upload status, sent count, accepted count, rejected count, operation card link and manual Excel link.

## Operation Card

- [ ] Ozon API operation card shows `step_code` and does not force Stage 2.2 operations into `check/process`.
- [ ] Short block contains human-readable summary, status, store, initiator, start/end, primary counts, files and related links.
- [ ] Raw summary/basis/source operations/API metadata are in collapsed technical blocks.
- [ ] Long JSON-like values do not stretch the full page; they are scrollable/preformatted and collapsed by default.
- [ ] Audit/debug data is visually separated from the user summary.
- [ ] Upload operation card shows confirmation facts, drift-check result, add/update/deactivate batch summaries and row-level rejections.

## Marketplace Navigation

- [ ] `Маркетплейсы` page uses hierarchy: marketplace -> section -> mode -> scenario.
- [ ] Ozon active path is `Ozon -> Акции -> API -> Эластичный бустинг`.
- [ ] Future sections `Цены`, `Акции`, `Остатки`, `Продажи`, `В производство`, `Поставки` are shown as inactive `Планируется` when not implemented.
- [ ] Future inactive entries do not expose action buttons, forms or implemented-looking routes.
- [ ] Top global navigation remains unchanged.

## Responsive And Accessibility Smoke

- [ ] Desktop viewport has no overlapping controls or clipped labels.
- [ ] Mobile viewport around `390x844` has no page-level horizontal overflow.
- [ ] Tables on mobile use row cards or local scroll inside the table area, not whole-page overflow.
- [ ] Long technical values cannot expand the mobile page width.
- [ ] Buttons show disabled/processing/completed/failed states.
- [ ] During processing, current-step submit buttons are disabled and the user sees that the action is running.
- [ ] Text in buttons/cards fits on desktop and mobile.
- [ ] Human-readable Russian labels are used in operator-facing workflow and result areas.

## Regression Guards

- [ ] Stage 2.2 underlying operation step codes remain unchanged.
- [ ] Stage 2.2 audit action codes and techlog event types remain unchanged.
- [ ] Stage 2.2 file scenarios and retention rules remain unchanged.
- [ ] Stage 2.2 permission codes remain unchanged.
- [ ] Stage 2.2 business reason/result codes remain unchanged.
- [ ] Ozon Excel Stage 1 remains available and is not replaced by API flow.
