// Типы реестра модулей BLOCK 13.
// UI модулей не реализуется, описываем только контракт данных.

export type PlatformModule = {
  id: string;
  name: string;
  title: string;
  path: string;
  order: number;
  is_primary: boolean;
  has_access: boolean;
  permissions?: Record<string, boolean>;
};

export type ModuleRuntimeProps = {
  permissions?: Record<string, boolean>;
};
