# CODEX_MASTER_PROMPT.md
# Расширение «Новый Дом»
# Единый регламент Codex + Архитектурная конституция + Дневник изменений

---

## 0) РЕЖИМ РАБОТЫ CODEX (ОБЯЗАТЕЛЬНО)

Проект уже реализован (BLOCK 11–20+, tasks в продвинутом виде). Репозиторий НЕ пустой.

### 0.1 Алгоритм работы в каждой ветке
1) Прочитать этот документ целиком.
2) Реализовать изменения в коде, соблюдая инварианты и контракты ниже.
3) В ЭТОЙ ЖЕ ВЕТКЕ обновить этот документ:
   - поправить разделы (контракты/правила/инварианты) если они реально изменились
   - добавить запись в “История изменений” (раздел 10) по формату
4) Не ломать структуру документа. Разделы можно расширять, но не “перемешивать”.

### 0.2 Человек в контуре
Коля вручную тестирует ветки и принимает/отклоняет изменения. Codex не “замыкает” процесс сам.

---

## 1) ЖЁСТКИЕ ПРАВИЛА ВЫВОДА ДЛЯ CODEX

Если изменяется код:
- писать только изменения кода/файлов;
- каждый файл отдельным блоком кода;
- первая строка — путь файла комментарием;
- не создавать пустые файлы;
- не добавлять зависимости без необходимости.

Комментарии в коде — ТОЛЬКО на русском языке.

---

## 2) СТАТУС ПРОЕКТА

- Тип: операционная платформа управления магазином
- Backend: FastAPI + SQLAlchemy + Alembic
- Frontend: Vite + React + TypeScript
- DB: PostgreSQL
- Интеграции: Далион Тренд, Frontol 6
- Фокус: роли и операционные процессы (в т.ч. задачи, закупка, контроль)

---

## 3) БАЗОВЫЕ ИНВАРИАНТЫ (НЕ НАРУШАЮТСЯ)

### 3.1 Backend — источник истины
- Бизнес-логика и расчёты: backend.
- Frontend не принимает логических решений.
- RBAC и доступы проверяются backend.

### 3.2 Архитектура модулей (платформа)
Цепочка модулей фиксирована:

/app/modules/:modulePath
→ ModuleContainer
→ GET /modules (backend — источник истины)
→ moduleRegistry (frontend)
→ UI Module
→ ModuleFallback

Запрещено:
- менять ModuleContainer / ModuleFallback ради бизнес-фич
- делать “умный” moduleRegistry (никаких if/switch/вычислений)

Registry — простой `Record<string, Component>`, ключ строго равен module.path. :contentReference[oaicite:5]{index=5}

### 3.3 Роутинг модулей
Внутри /app должен существовать вложенный маршрут:
`modules/:modulePath` → ModuleContainer
(иначе клики из sidebar и прямые URL будут редиректить в /app). :contentReference[oaicite:6]{index=6}

### 3.4 Контракт React Router params
ModuleContainer читает modulePath через `useParams()` (не через props). :contentReference[oaicite:7]{index=7}

---

## 4) AUTH / ENV / CORS (ЗАКРЕПЛЕНО)

### 4.1 Обязательные env для локального старта backend
Backend стартует только при корректной конфигурации окружения.
Минимум:
- DATABASE_URL
- AUTH_SECRET_KEY 

### 4.2 Alembic обязателен
Alembic должен жить в репозитории (alembic.ini + alembic/versions).
Воспроизводимый запуск включает:
`python -m alembic -c alembic.ini upgrade head` перед uvicorn. :contentReference[oaicite:9]{index=9}

### 4.3 Формат /auth/login (не придумывать)
Если backend использует OAuth2PasswordRequestForm:
- POST /auth/login принимает ТОЛЬКО `application/x-www-form-urlencoded`
- JSON отправлять нельзя
- использовать URLSearchParams на фронте 

Если в будущем контракт изменится — это отдельное изменение контракта с записью в истории.

### 4.4 CORS
CORSMiddleware должен быть добавлен ДО подключения роутеров (иначе OPTIONS может ловить 405). 

Рекомендованные параметры для локальной связки:
- allow_origins = ["http://localhost:5173"]
- allow_methods = ["*"]
- allow_headers = ["*"]
- allow_credentials = true

