import { create } from 'zustand';
import { ChatMessage } from '@/types/session';
import { studioApi } from '@/lib/api-client';
import { useStudioStore } from './useStudioStore';

interface CopilotState {
  isOpen: boolean;
  isThinking: boolean;
  messages: ChatMessage[];
  unreadCount: number;

  setOpen: (open: boolean) => void;
  toggleOpen: () => void;
  sendMessage: (userText: string) => Promise<void>;
  applyActionChip: (targetPerspectiveId: string, prompt: string) => void;
  clearUnread: () => void;
}

export const useCopilotStore = create<CopilotState>((set, get) => ({
  isOpen: false,
  isThinking: false,
  messages: [
    {
      id: 'welcome_1',
      role: 'assistant',
      content: '主理人您好！我是您的首席商业视觉顾问。我具备全案消费心理学洞察与专业摄影棚机位布光知识。请问您需要优化全案色调、润色特定机位，还是分析点击率抗拒点？',
      timestamp: Date.now(),
    },
  ],
  unreadCount: 0,

  setOpen: (open) => {
    set({ isOpen: open });
    if (open) {
      set({ unreadCount: 0 });
    }
  },

  toggleOpen: () => {
    const next = !get().isOpen;
    set({ isOpen: next });
    if (next) {
      set({ unreadCount: 0 });
    }
  },

  clearUnread: () => set({ unreadCount: 0 }),

  sendMessage: async (userText: string) => {
    if (!userText.trim()) return;

    const userMsg: ChatMessage = {
      id: `msg_u_${Date.now()}`,
      role: 'user',
      content: userText.trim(),
      timestamp: Date.now(),
    };

    set((state) => ({
      messages: [...state.messages, userMsg],
      isThinking: true,
    }));

    const studioState = useStudioStore.getState();
    const sessionId = studioState.currentSession?.session_id || 'default_session';
    const activeStep = studioState.currentStep;
    const activePerspectiveId = studioState.activePerspectiveId;

    try {
      const response = await studioApi.copilotChat({
        session_id: sessionId,
        message: userText,
        active_step: activeStep,
        active_perspective_id: activePerspectiveId,
      });

      const assistantMsg: ChatMessage = {
        id: `msg_a_${Date.now()}`,
        role: 'assistant',
        content: response.reply,
        timestamp: Date.now(),
        action_chip: response.action_chip,
      };

      set((state) => ({
        messages: [...state.messages, assistantMsg],
        isThinking: false,
        unreadCount: state.isOpen ? 0 : state.unreadCount + 1,
      }));
    } catch {
      // Local intelligent response fallback when backend copilot endpoint is offline or warming up
      const currentP = studioState.currentSession?.perspectives.find(
        (p) => p.id === activePerspectiveId
      );
      const pName = currentP?.name || '当前机位';

      const fallbackMsg: ChatMessage = {
        id: `msg_a_${Date.now()}`,
        role: 'assistant',
        content: `针对【${pName}】(${activePerspectiveId || '01_white_bg'})，建议强化光影侧向景深，并增强高光漫反射质感。您可以直接在镜头布景中补充：“85mm微距大光圈，冷金边缘轮廓光勾勒，消除暗角反射”。`,
        timestamp: Date.now(),
        action_chip: activePerspectiveId
          ? {
              target_perspective_id: activePerspectiveId,
              suggested_prompt: `${currentP?.prompt_zh || ''} 85mm商业静物微距特写，冷调轮廓光，细腻漫反射高光，极致工业细节。`.trim(),
              label: `✨ 应用到 ${pName}`,
            }
          : undefined,
      };

      set((state) => ({
        messages: [...state.messages, fallbackMsg],
        isThinking: false,
        unreadCount: state.isOpen ? 0 : state.unreadCount + 1,
      }));
    }
  },

  applyActionChip: (targetPerspectiveId: string, prompt: string) => {
    useStudioStore.getState().updatePerspectivePrompt(targetPerspectiveId, prompt);
  },
}));
