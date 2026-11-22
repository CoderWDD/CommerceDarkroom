import {
  PerspectiveVersion,
  Perspective,
  PerspectiveItem,
  QuickTweakItem,
  ProductDossier,
  ProductDossierExtracted,
  StudioSession,
  StylePreset,
  StylePresetId,
  VisionExtractDossierResponse,
} from './session';

export type {
  StylePresetId,
  StylePreset,
  ProductDossierExtracted,
  VisionExtractDossierResponse,
  Perspective,
  PerspectiveItem,
  QuickTweakItem,
};

export interface CreateSessionRequest {
  name?: string;
  product_info?: Partial<ProductDossier>;
  style_preset?: StylePresetId | string;
}

export interface PlanMatrixRequest {
  session_id: string;
  product_info: ProductDossier;
  style_preset?: StylePresetId | string;
  stream?: boolean;
}

export interface VisionExtractDossierRequest {
  session_id?: string;
  asset_url?: string;
  asset_path?: string;
  category_hint?: string;
}

export interface RefinePromptRequest {
  session_id: string;
  perspective_id: string;
  instruction?: string;
  current_prompt?: string;
}

export interface RefinePromptResponse {
  refined_prompt: string;
}

export interface RegeneratePerspectiveScriptRequest {
  session_id?: string;
  perspective_id?: string;
  instruction?: string;
  current_prompt?: string;
}

export interface RegeneratePerspectiveScriptResponse {
  success: boolean;
  session_id?: string;
  perspective_id: string;
  name: string;
  scene_highlight: string;
  commercial_strategy: string;
  prompt_zh: string;
  quick_tweaks?: QuickTweakItem[];
  quick_tweak_pills?: string[];
}

export interface RenderBatchRequest {
  session_id: string;
  perspective_ids?: string[];
  aspect_ratio?: '1:1' | '3:4' | '16:9';
  concurrency?: number;
}

export interface RenderSlotRequest {
  session_id: string;
  perspective_id: string;
  prompt_zh?: string;
  instruction?: string;
  user_feedback?: string;
  change_reason?: string;
  trigger_type?: 'manual_edit' | 'copilot_refine' | 'batch_initial';
  aspect_ratio?: '1:1' | '3:4' | '16:9';
}

export interface RollbackRequest {
  session_id: string;
  perspective_id: string;
  version_id: string | number;
}

export interface RollbackResponse {
  success: boolean;
  active_version_id: string;
  restored_prompt: string;
  image_url: string;
}

export interface CopilotChatRequest {
  session_id: string;
  message: string;
  active_step?: number;
  active_perspective_id?: string | null;
}

export interface SSEBatchEvent {
  event: 'progress' | 'perspective_start' | 'perspective_done' | 'perspective_success' | 'perspective_error' | 'batch_complete' | 'error' | 'ping';
  perspective_id?: string;
  name?: string;
  progress?: number;
  total?: number;
  completed?: number;
  eta_seconds?: number;
  version?: PerspectiveVersion;
  session?: StudioSession;
  error?: string;
  message?: string;
}