### 4.5 Auth hardening (frontend)
Требования UX/поведения:
- автологин: если токен есть → вызвать /auth/me; до ответа shell не отображать
- 401 в любом защищённом запросе → “Сессия истекла” + logout + редирект /login
- 401 на логине → “Неверный логин или пароль”
- network/500 → “Сервис временно недоступен, попробуйте позже”
- тех. детали только console.error :contentReference[oaicite:12]{index=12}

---

## 5) RBAC И ДОСТУПЫ (МОДУЛЬНЫЕ И ВНУТРИМОДУЛЬНЫЕ)

### 5.1 Module-level access control (BLOCK 16)
Контракт:
- backend отдаёт список модулей и поле `has_access`
- frontend НЕ вычисляет доступ и НЕ знает роли
- если нет доступа → модуль НЕ показывается в sidebar
- при прямом URL без доступа → замок + редирект через fallback (предсказуемо) 

Важно из практики:
- `has_access` обязан быть в ответе, иначе frontend трактует undefined как false → модуль “невидим/недоступен” даже admin. :contentReference[oaicite:14]{index=14}

### 5.2 In-module permissions (BLOCK 19)
Теперь пользователь может иметь:
- has_access=true (модуль видит)
- но разные возможности внутри модуля (permissions)

Контракт:
GET /modules возвращает вместе с модулем `permissions` (объект флагов).
Frontend:
- не вычисляет
- не комбинирует
- не знает ролей
Backend:
- агрегирует permissions по ролям
- модель: “разрешение побеждает запрет” (если хотя бы одна роль разрешает → true). :contentReference[oaicite:15]{index=15}

---

## 6) TASKS — ПРАВИЛА МОДУЛЯ (КРИТИЧНО)

> Этот раздел фиксирует поведение задач. Любые изменения — только осознанно и с записью в историю.

### 6.1 Показ выполненных (done) и сортировка
Поведение:
- выполненные задачи НЕ исчезают, возвращаются всегда (фильтрация вкладками на frontend)
- сортировка в UI:
  1) просроченные
  2) активные
  3) выполненные :contentReference[oaicite:16]{index=16}

### 6.2 is_overdue (строго)
- due_at < now
- status != done
- status != canceled
При этом due_date НЕ изменять (просрочка — это вычисление, не миграция дат). :contentReference[oaicite:17]{index=17}

### 6.3 due_at
Если due_time отсутствует → считать время как 23:59:59. :contentReference[oaicite:18]{index=18}

### 6.4 Calendar counts
GET /tasks/calendar?from=&to=
Возвращает [{date, count}]
count = задачи дня:
- due_date == date
- status != done
- is_hidden == false
Просроченные и выполненные в count не входят. :contentReference[oaicite:19]{index=19}

### 6.5 Выдача задач на день (важный контракт)
GET /tasks?date=YYYY-MM-DD&folder_id=...
- include_done параметр УДАЛИТЬ полностью (не использовать)
- из выдачи исключать is_hidden==true
- логика выдачи:
  1) due_date == выбранный день (is_hidden=false)
  2) + просроченные задачи: due_date < today AND status != done AND is_hidden=false
     просроченные показываются “сегодня” и дальше, пока не done :contentReference[oaicite:20]{index=20}

### 6.6 Attention / Verification
Есть отдельная зона “На проверку” для проверяющего. :contentReference[oaicite:21]{index=21}

Контракт verifier:
- effective_verifier = verifier_user_id OR created_by_user_id
- задача требует проверки → verified_at должен выставляться только effective_verifier

POST /tasks/{id}/verify:
- если verifier_user_id задан → только он
- если verifier_user_id null → создатель (created_by_user_id) :contentReference[oaicite:22]{index=22}

### 6.7 Права PATCH (редактирование)
Редактировать задачу может:
- создатель ИЛИ любой исполнитель (assignee) :contentReference[oaicite:23]{index=23}

### 6.8 Recurring tasks (MVP)
Поля:
- is_recurring (bool)
- recurrence_type: daily | weekly | monthly | yearly
- recurrence_interval (int >= 1)
- recurrence_days_of_week (JSON list[int])
- recurrence_end_date (date)
- recurrence_master_task_id (FK tasks.id)

Создание recurring:
- создать master (is_recurring=True)
- создать дочерние задачи до recurrence_end_date
- лимит максимум 366 задач, иначе HTTP 400 "recurrence_limit_exceeded"
- никаких cron/фоновой генерации :contentReference[oaicite:24]{index=24}

