export type AIProviderId = 'gemini' | 'openai' | 'custom_openai' | 'ollama';

export interface ProviderDetailConfig {
  api_key: string;
  base_url?: string;
  model: string;
  image_model?: string;
  is_configured?: boolean;
}

export interface StudioConfig {
  active_provider: AIProviderId;
  gemini: ProviderDetailConfig;
  openai: ProviderDetailConfig;
  custom_openai: ProviderDetailConfig;
  ollama: ProviderDetailConfig;
  system_env_status?: {
    has_gemini_env: boolean;
    has_openai_env: boolean;
  };
}

export interface TestConnectionParams {
  provider: AIProviderId;
  api_key?: string;
  base_url?: string;
  model?: string;
  image_model?: string;
  check_image_model?: boolean;
}

export interface TestConnectionResult {
  success: boolean;
  provider: AIProviderId;
  latency_ms: number;
  message: string;
  error_code?: string;
  details?: {
    auth_ok?: boolean;
    model_responding?: boolean;
    probe_response_excerpt?: string;
    image_model_status?: string;
    raw_error?: string;
  };
}
