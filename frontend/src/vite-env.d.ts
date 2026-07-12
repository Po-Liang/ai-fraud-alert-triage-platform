/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string;
  readonly VITE_DEMO_MODE?: "nttdata" | "insurance";
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