Редактирование recurring (scope как Google Calendar):
PATCH /tasks/{task_id} принимает apply_scope:
- "single"
- "future"
- "master"
Важно: никакого RRULE, никакого cron. :contentReference[oaicite:25]{index=25}

### 6.9 Task Folders (Saved Filters)
TaskFolder:
- id
- name
- created_by_user_id
- filter_json JSON
- created_at
Индекс по created_by_user_id обязателен.

API:
- GET /tasks/folders (только папки текущего пользователя)
- POST /tasks/folders
- PATCH /tasks/folders/{id}
- DELETE /tasks/folders/{id}

filter_json ключи (неизвестные игнорировать):
- assignee_user_id
- verifier_user_id
- urgency
- requires_verification
- status
- source_type

GET /tasks?date=...&folder_id=... применяет filter_json внутри list_tasks_for_date.
Папки доступны только создателю, никакого шаринга. 

---

## 7) UI/UX ИНВАРИАНТЫ SIDEBAR (BLOCK 12)

Collapsed режим:
- icons-only
- фиксированная ширина
- tooltip через data-атрибут
- при сворачивании не “сжимать” текст, а скрывать
- пользователь видит только нужные элементы в collapsed (без “мусорных” значков по решению владельца проекта) *(уточняется в UX-файлах)*

---

## 8) ТЕХНИЧЕСКИЕ ОГРАНИЧЕНИЯ (ЧТО НЕЛЬЗЯ ЛОМАТЬ)

Запрещено без отдельного блока:
- рефакторить shell/routing/auth “просто так”
- менять ModuleContainer/ModuleFallback
- делать логику в registry
- менять RBAC слой
- добавлять тяжёлые зависимости
- плодить дублирующиеся функции/эндпоинты

---

## 9) ЧЕК-ЛИСТ ПЕРЕД PR (ДЛЯ CODEX)

- Инварианты не нарушены (модули/registry/container/auth).
- Контракты /modules и has_access соблюдены.
- Permissions (если затронуты) — только данные, без вычислений на фронте.
- Tasks: overdue/attention/recurring/folders не сломаны.
- Этот документ обновлён и добавлена запись в историю.

---

## 10) ИСТОРИЯ ИЗМЕНЕНИЙ (АРХИТЕКТУРНЫЙ ДНЕВНИК)

Формат:
### [YYYY-MM-DD] — <branch>
Добавлено:
Изменено:
Удалено:
Причина:
Риски/заметки:


### [2026-03-10] — codex/tasks-excel-import-polish
Добавлено:
- UX-полировка предпросмотра Excel импорта задач: типизированные поля (date/time/datetime/number/select), searchable выбор пользователей (creator/assignee/verifier), отображение действия CREATE/UPDATE и расширенная сводка (всего/создано/обновлено/ошибок).
- В генерацию Excel-шаблона добавлены DataValidation для статуса, приоритета, дат/времени и числовых колонок, а также комментарии-подсказки по ключевым полям.
Изменено:
- Поле «Дата выполнения» в импорте отмечено обязательным и валидируется на этапе preview/import с ошибкой уровня строки при отсутствии значения.
- Нормализация приоритета при импорте приведена к UX-списку low/normal/high с маппингом в текущий backend-формат без изменения API контрактов.
Удалено:
- Нет.
Причина:
- Финальная UX-полировка Excel import/export модуля Tasks без изменения backend endpoints, import pipeline и архитектурных инвариантов платформы.
Риски/заметки:
- Приоритет low/high маппится в существующие backend значения normal/very_urgent; контракт Tasks API и recurring-логика не изменялись.

### [2026-03-06] — work
Добавлено:
- Backend API контрагентов: удаление папки `DELETE /counterparties/folders/{folder_id}` с защитой от удаления непустых папок (контрагенты и вложенные папки).
Изменено:
- UX формы create/edit контрагента: убрана дублирующая кнопка-иконка времени, оставлен один штатный `type=time` picker.
- UX панели автозадач: блок «Создатель» убран из постоянной панели и перенесён в модалку create/edit автозадачи; форма выстроена в последовательность «Тип → Название → Автор → Исполнители → День → Время».
- Статус контрагента синхронизирован с архивным состоянием: при архивировании/восстановлении статус в API и таблице отражает `archived/active`.
- Дерево папок: добавлено действие удаления папки из UI с мгновенным обновлением после успешного удаления и пользовательским сообщением при запрете.
Причина:
- Финальная UX-полировка модуля «Контрагенты» без изменения бизнес-логики задач и без регрессий в текущих сценариях.
Риски/заметки:
- Удаление корневой папки «Каталог» в UI по-прежнему запрещено.

