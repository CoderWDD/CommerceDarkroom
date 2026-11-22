import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import {
  StudioSession,
  Perspective,
  PerspectiveVersion,
  ProductDossier,
  SessionSummary,
  StylePresetId,
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

  // v2.0 爆款流派与逆向建档状态
  selectedStylePreset: StylePresetId | string;
  isExtractingDossier: boolean;
  extractionProgressText: string;

  // Actions
  setCurrentStep: (step: 1 | 2 | 3 | 4) => void;
  setActivePerspectiveId: (id: string | null) => void;
  setAspectRatio: (ratio: '1:1' | '3:4' | '16:9') => void;
  setConcurrency: (num: number) => void;
  setSession: (session: StudioSession) => void;
  updateProductInfo: (info: Partial<ProductDossier>) => void;
  updatePerspectivePrompt: (perspectiveId: string, promptZh: string) => void;
  updatePerspectiveScript: (perspectiveId: string, scriptData: Partial<Perspective>) => void;

  // v2.0 Actions
  setStylePreset: (presetId: StylePresetId | string) => void;
  extractDossierFromPhoto: (file: File, hint?: string) => Promise<void>;
  extractDossierFromExistingAsset: (assetUrl: string, hint?: string) => Promise<void>;

  // Version Control Actions
  selectPreviewVersion: (perspectiveId: string, versionId: string) => void;
  rollbackVersion: (perspectiveId: string, targetVersionId: string) => Promise<void>;
  addNewVersionSnapshot: (perspectiveId: string, newVersion: PerspectiveVersion) => void;

  // Card Status & Batch Actions
  setSingleCardStatus: (
    perspectiveId: string,
    status: 'idle' | 'rendering' | 'pending' | 'success' | 'error',
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
      concurrency: 1,

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

      // v2.0 初始状态
      selectedStylePreset: 'minimalist_muji',
      isExtractingDossier: false,
      extractionProgressText: '',

      setCurrentStep: (step) => set({ currentStep: step }),

      setActivePerspectiveId: (id) => set({ activePerspectiveId: id }),

      setAspectRatio: (ratio) => set({ aspectRatio: ratio }),

      setConcurrency: () => set({ concurrency: 1 }),

      setStylePreset: (presetId: StylePresetId | string) => {
        set((state) => {
          if (!state.currentSession) return { selectedStylePreset: presetId };
          return {
            selectedStylePreset: presetId,
            currentSession: {
              ...state.currentSession,
              style_preset: presetId,
              updated_at: Math.floor(Date.now() / 1000),
            },
          };
        });
      },

      extractDossierFromPhoto: async (file: File, hint?: string) => {
        let session = get().currentSession;
        if (!session) {
          get().initDefaultSession();
          session = get().currentSession;
        }
        const sessionId = session?.session_id;

        set({
          isExtractingDossier: true,
          extractionProgressText: '多模态大脑正在审视随手拍实物图...',
          error: null,
        });

        const timer1 = setTimeout(() => {
          if (get().isExtractingDossier) {
            set({ extractionProgressText: '正在逆向分析工业材质特征与光学几何...' });
          }
        }, 1200);

        const timer2 = setTimeout(() => {
          if (get().isExtractingDossier) {
            set({ extractionProgressText: '正在萃取客群决策抗拒点与视觉微标签...' });
          }
        }, 2600);

        try {
          const res = await studioApi.extractDossierFromPhoto(file, hint, sessionId);
          clearTimeout(timer1);
          clearTimeout(timer2);

          const current = get().currentSession;
          if (!current) return;

          const updatedRefImages = [...(current.product_info.reference_images || [])];
          const newRef = {
            id: `snap_${Date.now()}`,
            url: res.asset_url,
            is_primary: true,
            vision_tags: res.dossier.visual_tags?.length > 0 ? res.dossier.visual_tags : ['#随手拍逆向', '#实物材质'],
          };
          const finalRefImages = [
            newRef,
            ...updatedRefImages.map((img) => ({ ...img, is_primary: false })),
          ];

          const newDossier: ProductDossier = {
            ...current.product_info,
            name: res.dossier.product_name || current.product_info.name,
            category: res.dossier.category || current.product_info.category,
            material_features: res.dossier.material_features || current.product_info.material_features,
            target_audience: res.dossier.target_users || current.product_info.target_audience,
            pain_points: res.dossier.pain_points || current.product_info.pain_points,
            reference_images: finalRefImages,
            visual_tags: res.dossier.visual_tags || [],
            color_palette: res.dossier.color_palette || [],
          };

          set({
            isExtractingDossier: false,
            extractionProgressText: '建档完成！已智能回填商品档案',
            currentSession: {
              ...current,
              name: res.dossier.product_name ? `${res.dossier.product_name}商业视觉全案` : current.name,
              product_info: newDossier,
              updated_at: Math.floor(Date.now() / 1000),
              // 上传新照片后，清理旧商品视角提示词与成图，准备全新推演
              perspectives: current.perspectives.map((p) => ({
                ...p,
                prompt_zh: '',
                image_path: null,
                image_url: null,
                active_version_id: null,
                active_version: null,
                versions: [],
                render_status: 'idle',
                render_progress: 0,
              })),
            },
          });
        } catch (err: unknown) {
          clearTimeout(timer1);
          clearTimeout(timer2);
          const msg = err instanceof Error ? err.message : '多模态逆向建档失败';
          set({
            isExtractingDossier: false,
            extractionProgressText: '',
            error: msg,
          });
          throw err;
        }
      },

      extractDossierFromExistingAsset: async (assetUrl: string, hint?: string) => {
        const session = get().currentSession;
        if (!session) return;

        set({
          isExtractingDossier: true,
          extractionProgressText: '正在解析指定参考图...',
          error: null,
        });

        try {
          const res = await studioApi.extractDossier({
            asset_url: assetUrl,
            session_id: session.session_id,
            category_hint: hint,
          });

          const current = get().currentSession;
          if (!current) return;

          const newDossier: ProductDossier = {
            ...current.product_info,
            name: res.dossier.product_name || current.product_info.name,
            category: res.dossier.category || current.product_info.category,
            material_features: res.dossier.material_features || current.product_info.material_features,
            target_audience: res.dossier.target_users || current.product_info.target_audience,
            pain_points: res.dossier.pain_points || current.product_info.pain_points,
            visual_tags: res.dossier.visual_tags || [],
            color_palette: res.dossier.color_palette || [],
          };

          set({
            isExtractingDossier: false,
            extractionProgressText: '建档成功',
            currentSession: {
              ...current,
              name: res.dossier.product_name ? `${res.dossier.product_name}商业视觉全案` : current.name,
              product_info: newDossier,
              updated_at: Math.floor(Date.now() / 1000),
              // 上传新照片后，清理旧商品视角提示词与成图，准备全新推演
              perspectives: current.perspectives.map((p) => ({
                ...p,
                prompt_zh: '',
                image_path: null,
                image_url: null,
                active_version_id: null,
                active_version: null,
                versions: [],
                render_status: 'idle',
                render_progress: 0,
              })),
            },
          });
        } catch (err: unknown) {
          const msg = err instanceof Error ? err.message : '参考图解析建档失败';
          set({
            isExtractingDossier: false,
            extractionProgressText: '',
            error: msg,
          });
          throw err;
        }
      },

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

        const activePreset = (session.style_preset as StylePresetId) || get().selectedStylePreset || 'minimalist_muji';

        set({
          currentSession: {
            ...session,
            style_preset: activePreset,
            perspectives,
          },
          selectedStylePreset: activePreset,
          selectedPreviewVersions: selectedVersions,
        });
      },

      updateProductInfo: (info) => {
        const { currentSession } = get();
        if (!currentSession) return;
        const nameChanged = Boolean(info.name && info.name.trim() !== currentSession.product_info.name?.trim());
        set({
          currentSession: {
            ...currentSession,
            name: nameChanged ? `${info.name}商业视觉全案` : currentSession.name,
            updated_at: Math.floor(Date.now() / 1000),
            product_info: {
              ...currentSession.product_info,
              ...info,
            },
            // 若更换了商品名称，清理旧商品残留的历史成图与旧提示词，避免展示混乱
            perspectives: nameChanged
              ? currentSession.perspectives.map((p) => ({
                  ...p,
                  prompt_zh: '',
                  image_path: null,
                  image_url: null,
                  active_version_id: null,
                  active_version: null,
                  versions: [],
                  render_status: 'idle',
                  render_progress: 0,
                }))
              : currentSession.perspectives,
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

      updatePerspectiveScript: (perspectiveId, scriptData) => {
        const { currentSession } = get();
        if (!currentSession) return;

        const updatedPerspectives = currentSession.perspectives.map((p) => {
          if (matchPerspectiveId(p.id, perspectiveId)) {
            return {
              ...p,
              ...scriptData,
              prompt_zh: scriptData.prompt_zh !== undefined ? scriptData.prompt_zh : p.prompt_zh,
            };
          }
          return p;
        });

        const updatedMatrix = currentSession.prompts_matrix?.map((item) => {
          if (matchPerspectiveId(item.id, perspectiveId)) {
            return {
              ...item,
              prompt: scriptData.prompt_zh !== undefined ? scriptData.prompt_zh : item.prompt,
              scene_highlight: scriptData.scene_highlight || item.scene_highlight,
              commercial_strategy: scriptData.commercial_strategy || item.commercial_strategy,
              quick_tweaks: scriptData.quick_tweaks || item.quick_tweaks,
              quick_tweak_pills: scriptData.quick_tweak_pills || item.quick_tweak_pills,
            };
          }
          return item;
        });

        set({
          currentSession: {
            ...currentSession,
            updated_at: Math.floor(Date.now() / 1000),
            perspectives: updatedPerspectives,
            prompts_matrix: updatedMatrix,
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
          if (p.render_status === 'rendering' || p.render_status === 'pending') {
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
        const activePreset = get().selectedStylePreset || 'minimalist_muji';
        try {
          const session = await studioApi.createSession({
            name: sessionName,
            style_preset: activePreset,
          });
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
            style_preset: activePreset,
            product_info: {
              name: '',
              category: '',
              target_audience: '',
              pain_points: '',
              material_features: '',
              reference_images: [],
              visual_tags: [],
              color_palette: [],
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
          style_preset: 'minimalist_muji',
          product_info: {
            name: '智能数显真空气密随行保温杯',
            category: '316L医用不锈钢 / 哑光亲肤磨砂黑 / 触控数显杯盖',
            target_audience: '25-38岁都市白领、商务通勤人士、注重生活质感的咖啡/茶饮爱好者',
            pain_points: '市面竞品保温时长短、放在背包里容易渗水、杯口易烫嘴、瓶身容易刮花掉漆',
            material_features: '316L医用级不锈钢内胆，外壁曜石黑亲肤喷砂烤漆，高精度LED数显触控屏',
            reference_images: [],
            visual_tags: ['#316L医用钢', '#微米级哑光喷砂', '#触控LED冷光数显', '#纯净黑钛调'],
            color_palette: ['#09090B 曜石黑', '#71717A 钛金灰', '#38BDF8 幽蓝冷光'],
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
      version: 2,
      storage: createJSONStorage(() => localStorage),
      migrate: (persistedState: unknown, version: number) => {
        const state = persistedState as {
          currentSession?: StudioSession;
          selectedStylePreset?: StylePresetId | string;
        };
        if (version < 2) {
          if (state?.currentSession && !state.currentSession.style_preset) {
            state.currentSession.style_preset = 'minimalist_muji';
          }
          state.selectedStylePreset = 'minimalist_muji';
        }
        return state as StudioState;
      },
      partialize: (state) => ({
        currentSession: state.currentSession,
        currentStep: state.currentStep,
        selectedStylePreset: state.selectedStylePreset,
        aspectRatio: state.aspectRatio,
        concurrency: state.concurrency,
        selectedPreviewVersions: state.selectedPreviewVersions,
      }),
    }
  )
);
