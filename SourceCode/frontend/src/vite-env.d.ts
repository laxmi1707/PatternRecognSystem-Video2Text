/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string;
  readonly VITE_API_KEY?: string;
  readonly VITE_SOP_DETECTOR_URL?: string;
  /** "true" switches the SOP detector on; anything else leaves it off */
  readonly VITE_SOP_DETECTOR_ENABLED?: string;
}
