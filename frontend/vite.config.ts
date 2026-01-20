// Минимальная конфигурация Vite для React-приложения.
// Файл существует, чтобы фронтенд запускался без дополнительной логики.
// Минимальность — только базовая настройка плагина.

import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
});
