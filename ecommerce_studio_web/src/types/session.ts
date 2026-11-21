export interface PerspectiveVersion {
  version_id: string; // "v1", "v2"
  version_num: number;
  image_path?: string;
  image_url?: string;
  prompt_zh: string;
  timestamp: number;
  created_at_fmt: string;
  trigger_type?: 'batch_initial' | 'manual_edit' | 'copilot_refine';
  change_reason?: string;
  aspect_ratio?: '1:1' | '3:4' | '16:9';
  note?: string;
}

export interface Perspective {
  id: string; // "01_white_bg", "02_scene", etc.
  name: string; // "商业纯净白底首图"
  tag: string; // "CTR点击率收割机"
  desc?: string;
  category: '主图转化' | '场景生活' | '材质工艺' | '原理透视' | '痛点消灭' | '尺码参照' | '品牌格调' | '多色矩阵' | '买家社交' | string;
  psychology_target: string;
  prompt_zh: string;
  active_version_id: string | null;
  active_version?: number | null;
  image_path?: string | null;
  image_url?: string | null;
  versions: PerspectiveVersion[];
  
  // 运行时客户端状态 (Transient UI States)
  render_status?: 'idle' | 'rendering' | 'pending' | 'success' | 'error';
  render_progress?: number;
  error_message?: string;
}

export interface ReferenceImage {
  id: string;
  url: string;
  file_path?: string;
  is_primary: boolean;
  vision_tags: string[];
}

export interface ProductDossier {
  name: string;
  category: string;
  target_audience: string;
  pain_points: string;
  material_features?: string;
  reference_images?: ReferenceImage[];
}

export interface StrategySummary {
  tone: string;
  usp: string;
  color_palette: string[];
  overview_text?: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: number;
  action_chip?: {
    target_perspective_id: string;
    suggested_prompt: string;
    label: string;
  };
}

export interface StudioSession {
  schema_version: '2.0';
  session_id: string;
  name: string;
  created_at: number;
  updated_at: number;
  product_info: ProductDossier;
  analysis_result?: string;
  strategy_summary?: StrategySummary;
  prompts_matrix?: Array<{
    id: string;
    name: string;
    desc: string;
    prompt: string;
  }>;
  generated_images?: Array<Record<string, unknown>>;
  perspectives: Perspective[];
  chat_history: ChatMessage[];
}

export interface SessionSummary {
  session_id: string;
  name: string;
  created_at: number;
  updated_at: number;
  product_name: string;
  images_count: number;
  chat_count: number;
}
