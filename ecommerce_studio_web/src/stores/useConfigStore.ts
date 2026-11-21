import { create } from "zustand";
import { StudioConfig, TestConnectionParams, TestConnectionResult } from "@/types/config";
import { getApiBaseUrl } from "@/lib/constants";

interface ConfigStoreState {
  config: StudioConfig | null;
  isLoading: boolean;
  isSaving: boolean;
  isTesting: boolean;
  testResult: TestConnectionResult | null;
  isSettingsOpen: boolean;

  openSettings: () => void;
  closeSettings: () => void;
  fetchConfig: () => Promise<void>;
  updateConfig: (payload: Partial<StudioConfig>) => Promise<boolean>;
  testConnection: (params: TestConnectionParams) => Promise<TestConnectionResult>;
  resetToDefaults: () => Promise<void>;
}

export const useConfigStore = create<ConfigStoreState>((set, get) => ({
  config: null,
  isLoading: false,
  isSaving: false,
  isTesting: false,
  testResult: null,
  isSettingsOpen: false,

  openSettings: () => {
    set({ isSettingsOpen: true, testResult: null });
    get().fetchConfig();
  },

  closeSettings: () => set({ isSettingsOpen: false, testResult: null }),

  fetchConfig: async () => {
    set({ isLoading: true });
    try {
      const res = await fetch(`${getApiBaseUrl()}/config`);
      if (!res.ok) throw new Error("获取配置失败");
      const data: StudioConfig = await res.json();
      set({ config: data });
    } catch (err) {
      console.error("fetchConfig error:", err);
    } finally {
      set({ isLoading: false });
    }
  },

  updateConfig: async (payload) => {
    set({ isSaving: true });
    try {
      const res = await fetch(`${getApiBaseUrl()}/config`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error("保存配置失败");
      await get().fetchConfig();
      return true;
    } catch (err) {
      console.error("updateConfig error:", err);
      return false;
    } finally {
      set({ isSaving: false });
    }
  },

  testConnection: async (params) => {
    set({ isTesting: true, testResult: null });
    try {
      const res = await fetch(`${getApiBaseUrl()}/config/test`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(params),
      });
      const result: TestConnectionResult = await res.json();
      set({ testResult: result });
      return result;
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : String(err);
      const fallbackResult: TestConnectionResult = {
        success: false,
        provider: params.provider,
        latency_ms: 0,
        message: "前端网关连通异常",
        details: { raw_error: errorMsg },
      };
      set({ testResult: fallbackResult });
      return fallbackResult;
    } finally {
      set({ isTesting: false });
    }
  },

  resetToDefaults: async () => {
    if (typeof window !== "undefined" && !window.confirm("确认重置所有模型配置为出厂默认值吗？")) return;
    try {
      const res = await fetch(`${getApiBaseUrl()}/config/reset`, { method: "POST" });
      if (res.ok) {
        await get().fetchConfig();
        set({ testResult: null });
      }
    } catch (err) {
      console.error("resetToDefaults error:", err);
    }
  },
}));
