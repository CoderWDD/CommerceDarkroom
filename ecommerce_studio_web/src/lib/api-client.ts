import {
  CreateSessionRequest,
  PlanMatrixRequest,
  RefinePromptRequest,
  RefinePromptResponse,
  RegeneratePerspectiveScriptRequest,
  RegeneratePerspectiveScriptResponse,
  RenderSlotRequest,
  RollbackRequest,
  RollbackResponse,
  CopilotChatRequest,
  VisionExtractDossierResponse,
  StylePreset,
} from '@/types/api';
import { StudioSession, SessionSummary, PerspectiveVersion } from '@/types/session';
import { getApiBaseUrl } from '@/lib/constants';

const getBaseUrl = () => getApiBaseUrl();

async function timedFetch(url: string, init?: RequestInit): Promise<Response> {
  const method = init?.method || 'GET';
  const t0 = Date.now();
  try {
    const res = await fetch(url, init);
    const duration = Date.now() - t0;
    console.log(`⏱️ [Frontend API] ${method} ${url} -> ${res.status} (${duration}ms)`);
    return res;
  } catch (err) {
    const duration = Date.now() - t0;
    console.error(`❌ [Frontend API Error] ${method} ${url} failed after ${duration}ms:`, err);
    throw err;
  }
}

export const studioApi = {
  // 1. 会话列表与管理
  async listSessions(): Promise<SessionSummary[]> {
    try {
      const res = await timedFetch(`${getBaseUrl()}/sessions`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch (e) {
      console.warn('API listSessions failed, falling back to local list', e);
      return [];
    }
  },

  async createSession(payload?: CreateSessionRequest): Promise<StudioSession> {
    const res = await timedFetch(`${getBaseUrl()}/sessions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload || {}),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}: Failed to create session`);
    return await res.json();
  },

  async getSession(sessionId: string): Promise<StudioSession> {
    const res = await timedFetch(`${getBaseUrl()}/sessions/${sessionId}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}: Failed to fetch session`);
    return await res.json();
  },

  async deleteSession(sessionId: string): Promise<boolean> {
    const res = await timedFetch(`${getBaseUrl()}/sessions/${sessionId}`, {
      method: 'DELETE',
    });
    return res.ok;
  },

  async updateSessionName(sessionId: string, name: string): Promise<boolean> {
    const res = await timedFetch(`${getBaseUrl()}/sessions/${sessionId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name }),
    });
    return res.ok;
  },

  // 2. 爆款流派获取
  async getStylePresets(): Promise<StylePreset[]> {
    try {
      const res = await timedFetch(`${getBaseUrl()}/style-presets`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch (e) {
      console.warn('API getStylePresets failed, fallback to local constants', e);
      const { STYLE_PRESETS } = await import('@/lib/constants');
      return STYLE_PRESETS;
    }
  },

  // 3. Step 1: 随手拍多模态逆向建档
  async extractDossier(input: {
    file?: File;
    asset_url?: string;
    session_id?: string;
    category_hint?: string;
  }): Promise<VisionExtractDossierResponse> {
    const baseUrl = getBaseUrl();
    if (input.file) {
      const formData = new FormData();
      formData.append('file', input.file);
      if (input.session_id) formData.append('session_id', input.session_id);
      if (input.category_hint) formData.append('category_hint', input.category_hint);

      const res = await timedFetch(`${baseUrl}/vision/extract-dossier`, {
        method: 'POST',
        body: formData,
      });
      if (!res.ok) {
        let errMsg = `HTTP ${res.status}: 逆向建档多模态解析失败`;
        try {
          const errJson = await res.json();
          if (errJson.detail) errMsg = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail);
        } catch {}
        throw new Error(errMsg);
      }
      return await res.json();
    } else {
      const res = await timedFetch(`${baseUrl}/vision/extract-dossier`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: input.session_id,
          asset_url: input.asset_url,
          category_hint: input.category_hint,
        }),
      });
      if (!res.ok) {
        let errMsg = `HTTP ${res.status}: 逆向建档多模态解析失败`;
        try {
          const errJson = await res.json();
          if (errJson.detail) errMsg = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail);
        } catch {}
        throw new Error(errMsg);
      }
      return await res.json();
    }
  },

  async extractDossierFromPhoto(
    file: File,
    hint?: string,
    sessionId?: string
  ): Promise<VisionExtractDossierResponse> {
    return this.extractDossier({
      file,
      category_hint: hint,
      session_id: sessionId,
    });
  },

  // 4. Step 1: 资产上传与解析 (传统)
  async uploadAsset(sessionId: string, file: File, isPrimary: boolean = false): Promise<{
    id: string;
    url: string;
    vision_tags: string[];
  }> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('is_primary', String(isPrimary));
    const res = await timedFetch(`${getBaseUrl()}/sessions/${sessionId}/assets/upload`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}: Upload failed`);
    return await res.json();
  },

  // 5. Step 1 -> Step 2: 9大商业矩阵推演
  async planMatrix(payload: PlanMatrixRequest): Promise<StudioSession> {
    const res = await timedFetch(`${getBaseUrl()}/plan`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}: Planning matrix failed`);
    return await res.json();
  },

  async planSession(payload: PlanMatrixRequest): Promise<StudioSession> {
    return this.planMatrix(payload);
  },

  // 6. Step 2: 策划案灵感润色 (AI Magic Refiner)
  async refinePrompt(payload: RefinePromptRequest): Promise<RefinePromptResponse> {
    const res = await timedFetch(`${getBaseUrl()}/refine-prompt`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      let errMsg = `HTTP ${res.status}: Prompt refinement failed`;
      try {
        const errJson = await res.json();
        if (errJson.detail) errMsg = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail);
      } catch {}
      throw new Error(errMsg);
    }
    return await res.json();
  },

  // 6.1 Step 2: 单卡 AI 视觉导演全自主重新构思 (Reimagine Perspective)
  async regeneratePerspectiveScript(
    payload: RegeneratePerspectiveScriptRequest
  ): Promise<RegeneratePerspectiveScriptResponse> {
    const sid = payload.session_id;
    const pid = payload.perspective_id;
    const url = sid && pid
      ? `${getBaseUrl()}/sessions/${sid}/perspectives/${pid}/regenerate-script`
      : `${getBaseUrl()}/regenerate-perspective-script`;
    const res = await timedFetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      let errMsg = `HTTP ${res.status}: Perspective script regeneration failed`;
      try {
        const errJson = await res.json();
        if (errJson.detail) errMsg = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail);
      } catch {}
      throw new Error(errMsg);
    }
    return await res.json();
  },

  // 7. Step 3: 单镜头微调渲染 (产出新版本快照与完整同步会话)
  async renderSlot(payload: RenderSlotRequest): Promise<{
    success: boolean;
    perspective_id: string;
    version: PerspectiveVersion;
    session?: StudioSession;
  }> {
    const res = await timedFetch(`${getBaseUrl()}/refine-slot`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      let errMsg = `HTTP ${res.status}: Slot rendering failed`;
      try {
        const errJson = await res.json();
        if (errJson.detail) errMsg = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail);
      } catch {}
      throw new Error(errMsg);
    }
    const data = await res.json();
    const versionObj = data.version || data;
    return {
      success: data.success ?? true,
      perspective_id: data.perspective_id || payload.perspective_id,
      version: versionObj,
      session: data.session,
    };
  },

  // 8. Step 3: 版本回滚
  async rollbackVersion(payload: RollbackRequest): Promise<RollbackResponse> {
    const res = await timedFetch(`${getBaseUrl()}/rollback`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      let errMsg = `HTTP ${res.status}: Rollback failed`;
      try {
        const errJson = await res.json();
        if (errJson.detail) errMsg = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail);
      } catch {}
      throw new Error(errMsg);
    }
    return await res.json();
  },

  // 9. 首席顾问对话
  async copilotChat(payload: CopilotChatRequest): Promise<{
    reply: string;
    action_chip?: {
      target_perspective_id: string;
      suggested_prompt: string;
      label: string;
    };
  }> {
    const res = await timedFetch(`${getBaseUrl()}/copilot/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}: Copilot chat failed`);
    return await res.json();
  },

  // 10. 交付下载链接
  getZipExportUrl(sessionId: string): string {
    return `${getBaseUrl()}/sessions/${sessionId}/export/zip`;
  },

  getMarkdownExportUrl(sessionId: string): string {
    return `${getBaseUrl()}/sessions/${sessionId}/export/markdown`;
  },
};
