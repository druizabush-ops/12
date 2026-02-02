// Типы модуля описывают контракт данных между API и UI.
// Отдельный файл нужен, чтобы Sidebar оставался только отображением.

export type ModuleDto = {
  id: string;
  name: string;
  title?: string;
  path?: string;
  icon?: string | null;
  is_primary?: boolean;
  order?: number;
};

export type Module = {
  id: string;
  name: string;
  title: string;
  path: string;
  icon?: string | null;
  isPrimary: boolean;
  order: number;
};
