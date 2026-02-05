# BLOCK 18 — UI Module SDK / Template

Платформенный стандарт для всех статических UI-модулей во frontend.

## Обязательная структура
Каждый модуль создаётся в папке `frontend/src/modules/<modulePath>/` и обязан содержать:
- `<ModuleName>Module.tsx`
- `index.ts`
- `README.md`

Где `<modulePath>` строго равен `module.path` из backend registry.

## SDK-контракт UI-модуля
UI-модуль — это только React-компонент отображения.

Разрешено:
- локальный UI state;
- рендеринг пользовательского интерфейса;
- получение platform props в будущем.

Запрещено:
- прямые API-запросы;
- RBAC/permissions-логика;
- знание о routing/sidebar/registry;
- импорт `ModuleContainer`/`ModuleFallback`;
- навигация.

## Правила регистрации (React-registry)
- `moduleRegistry` хранит только React-компоненты;
- ключ registry === `module.path` из backend;
- без условий, без вычислений, без бизнес-логики.

## Диагностика
Обязательная диагностика выполняется в `ModuleContainer`:
- `modulePath` из route;
- список доступных modules;
- `resolvedModule`;
- имя/ключ рендеримого компонента.

UI-модули могут логировать только собственную инициализацию.

## Как создать новый модуль через Codex, не ломая платформу
1. Создайте папку `frontend/src/modules/<modulePath>/`.
2. Добавьте `<ModuleName>Module.tsx` по SDK-контракту (только UI).
3. Добавьте `index.ts` с `export { default } from "./<ModuleName>Module";`.
4. Добавьте `README.md` с обязательными разделами (назначение, path, доступ, ограничения, prompt, инструкция).
5. Зарегистрируйте модуль в `frontend/src/modules/registry.ts` простым соответствием ключа и компонента.
6. Не изменяйте `ModuleContainer`, маршруты, RBAC и `ModuleFallback`.
