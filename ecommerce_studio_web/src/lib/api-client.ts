import {
  CreateSessionRequest,
  PlanMatrixRequest,
  RefinePromptRequest,
  RefinePromptResponse,
  RenderSlotRequest,
  RollbackRequest,
  RollbackResponse,
  CopilotChatRequest,
} from '@/types/api';
import { StudioSession, SessionSummary, PerspectiveVersion } from '@/types/session';

const BASE_URL = '/api/v1/studio';

export const studioApi = {
  // 1. 会话列表与管理
  async listSessions(): Promise<SessionSummary[]> {
    try {
      const res = await fetch(`${BASE_URL}/sessions`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch (e) {
      console.warn('API listSessions failed, falling back to local list', e);
      return [];
    }
  },

  async createSession(payload?: CreateSessionRequest): Promise<StudioSession> {
    const res = await fetch(`${BASE_URL}/sessions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload || {}),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}: Failed to create session`);
    return await res.json();
  },

  async getSession(sessionId: string): Promise<StudioSession> {
    const res = await fetch(`${BASE_URL}/sessions/${sessionId}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}: Failed to fetch session`);
    return await res.json();
  },

  async deleteSession(sessionId: string): Promise<boolean> {
    const res = await fetch(`${BASE_URL}/sessions/${sessionId}`, {
      method: 'DELETE',
    });
    return res.ok;
  },

  async updateSessionName(sessionId: string, name: string): Promise<boolean> {
    const res = await fetch(`${BASE_URL}/sessions/${sessionId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name }),
    });
    return res.ok;
  },

  // 2. Step 1: 资产上传与解析
  async uploadAsset(sessionId: string, file: File, isPrimary: boolean = false): Promise<{
    id: string;
    url: string;
    vision_tags: string[];
  }> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('is_primary', String(isPrimary));
    const res = await fetch(`${BASE_URL}/sessions/${sessionId}/assets/upload`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}: Upload failed`);
    return await res.json();
  },

  // 3. Step 1 -> Step 2: 9大商业矩阵推演
  async planMatrix(payload: PlanMatrixRequest): Promise<StudioSession> {
    const res = await fetch(`${BASE_URL}/plan`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}: Planning matrix failed`);
    return await res.json();
  },

  // 4. Step 2: 策划案灵感润色 (AI Magic Refiner)
  async refinePrompt(payload: RefinePromptRequest): Promise<RefinePromptResponse> {
    const res = await fetch(`${BASE_URL}/refine-prompt`, {
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

  // 5. Step 3: 单镜头微调渲染 (产出新版本快照)
  async renderSlot(payload: RenderSlotRequest): Promise<PerspectiveVersion> {
    const res = await fetch(`${BASE_URL}/refine-slot`, {
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
    return data.version || data;
  },

  // 6. Step 3: 版本回滚
  async rollbackVersion(payload: RollbackRequest): Promise<RollbackResponse> {
    const res = await fetch(`${BASE_URL}/rollback`, {
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

  // 7. 首席顾问对话
  async copilotChat(payload: CopilotChatRequest): Promise<{
    reply: string;
    action_chip?: {
      target_perspective_id: string;
      suggested_prompt: string;
      label: string;
    };
  }> {
    const res = await fetch(`${BASE_URL}/copilot/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}: Copilot chat failed`);
    return await res.json();
  },

  // 8. 交付下载链接
  getZipExportUrl(sessionId: string): string {
    return `${BASE_URL}/sessions/${sessionId}/export/zip`;
  },

  getMarkdownExportUrl(sessionId: string): string {
    return `${BASE_URL}/sessions/${sessionId}/export/markdown`;
  },
};