### [2026-03-05] — work
Изменено:
- Frontend модуля «Контрагенты»: усилены вертикальные разделители между колонками «Папки | Контрагенты | Карточка | Автозадачи» через border-right 1px var(--border) для более явной визуальной сегментации.
- Таблица списка контрагентов упрощена до двух колонок «Наименование» и «Статус», архивные строки выделяются красным в стиле просроченных задач (danger фон + акцент цвета текста).
- Карточка контрагента: дни недели отображаются как «ПН..ВС» вместо чисел, заголовки секций «Основное / Контакты и доступы / Логистика» выделены цветом темы и underline.
- Форма create/edit контрагента: числовые поля дней недели заменены select с «ПН..ВС», поле «Дедлайн заявки» переведено на type=time и дополнено кнопкой-иконкой часов для открытия стандартного time picker.
Причина:
- Довести UX контрагентов до финального состояния по визуальной читаемости, скорости ввода и единообразию отображения бизнес-данных без изменения backend/API.
Риски/заметки:
- Браузеры без поддержки showPicker используют fallback через focus в поле времени.
### [2026-03-05] — work
Изменено:
- Frontend модуля «Контрагенты»: зафиксирован 4-колоночный layout 260px | 340px | flex | 340px с визуальными вертикальными разделителями (1px var(--border)), заголовками колонок и независимым скроллом каждой зоны.
- Панель автозадач: создание/редактирование правила вынесено в modal через кнопку «Создать автозадачу», список правил уплотнён в карточки с ключевой информацией и действиями edit/delete.
- Из UI автозадач удалены inline-кнопки pause/resume/stop, сохранены операции редактирования и удаления правила.
Причина:
- Финальная полировка UX модуля «Контрагенты» для чёткого разделения контекста (папки, список, карточка, автозадачи) и снижения визуальной перегрузки.
Риски/заметки:
- Сборка frontend в текущем окружении может быть недоступна без доступа к npm registry (ограничение политики).



### [2026-03-05] — codex/polish-counterparties-autotasks-ux-v1.1
Добавлено:
- API удаления правила автозадач: DELETE /counterparties/{counterparty_id}/auto-tasks/{rule_id} c ответом 204 No Content без response body.
- Frontend AutoTasks UX v1.1: карточки правил в стиле Tasks, иконки действий edit/pause/resume/stop/delete, confirm при удалении, inline status-бейджи 🟢/🟡/⚫.
Изменено:
- Сервис counterparties: soft-delete правила через state="deleted", исключение deleted из list/операций, остановка master recurring при delete с очисткой будущих неделанных дочерних задач.
- Frontend форма автоправил: time picker с очисткой, дни недели ПН..ВС, 4 визуально разделённые колонки, loading + toast + refetch после операций.
- Общий apiFetch: корректная обработка 204 и non-JSON ответов без падения response.json().
Причина:
- Устранить регрессию FastAPI/HTTP 204 и довести UX управления автоправилами контрагентов до рабочего состояния без ручных точечных правок.
Риски/заметки:
- Полная проверка alembic upgrade head требует PostgreSQL; в SQLite окружении часть старых миграций (0008) не поддерживается из-за ограничений ALTER CONSTRAINT.

### [2026-03-05] — counterparties-autotasks-v1
Добавлено:
- Counterparties AutoTasks v1: отдельные правила MAKE_ORDER/SEND_ORDER, rolling ensure горизонта 15 дней без cron, источники задач source_module/source_counterparty_id/source_trigger_id.
- Настройка counterparties.task_creator_user_id и API управления состояниями правила (pause/resume/stop).
Изменено:
- API контрагентов для автозадач переведён на /counterparties/{id}/auto-tasks и PATCH с action=keep|replace при смене расписания.
- Frontend 4-й колонки «Автозадачи»: список правил, создание, смена статусов, keep/replace при изменении расписания.
Причина:
- Нужен управляемый rolling-план задач поставщикам на 15 дней вперёд с сохранением истории выполнения в Tasks recurring-модели.
Риски/заметки:
- Миграция 0012 не содержит downgrade; при rollout требуется прямой путь upgrade.

