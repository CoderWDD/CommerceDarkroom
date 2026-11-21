import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import {
  StudioSession,
  Perspective,
  PerspectiveVersion,
  ProductDossier,
  SessionSummary,
} from '@/types/session';
import { STANDARD_PERSPECTIVES_META } from '@/lib/constants';
import { studioApi } from '@/lib/api-client';

export function matchPerspectiveId(id1?: string | null, id2?: string | null): boolean {
  if (!id1 || !id2) return false;
  if (id1 === id2) return true;
  if (id1.length >= 2 && id2.length >= 2 && id1.substring(0, 2) === id2.substring(0, 2)) {
    return true;
  }
  return false;
}

interface BatchProgress {
  total: number;
  completed: number;
  etaSeconds: number;
  currentRunningIds: string[];
}

interface StudioState {
  currentSession: StudioSession | null;
  currentStep: 1 | 2 | 3 | 4;
  activePerspectiveId: string | null;
  selectedPreviewVersions: Record<string, string>; // perspectiveId -> version_id
  aspectRatio: '1:1' | '3:4' | '16:9';
  concurrency: number;

  isBatchRendering: boolean;
  batchProgress: BatchProgress;

  sessionList: SessionSummary[];
  isLoading: boolean;
  error: string | null;

  // Actions
  setCurrentStep: (step: 1 | 2 | 3 | 4) => void;
  setActivePerspectiveId: (id: string | null) => void;
  setAspectRatio: (ratio: '1:1' | '3:4' | '16:9') => void;
  setConcurrency: (num: number) => void;
  setSession: (session: StudioSession) => void;
  updateProductInfo: (info: Partial<ProductDossier>) => void;
  updatePerspectivePrompt: (perspectiveId: string, promptZh: string) => void;

  // Version Control Actions
  selectPreviewVersion: (perspectiveId: string, versionId: string) => void;
  rollbackVersion: (perspectiveId: string, targetVersionId: string) => Promise<void>;
  addNewVersionSnapshot: (perspectiveId: string, newVersion: PerspectiveVersion) => void;

  // Card Status & Batch Actions
  setSingleCardStatus: (
    perspectiveId: string,
    status: 'idle' | 'rendering' | 'success' | 'error',
    progress?: number,
    errorMsg?: string
  ) => void;
  markAllRenderingAsError: (reason?: string) => void;
  setBatchRenderingState: (rendering: boolean, progress?: Partial<BatchProgress>) => void;

  // Session Lifecycle
  fetchSessionList: () => Promise<void>;
  loadSession: (sessionId: string) => Promise<void>;
  createNewSession: (name?: string) => Promise<string>;
  renameCurrentSession: (newName: string) => Promise<void>;
  deleteSession: (sessionId: string) => Promise<void>;
  initDefaultSession: () => void;
}

export function createInitialPerspectives(): Perspective[] {
  return STANDARD_PERSPECTIVES_META.map((meta) => ({
    ...meta,
    prompt_zh: '',
    active_version_id: null,
    active_version: null,
    image_path: null,
    image_url: null,
    versions: [],
    render_status: 'idle',
    render_progress: 0,
  }));
}

