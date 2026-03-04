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
---

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