# PROJECT_NAVIGATOR.md

Статус: навигационная карта проекта.

Назначение: быстро объяснить новому специалисту, Codex CLI оркестратору или агенту, что это за проект, что уже реализовано, где лежит документация и какие границы нельзя менять без отдельного решения.

Этот документ не заменяет исходное ТЗ, ADR, GAP, task files, audit reports, спецификации и тестовые протоколы. Он только показывает, куда идти и что читать.

## 1. Что такое promo_v2

`promo_v2` - внутренняя веб-панель для работы с маркетплейсами WB и Ozon: магазины, товары, листинги, цены, скидки, акции, API/Excel-операции и дальнейшее развитие в сторону складского, производственного и закупочного контуров.

Техническая база: Django + PostgreSQL modular monolith.

## 2. Иерархия источников

При противоречиях используется такой порядок:

1. `itogovoe_tz_platforma_marketplace_codex.txt` - исходный источник истины для аудита и спорных требований.
2. Утверждённая исполнительная документация в `docs/`.
3. `docs/adr/ADR_LOG.md` и `docs/gaps/GAP_REGISTER.md`.
4. Task-scoped задачи в `docs/tasks/`.
5. Audit/test/release reports в `docs/audit/`, `docs/testing/`, `docs/reports/`.

Итоговое ТЗ не перечитывается целиком каждым агентом. Оркестратор выдаёт task-scoped пакет и конкретные разделы ТЗ.

## 3. Главная архитектурная идея

Ядро системы находится внутри компании:

- `InternalProduct` / `ProductVariant` - внутренний товар и вариант.
- `MarketplaceListing` - внешний листинг товара в конкретном магазине WB/Ozon.
- WB/Ozon - внешние каналы продаж, а не ядро системы.
- API WB/Ozon - источник актуальных внешних данных.
- Excel - операционный вход/выход, но не источник истины по внутреннему товару.
- `MarketplaceProduct` - legacy-слой совместимости, который нельзя удалять или очищать без утверждённого migration/backup/rollback plan и regression-тестов Stage 1/2.

## 4. Текущее состояние

Актуальный статус вынесен в `docs/project/CURRENT_STATUS.md`.

Кратко: Stage 1 Excel workflows, Stage 2.1 WB API, Stage 2.2 Ozon Elastic API и Stage 3.0 / CORE-1 Product Core Foundation реализованы и покрыты текущими отчётами аудита/тестов.

## 5. Карта модулей

| Модуль | Назначение |
| --- | --- |
| `apps.stores` | магазины, кабинеты, API-подключения |
| `apps.operations` | операции, runs, строки операций |
| `apps.marketplace_products` | legacy marketplace products |
| `apps.product_core` | внутренние товары, варианты, листинги, snapshots, mapping |
| `apps.discounts` | WB/Ozon скидки Excel/API |
| `apps.audit` | audit trail |
| `apps.techlog` | технический журнал |
| `apps.identity_access` | пользователи, роли, права |

## 6. Карта документации

Начинать чтение с:

1. `AGENTS.md`
2. `docs/README.md`
3. `docs/DOCUMENTATION_MAP.md`
4. `docs/roles/READING_PACKAGES.md`
5. `docs/orchestration/AGENTS.md`
6. `docs/orchestration/ORCHESTRATION.md`
7. `docs/adr/ADR_LOG.md`
8. `docs/gaps/GAP_REGISTER.md`

Дальше читать только документы из выданного task-scoped пакета.

## 7. Карта этапов

| Этап | Статус | Суть |
| --- | --- | --- |
| Stage 1 | реализован | Excel workflows WB/Ozon |
| Stage 2.1 | реализован | WB API prices/promotions/discount upload |
| Stage 2.2 | реализован / покрыт regression | Ozon Elastic Boosting API |
| Stage 3.0 / CORE-1 | реализован / принят | Product Core Foundation |
| Следующий этап | требует отдельного ТЗ | перевод операций на Product Core, склад/производство позже |

## 8. Роли и чтение

Роли не получают весь проект целиком. Каждая роль получает задачу и пакет чтения:

- оркестратор - `docs/roles/READING_PACKAGES.md`, orchestration docs, ADR/GAP и профильные документы;
- проектировщик - профильный stage scope, исходные ограничения, ADR/GAP и docs update protocol;
- разработчик - конкретный task file, профильные specs, tests и ограниченный кодовый контекст;
- аудитор - task output, specs, acceptance checklist, ADR/GAP и релевантные разделы ТЗ;
- тестировщик - test protocol, acceptance checklist, task file и regression scope;
- техрайтер - handoff, изменённые docs, reports, ADR/GAP и documentation update protocol.

Полные правила чтения: `docs/roles/READING_PACKAGES.md`.

## 9. Audit-Gate

Перед реализацией нового этапа:

1. проектировщик готовит исполнительную документацию;
2. аудитор проверяет полноту, трассируемость и непротиворечивость;
3. замечания возвращаются проектировщику;
4. blocking gaps передаются заказчику через оркестратора;
5. реализация начинается только после `AUDIT PASS`.

## 10. Запреты без согласования

Нельзя:

- менять бизнес-логику скидок без ТЗ/ADR;
- удалять legacy `MarketplaceProduct` без миграционного плана;
- автоматически связывать товары WB/Ozon без утверждённого правила;
- считать Excel источником истины без явно утверждённого режима;
- менять права доступа без обновления permissions matrix;
- добавлять UX/functionality веб-панели по догадке;
- раскрывать API-секреты в UI, logs, reports или snapshots;
- смешивать Stage 1, Stage 2 и Stage 3 задачи без явной связки.

## 11. Быстрый вход

За 30 минут:

1. `README.md`
2. `AGENTS.md`
3. `docs/PROJECT_NAVIGATOR.md`
4. `docs/DOCUMENTATION_MAP.md`
5. task-scoped пакет
6. связанные ADR/GAP

За 2 часа дополнительно:

1. профильный stage scope;
2. профильные specs;
3. последние audit/test/release reports по области;
4. regression constraints.

## 12. Обновление документа

Документ обновляется при завершении этапа, изменении архитектурного ядра, добавлении нового модуля, изменении маршрута агентов, появлении/закрытии critical gap или изменении release process.

Ответственный: техрайтер или оркестратор по handoff от исполнителя.