### [2026-03-03] — work
Добавлено:
- BLOCK COUNTERPARTIES v1 (дерево, карточка, архив, автозадачи через recurring Tasks)
Причина:
- запуск базы поставщиков и напоминаний без внедрения cron/движка триггеров
Риски/заметки:
- опора на лимит 366 и recurrence_end_date; возможный Trigger Engine v2 при необходимости

### [2026-03-03] — constitution/v1.1
Добавлено:
- Расширенные правила по tasks (выдача, overdue, recurring scopes, folders)
- Зафиксированы контракты RBAC (has_access) и in-module permissions
- Зафиксированы правила auth (env, form-urlencoded login, CORS до роутеров, hardening UX)
Причина:
- Реальные правила уже реализованы и должны быть защищены от регрессий


### [2026-03-04] — counterparties-ux-v2.2-4col
Изменено:
- Frontend counterparties переведён на 4-колоночный UX: папки, содержимое выбранной папки, viewer карточки, отдельная панель автозадач (read-only placeholder).
- Добавлена стратегия frontend root-folder «Каталог»: гарантируется rootFolderId, исключена отправка folder_id=null при create/edit/move контрагентов.
- Нормализация старых папок в UI: sort_order null -> 0, невалидный parent_id -> rootFolderId для построения дерева без скрытия элементов.
- Поиск ограничен содержимым выбранной папки и фильтрует по name/legal_name/phone/email (case-insensitive).
- В модалке create/edit добавлен опциональный цвет карточки (frontend storage), который применяется к фону viewer.
Причина:
- Упростить рабочий сценарий закупщика и убрать 422-регрессии по folder_id=null без изменения backend API.
Риски/заметки:
- Цвет карточки хранится на frontend (localStorage) и не синхронизируется между устройствами до появления backend-поля.

### [2026-03-04] — counterparties-ux-v2.1-fix-pack
Изменено:
- Frontend модуля counterparties: добавлен UI-root «Каталог», режим «содержимое папки», улучшены drag&drop и поиск, возвращены действия архив/восстановление.
- Карточка контрагента переработана в секции read-only, редактирование оставлено через modal.
- Отображение старых папок и элементов с null sort_order зафиксировано через фронтовую нормализацию в 0.
Причина:
- Устранение UX-регрессий без изменения backend API, routing, RBAC и модуля Tasks.
Риски/заметки:
- Перенос контрагента в root использует текущий API с folder_id=null; поведение зависит от backend-валидации в окружении.
---


### [2026-03-16] — codex/employees-module-e2e
Добавлено:
- Новый модуль «Сотрудники» (backend + frontend) с тремя вкладками: пользователи, оргструктура, роли.
- API для users/organizations/org/groups/org/positions/roles/permissions и endpoint переключения организации `/auth/switch-organization`.
- Новые SQLAlchemy-модели и Alembic-миграция `0013_employees_module` для оргструктуры, ролей, permissions и связей пользователей с организациями/должностями.
Изменено:
- Auth User расширен полями сотрудника (ФИО, телефон, архивность, last_organization_id, timestamps) без поломки существующего user_id/token контракта.
- `/auth/login` переведён на form-urlencoded через `OAuth2PasswordRequestForm` и frontend логин синхронизирован с этим контрактом.
- `/modules` продолжает возвращать `has_access` и `permissions`; для модуля employees добавлена backend-агрегация effective permissions.
Удалено:
- Нет.
Причина:
- Внедрение production-ready админ-модуля сотрудников с сохранением модульной платформы, routing и backend-first RBAC.
Риски/заметки:
- UI модуля «Сотрудники» реализован в существующем стиле и не меняет ModuleContainer/ModuleFallback/registry-инварианты.
- Для полного бизнес-покрытия в следующих итерациях можно расширить интерфейсы create/edit и детальные action-flow по месту использования ролей.

---

## 11) API CONTRACTS (СТРОГО ЗАКРЕПЛЕНО)

Этот раздел фиксирует публичные API-контракты.
Любое изменение структуры ответа, обязательных полей или поведения требует записи в историю (раздел 10).

---

### 11.1 Modules API

GET /modules  
Возвращает список модулей с полями:

- id
- name
- path
- has_access (bool) — ОБЯЗАТЕЛЬНО
- permissions (object | null)