export const useStudioStore = create<StudioState>()(
  persist(
    (set, get) => ({
      currentSession: null,
      currentStep: 1,
      activePerspectiveId: '01_white_bg',
      selectedPreviewVersions: {},
      aspectRatio: '1:1',
      concurrency: 3,

      isBatchRendering: false,
      batchProgress: {
        total: 9,
        completed: 0,
        etaSeconds: 0,
        currentRunningIds: [],
      },

      sessionList: [],
      isLoading: false,
      error: null,

      setCurrentStep: (step) => set({ currentStep: step }),

      setActivePerspectiveId: (id) => set({ activePerspectiveId: id }),

      setAspectRatio: (ratio) => set({ aspectRatio: ratio }),

      setConcurrency: (num) => set({ concurrency: Math.max(1, Math.min(5, num)) }),

      setSession: (session) => {
        // Ensure perspectives are aligned with standard meta
        const perspectives = session.perspectives && session.perspectives.length === 9
          ? session.perspectives
          : createInitialPerspectives();

        // Initialize preview version mappings
        const selectedVersions: Record<string, string> = {};
        perspectives.forEach((p) => {
          if (p.active_version_id) {
            selectedVersions[p.id] = p.active_version_id;
          } else if (p.versions && p.versions.length > 0) {
            selectedVersions[p.id] = p.versions[p.versions.length - 1].version_id;
          }
        });

        set({
          currentSession: {
            ...session,
            perspectives,
          },
          selectedPreviewVersions: selectedVersions,
        });
      },

      updateProductInfo: (info) => {
        const { currentSession } = get();
        if (!currentSession) return;
        set({
          currentSession: {
            ...currentSession,
            updated_at: Math.floor(Date.now() / 1000),
            product_info: {
              ...currentSession.product_info,
              ...info,
            },
          },
        });
      },

      updatePerspectivePrompt: (perspectiveId, promptZh) => {
        const { currentSession } = get();
        if (!currentSession) return;

        const updatedPerspectives = currentSession.perspectives.map((p) => {
          if (p.id === perspectiveId) {
            return { ...p, prompt_zh: promptZh };
          }
          return p;
        });

        set({
          currentSession: {
            ...currentSession,
            updated_at: Math.floor(Date.now() / 1000),
            perspectives: updatedPerspectives,
          },
        });
      },

      selectPreviewVersion: (perspectiveId, versionId) => {
        set((state) => ({
          selectedPreviewVersions: {
            ...state.selectedPreviewVersions,
            [perspectiveId]: versionId,
          },
        }));
      },

      rollbackVersion: async (perspectiveId, targetVersionId) => {
        const { currentSession } = get();
        if (!currentSession) return;

        const targetP = currentSession.perspectives.find((p) => matchPerspectiveId(p.id, perspectiveId));
        if (!targetP) return;

        const targetVersion = targetP.versions.find(
          (v) => String(v.version_id) === String(targetVersionId) || String(v.version_num) === String(targetVersionId)
        );
        if (!targetVersion) return;

        // 乐观更新 (Optimistic UI Update)
        const updatedPerspectives = currentSession.perspectives.map((p) => {
          if (matchPerspectiveId(p.id, perspectiveId)) {
            return {
              ...p,
              active_version_id: targetVersion.version_id,
              active_version: targetVersion.version_num,
              image_url: targetVersion.image_url || p.image_url,
              image_path: targetVersion.image_path || p.image_path,
              prompt_zh: targetVersion.prompt_zh || p.prompt_zh,
            };
          }
          return p;
        });

        set({
          currentSession: {
            ...currentSession,
            perspectives: updatedPerspectives,
            updated_at: Math.floor(Date.now() / 1000),
          },
          selectedPreviewVersions: {
            ...get().selectedPreviewVersions,
            [perspectiveId]: targetVersion.version_id,
            [targetP.id]: targetVersion.version_id,
          },
        });

        // 调用后端 API 持久化回滚状态
        try {
          await studioApi.rollbackVersion({
            session_id: currentSession.session_id,
            perspective_id: perspectiveId,
            version_id: targetVersionId,
          });
        } catch (e) {
          console.error('Backend rollback sync error:', e);
        }
      },

      addNewVersionSnapshot: (perspectiveId, newVersion) => {
        const { currentSession } = get();
        if (!currentSession) return;

        let matchedCardId = perspectiveId;
        const updatedPerspectives = currentSession.perspectives.map((p) => {
          if (matchPerspectiveId(p.id, perspectiveId)) {
            matchedCardId = p.id;
            const exists = p.versions.some((v) => v.version_id === newVersion.version_id);
            const versions = exists
              ? p.versions.map((v) => (v.version_id === newVersion.version_id ? newVersion : v))
              : [...p.versions, newVersion];

            return {
              ...p,
              active_version_id: newVersion.version_id,
              active_version: newVersion.version_num,
              image_url: newVersion.image_url || p.image_url,
              image_path: newVersion.image_path || p.image_path,
              prompt_zh: newVersion.prompt_zh || p.prompt_zh,
              render_status: 'success' as const,
              render_progress: 100,
              error_message: undefined,
              versions,
            };
          }
          return p;
        });

        set({
          currentSession: {
            ...currentSession,
            perspectives: updatedPerspectives,
            updated_at: Math.floor(Date.now() / 1000),
          },
          selectedPreviewVersions: {
            ...get().selectedPreviewVersions,
            [perspectiveId]: newVersion.version_id,
            [matchedCardId]: newVersion.version_id,
          },
        });
      },

      setSingleCardStatus: (perspectiveId, status, progress = 0, errorMsg) => {
        const { currentSession } = get();
        if (!currentSession) return;

        const updatedPerspectives = currentSession.perspectives.map((p) => {
          if (matchPerspectiveId(p.id, perspectiveId)) {
            return {
              ...p,
              render_status: status,
              render_progress: progress,
              error_message: errorMsg,
            };
          }
          return p;
        });

        set({
          currentSession: {
            ...currentSession,
            perspectives: updatedPerspectives,
          },
        });
      },

      markAllRenderingAsError: (reason = '渲染被中止或超时熔断') => {
        const { currentSession } = get();
        if (!currentSession) return;
        const updated = currentSession.perspectives.map((p) => {
          if (p.render_status === 'rendering') {
            return {
              ...p,
              render_status: 'error' as const,
              error_message: reason,
              render_progress: 0,
            };
          }
          return p;
        });
        set({
          isBatchRendering: false,
          currentSession: {
            ...currentSession,
            perspectives: updated,
          },
        });
      },

      setBatchRenderingState: (rendering, progress) => {
        set((state) => ({
          isBatchRendering: rendering,
          batchProgress: {
            ...state.batchProgress,
            ...progress,
          },
        }));
      },

      fetchSessionList: async () => {
        try {
          const list = await studioApi.listSessions();
          set({ sessionList: list });
        } catch (e) {
          console.error('Failed to fetch session list:', e);
        }
      },

      loadSession: async (sessionId: string) => {
        set({ isLoading: true, error: null });
        try {
          const session = await studioApi.getSession(sessionId);
          get().setSession(session);
        } catch (e: unknown) {
          const msg = e instanceof Error ? e.message : '加载会话失败';
          set({ error: msg });
        } finally {
          set({ isLoading: false });
        }
      },

      createNewSession: async (name) => {
        const sessionName = name || `商业策划_${new Date().toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }).replace('/', '')}`;
        try {
          const session = await studioApi.createSession({ name: sessionName });
          get().setSession(session);
          await get().fetchSessionList();
          return session.session_id;
        } catch {
          // Fallback to local session
          const now = Math.floor(Date.now() / 1000);
          const localSession: StudioSession = {
            schema_version: '2.0',
            session_id: `sess_${now}_${Math.random().toString(36).substring(2, 8)}`,
            name: sessionName,
            created_at: now,
            updated_at: now,
            product_info: {
              name: '',
              category: '',
              target_audience: '',
              pain_points: '',
              material_features: '',
              reference_images: [],
            },
            perspectives: createInitialPerspectives(),
            chat_history: [],
          };
          get().setSession(localSession);
          return localSession.session_id;
        }
      },

      renameCurrentSession: async (newName: string) => {
        const { currentSession } = get();
        if (!currentSession) return;
        set({
          currentSession: {
            ...currentSession,
            name: newName,
            updated_at: Math.floor(Date.now() / 1000),
          },
        });
        try {
          await studioApi.updateSessionName(currentSession.session_id, newName);
          await get().fetchSessionList();
        } catch (e) {
          console.warn('Update session name backend error:', e);
        }
      },

      deleteSession: async (sessionId: string) => {
        try {
          await studioApi.deleteSession(sessionId);
          await get().fetchSessionList();
          if (get().currentSession?.session_id === sessionId) {
            get().initDefaultSession();
          }
        } catch (e) {
          console.error('Delete session error:', e);
        }
      },

      initDefaultSession: () => {
        const now = Math.floor(Date.now() / 1000);
        const defaultSession: StudioSession = {
          schema_version: '2.0',
          session_id: `sess_${now}_init`,
          name: '智能数显保温杯商业视觉全案',
          created_at: now,
          updated_at: now,
          product_info: {
            name: '智能数显真空气密随行保温杯',
            category: '316L医用不锈钢 / 哑光亲肤磨砂黑 / 触控数显杯盖',
            target_audience: '25-38岁都市白领、商务通勤人士、注重生活质感的咖啡/茶饮爱好者',
            pain_points: '市面竞品保温时长短、放在背包里容易渗水、杯口易烫嘴、瓶身容易刮花掉漆',
            material_features: '316L医用级不锈钢内胆，外壁曜石黑亲肤喷砂烤漆，高精度LED数显触控屏',
            reference_images: [],
          },
          strategy_summary: {
            tone: '现代极简冷峻精工，商务科技美学',
            usp: '触控看温度，通勤喝热饮更从容',
            color_palette: ['#18181b', '#38bdf8', '#71717a', '#ffffff'],
            overview_text: '以克制科技黑与触控数显为核心记忆点，九张图按“认识产品—看见数显—感受材质—回应顾虑—融入日常”黄金买家动线展开。',
          },
          perspectives: createInitialPerspectives(),
          chat_history: [
            {
              id: 'init_msg_1',
              role: 'assistant',
              content: '主理人您好！我是您的电商视觉首席顾问。我已准备好协助您将商品打造为商业级爆款视觉矩阵。您可以在任意步骤与我讨论镜头打光、消费心理学转化点或微调指令。',
              timestamp: now,
            },
          ],
        };

        get().setSession(defaultSession);
      },
    }),
    {
      name: 'ecommerce-studio-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        currentSession: state.currentSession,
        currentStep: state.currentStep,
        aspectRatio: state.aspectRatio,
        concurrency: state.concurrency,
        selectedPreviewVersions: state.selectedPreviewVersions,
      }),
    }
  )
);
