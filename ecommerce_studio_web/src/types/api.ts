import { PerspectiveVersion, ProductDossier } from './session';

export interface CreateSessionRequest {
  name?: string;
  product_info?: Partial<ProductDossier>;
}

export interface PlanMatrixRequest {
  session_id: string;
  product_info: ProductDossier;
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

export interface RenderBatchRequest {
  session_id: string;
  perspective_ids?: string[];
  aspect_ratio?: '1:1' | '3:4' | '16:9';
  concurrency?: number;
}

export interface RenderSlotRequest {
  session_id: string;
  perspective_id: string;
  prompt_zh: string;
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
  event: 'progress' | 'perspective_done' | 'perspective_error' | 'batch_complete';
  perspective_id?: string;
  progress?: number;
  total?: number;
  completed?: number;
  eta_seconds?: number;
  version?: PerspectiveVersion;
  error?: string;
  message?: string;
}