Инварианты:
- has_access обязан присутствовать всегда.
- permissions обязан присутствовать (может быть {}).
- frontend не вычисляет доступ.
- frontend не знает ролей.

⚠ Если has_access отсутствует, frontend трактует undefined как false, и модуль становится недоступным даже для admin.
Это считается критической регрессией.

---

### 11.2 Tasks API (обязательный набор)

GET /tasks?date=YYYY-MM-DD&folder_id=...
- возвращает задачи выбранного дня
- автоматически включает просроченные
- exclude is_hidden == true
- не использует include_done (параметр удалён)

GET /tasks/calendar?from=YYYY-MM-DD&to=YYYY-MM-DD
- возвращает [{ date, count }]
- count включает только:
  - due_date == date
  - status != done
  - is_hidden == false

POST /tasks
- поддерживает создание recurring задач
- при recurring создаёт master + дочерние
- лимит генерации ≤ 366 задач

PATCH /tasks/{id}
- поддерживает apply_scope:
  - "single"
  - "future"
  - "master"

POST /tasks/{id}/complete
- помечает задачу выполненной

POST /tasks/{id}/verify
- доступно только effective_verifier

POST /tasks/{id}/return-active
- возвращает выполненную задачу в active

DELETE /tasks/{id}
- удаляет одну задачу

DELETE /tasks/{id}?scope=future
- удаляет текущую и будущие дочерние

DELETE /tasks/{id}?scope=master
- удаляет всю серию

Инварианты:
- overdue считается динамически
- due_date не переписывается
- логика recurring не использует cron
- никаких RRULE
- фоновой генерации нет

---

### 11.3 Auth API

POST /auth/login
- принимает только application/x-www-form-urlencoded
- JSON запрещён

GET /auth/me
- возвращает профиль пользователя
- используется для автологина

401 в защищённых эндпоинтах:
- frontend обязан выполнить logout

---

### 11.4 RBAC Contract

Backend:
- агрегирует роли пользователя
- рассчитывает has_access
- рассчитывает permissions

Frontend:
- только читает
- ничего не вычисляет
- не знает роли
- не делает fallback-логику по ролям

---
---

## 12) АНТИ-ПАТТЕРНЫ И ИСТОРИЧЕСКИЕ ОШИБКИ (НЕ ПОВТОРЯТЬ)

Этот раздел фиксирует реальные баги, которые уже происходили.
Повторение считается архитектурной регрессией.

---

### 12.1 Отсутствие has_access в /modules

Симптом:
- модуль не отображается даже для admin

Причина:
- has_access отсутствует в ответе
- frontend трактует undefined как false

Решение:
- has_access обязателен
- permissions обязателен

---

### 12.2 Логика в moduleRegistry

Симптом:
- registry содержит условия
- registry содержит вычисления
- registry зависит от ролей

Причина:
- попытка перенести RBAC на frontend

Решение:
- registry — тупой объект соответствий
- логика доступа только backend

---

### 12.3 Изменение ModuleContainer ради фич

Симптом:
- ModuleContainer начинает содержать бизнес-логику
- появляются props, лишние состояния, useMemo без необходимости

Решение:
- ModuleContainer — диспетчер
- бизнес-логика в модуле

---

### 12.4 Нарушение form-urlencoded при логине

Симптом:
- 422 / 400 при логине

Причина:
- отправка JSON вместо form-urlencoded

Решение:
- использовать URLSearchParams
- строго следовать контракту OAuth2PasswordRequestForm

---

### 12.5 CORS добавлен после роутеров

Симптом:
- OPTIONS → 405

Причина:
- CORSMiddleware подключён после include_router

Решение:
- middleware добавляется до подключения роутеров

---

### 12.6 Изменение due_date вместо расчёта overdue

Симптом:
- просроченные задачи “переписывают” дату

Причина:
- путаница между due_date и overdue

Решение:
- overdue — вычисляемое состояние
- due_date не изменяется

---

### 12.7 include_done в Tasks API

Симптом:
- расхождение поведения календаря и списка

Причина:
- попытка фильтровать done через query-параметр

Решение:
- include_done удалён из контракта
- фильтрация done — ответственность frontend вкладок

---

### 12.8 Попытка реализовать recurring через cron

Симптом:
- сложность поддержки
- рассинхронизация master и дочерних задач

Решение:
- recurring генерируется сразу
- лимит 366
- никаких фоновых задач

---



# КОНЕЦ ДОКУМЕНТА
