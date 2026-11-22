"use client";

import React, { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import {
  Sparkles,
  Zap,
  Globe,
  Server,
  Eye,
  EyeOff,
  CheckCircle2,
  XCircle,
  Loader2,
  RotateCcw,
} from "lucide-react";
import { useConfigStore } from "@/stores/useConfigStore";
import { AIProviderId, ProviderDetailConfig } from "@/types/config";

const PROVIDERS_META: Array<{
  id: AIProviderId;
  name: string;
  desc: string;
  icon: React.ReactNode;
  tag: string;
}> = [
  {
    id: "gemini",
    name: "Google Gemini",
    desc: "原生多模态图文解析与 Imagen 3 工业生图",
    icon: <Sparkles className="h-4 w-4 text-blue-600" />,
    tag: "推荐首选",
  },
  {
    id: "openai",
    name: "OpenAI 官方",
    desc: "GPT-4o 深度策划与 DALL-E 3 视觉渲染",
    icon: <Globe className="h-4 w-4 text-emerald-600" />,
    tag: "全球直连",
  },
  {
    id: "custom_openai",
    name: "兼容中继 / 代理",
    desc: "OneAPI / NewAPI / DeepSeek / 通义千问中转",
    icon: <Zap className="h-4 w-4 text-amber-600" />,
    tag: "国内加速",
  },
  {
    id: "ollama",
    name: "Ollama 本地私有",
    desc: "纯本地运行 Llama-3.2-Vision / Qwen2-VL",
    icon: <Server className="h-4 w-4 text-purple-600" />,
    tag: "隐私安全",
  },
];

const PRESET_MODELS: Record<AIProviderId, { text: string[]; image: string[] }> = {
  gemini: {
    text: ["gemini-2.0-flash", "gemini-2.0-pro-exp", "gemini-1.5-pro", "gemini-1.5-flash"],
    image: ["imagen-3.0-generate-002"],
  },
  openai: {
    text: ["gpt-4o", "gpt-4o-mini", "o1-preview", "gpt-4-turbo"],
    image: ["dall-e-3", "dall-e-2"],
  },
  custom_openai: {
    text: ["deepseek-chat", "deepseek-reasoner", "qwen-vl-max", "gpt-4o", "claude-3-5-sonnet"],
    image: ["dall-e-3", "flux-pro", "flux-schnell"],
  },
  ollama: {
    text: ["llama3.2-vision:latest", "llava:latest", "qwen2-vl:latest"],
    image: ["dall-e-3"],
  },
};

export const ModelSettingsDialog: React.FC = () => {
  const {
    config,
    isSettingsOpen,
    closeSettings,
    updateConfig,
    testConnection,
    isTesting,
    isSaving,
    testResult,
    resetToDefaults,
  } = useConfigStore();

  const [activeTab, setActiveTab] = useState<AIProviderId>("gemini");
  const [showKey, setShowKey] = useState<boolean>(false);
  const [formData, setFormData] = useState<Record<AIProviderId, ProviderDetailConfig>>({
    gemini: { api_key: "", model: "gemini-2.0-flash", image_model: "imagen-3.0-generate-002" },
    openai: { api_key: "", base_url: "https://api.openai.com/v1", model: "gpt-4o", image_model: "dall-e-3" },
    custom_openai: { api_key: "", base_url: "", model: "deepseek-chat", image_model: "dall-e-3" },
    ollama: { api_key: "", base_url: "http://localhost:11434/v1", model: "llama3.2-vision:latest", image_model: "" },
  });

  // 同步远端配置至本地草稿
  useEffect(() => {
    if (config) {
      if (config.active_provider) {
        setActiveTab(config.active_provider);
      }
      setFormData({
        gemini: { ...config.gemini },
        openai: { ...config.openai },
        custom_openai: { ...config.custom_openai },
        ollama: { ...config.ollama },
      });
    }
  }, [config, isSettingsOpen]);

  const currentForm = formData[activeTab] || {
    api_key: "",
    model: "",
    image_model: "",
  };

  const handleFieldChange = (field: keyof ProviderDetailConfig, value: string) => {
    setFormData((prev) => ({
      ...prev,
      [activeTab]: {
        ...prev[activeTab],
        [field]: value,
      },
    }));
  };

  const handleBaseUrlBlur = () => {
    let url = (currentForm.base_url || "").trim();
    if (!url) return;
    // 移除尾部斜杠
    url = url.replace(/\/+$/, "");
    // 补齐 http/https 前缀
    if (!url.startsWith("http://") && !url.startsWith("https://")) {
      if (url.includes("localhost") || url.startsWith("127.0.0.1")) {
        url = `http://${url}`;
      } else {
        url = `https://${url}`;
      }
    }
    handleFieldChange("base_url", url);
  };

  const handleAppendOllamaV1 = () => {
    let url = (currentForm.base_url || "").trim().replace(/\/+$/, "");
    if (!url.endsWith("/v1")) {
      url = `${url}/v1`;
      handleFieldChange("base_url", url);
    }
  };

  const handleRunTest = async () => {
    await testConnection({
      provider: activeTab,
      api_key: currentForm.api_key,
      base_url: currentForm.base_url,
      model: currentForm.model,
      image_model: currentForm.image_model,
    });
  };

  const handleSave = async () => {
    const success = await updateConfig({
      active_provider: activeTab,
      [activeTab]: currentForm,
    });
    if (success) {
      closeSettings();
    }
  };

  return (
    <Dialog open={isSettingsOpen} onOpenChange={(open) => !open && closeSettings()}>
      <DialogContent className="max-w-2xl bg-white border border-slate-200 text-slate-900 p-6 shadow-popover">
        <DialogHeader className="pb-3 border-b border-slate-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="h-8 w-8 rounded-lg bg-blue-50 border border-blue-200 flex items-center justify-center">
                <Sparkles className="h-4 w-4 text-blue-600" />
              </div>
              <div>
                <DialogTitle className="text-base font-semibold tracking-tight text-slate-900">
                  AI 模型引擎与接入设置
                </DialogTitle>
                <DialogDescription className="text-xs text-slate-500 mt-0.5">
                  配置用于商业图文解构、策划及渲染的多模态大模型底座与中继网关
                </DialogDescription>
              </div>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={resetToDefaults}
              className="h-7 text-[11px] text-slate-500 hover:text-slate-800 gap-1 px-2"
              title="重置为系统出厂预设配置"
            >
              <RotateCcw className="h-3 w-3" />
              还原预设
            </Button>
          </div>
        </DialogHeader>

        {/* 1. Provider 单选卡片网格 */}
        <div className="pt-3">
          <Label className="text-xs font-medium text-slate-700 mb-2 block">
            选择当前活跃模型提供商 (Active Provider)
          </Label>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            {PROVIDERS_META.map((p) => {
              const isActive = activeTab === p.id;
              return (
                <button
                  key={p.id}
                  type="button"
                  onClick={() => setActiveTab(p.id)}
                  className={`flex flex-col items-start p-2.5 rounded-lg border text-left transition-all relative ${
                    isActive
                      ? "border-blue-600 bg-blue-50/80 ring-1 ring-blue-500/30"
                      : "border-slate-200 bg-slate-50/50 hover:bg-slate-100 hover:border-slate-300"
                  }`}
                >
                  <div className="flex items-center justify-between w-full mb-1">
                    <span className="p-1 rounded bg-white border border-slate-200/80 shadow-xs">{p.icon}</span>
                    <Badge variant="outline" className="text-[9px] px-1 py-0 h-3.5 border-slate-200 bg-white text-slate-500">
                      {p.tag}
                    </Badge>
                  </div>
                  <span className="text-xs font-semibold text-slate-800">{p.name}</span>
                  <span className="text-[10px] text-slate-500 line-clamp-1 mt-0.5">{p.desc}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* 2. 核心参数表单 */}
        <div className="space-y-3.5 pt-2">
          {/* Base URL (非 Gemini 原生时展示) */}
          {activeTab !== "gemini" && (
            <div className="space-y-1">
              <div className="flex items-center justify-between">
                <Label className="text-xs font-medium text-slate-700">
                  API 端点地址 (Base URL)
                </Label>
                <div className="flex items-center gap-1.5">
                  {activeTab === "ollama" && currentForm.base_url && !currentForm.base_url.endsWith("/v1") && (
                    <button
                      type="button"
                      onClick={handleAppendOllamaV1}
                      className="text-[10px] text-amber-600 hover:text-amber-700 underline font-mono cursor-pointer"
                    >
                      +添加 /v1 适配
                    </button>
                  )}
                  <span className="text-[10px] text-slate-500 font-mono">
                    {activeTab === "ollama" ? "例: http://localhost:11434/v1" : "支持 /v1 规范路径"}
                  </span>
                </div>
              </div>
              <Input
                value={currentForm.base_url || ""}
                onChange={(e) => handleFieldChange("base_url", e.target.value)}
                onBlur={handleBaseUrlBlur}
                placeholder={activeTab === "ollama" ? "http://localhost:11434/v1" : "https://api.your-proxy.com/v1"}
                className="h-8 text-xs bg-white border-slate-200 font-mono text-slate-900 focus:border-blue-500"
              />
            </div>
          )}

          {/* API Key 输入与安全掩码 */}
          <div className="space-y-1">
            <div className="flex items-center justify-between">
              <Label className="text-xs font-medium text-slate-700">
                {activeTab === "ollama" ? "API Key (Ollama 可留空)" : "API 访问密钥 (API Key)"}
              </Label>
              {currentForm.api_key && currentForm.api_key.includes("*") && (
                <span className="text-[10px] text-emerald-600 flex items-center gap-1 font-medium">
                  <CheckCircle2 className="h-3 w-3 text-emerald-600" /> 系统已安全存储脱敏密钥（如不修改无需重输）
                </span>
              )}
            </div>
            <div className="relative">
              <Input
                type={showKey ? "text" : "password"}
                value={currentForm.api_key || ""}
                onChange={(e) => handleFieldChange("api_key", e.target.value)}
                placeholder={currentForm.api_key ? "留空则保留原有已存密钥" : "请输入有效的 API Key..."}
                className="h-8 pr-8 text-xs bg-white border-slate-200 font-mono text-slate-900 focus:border-blue-500"
              />
              <button
                type="button"
                onClick={() => setShowKey(!showKey)}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
              >
                {showKey ? <EyeOff className="h-3.5 w-3.5" /> : <Eye className="h-3.5 w-3.5" />}
              </button>
            </div>
          </div>

          {/* 双槽位模型输入 (自由键入 + 预置候选项列表) */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
            {/* 槽位 1: 多模态策划/思维大脑 */}
            <div className="space-y-1">
              <Label className="text-xs font-medium text-slate-700">
                推理与策划模型 (LLM Model)
              </Label>
              <div className="relative">
                <Input
                  list={`models-${activeTab}`}
                  value={currentForm.model || ""}
                  onChange={(e) => handleFieldChange("model", e.target.value)}
                  placeholder="如: gpt-4o 或 deepseek-chat"
                  className="h-8 text-xs bg-white border-slate-200 font-mono text-slate-900"
                />
                <datalist id={`models-${activeTab}`}>
                  {PRESET_MODELS[activeTab]?.text.map((m) => (
                    <option key={m} value={m} />
                  ))}
                </datalist>
              </div>
              <p className="text-[10px] text-slate-500">支持自由输入任何模型标识</p>
            </div>

            {/* 槽位 2: 商业生图模型 */}
            <div className="space-y-1">
              <Label className="text-xs font-medium text-slate-700">
                商业生图引擎 (Image Model)
              </Label>
              <div className="relative">
                <Input
                  list={`image-models-${activeTab}`}
                  value={currentForm.image_model || ""}
                  onChange={(e) => handleFieldChange("image_model", e.target.value)}
                  placeholder="如: dall-e-3 / imagen-3.0"
                  className="h-8 text-xs bg-white border-slate-200 font-mono text-slate-900"
                />
                <datalist id={`image-models-${activeTab}`}>
                  {PRESET_MODELS[activeTab]?.image.map((m) => (
                    <option key={m} value={m} />
                  ))}
                </datalist>
              </div>
              <p className="text-[10px] text-slate-500">用于渲染商品 3x3 高清主图</p>
            </div>
          </div>

          {/* 3. 连通性测试诊断反馈卡片 */}
          {testResult && (
            <div
              className={`p-2.5 rounded-lg border text-xs transition-all ${
                testResult.success
                  ? "bg-emerald-50 border-emerald-200 text-emerald-800"
                  : "bg-red-50 border-red-200 text-red-800"
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-center gap-1.5 font-medium">
                  {testResult.success ? (
                    <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
                  ) : (
                    <XCircle className="h-4 w-4 text-red-600 shrink-0" />
                  )}
                  <span>{testResult.message}</span>
                </div>
                <Badge variant="outline" className="text-[10px] font-mono h-4 border-current">
                  {testResult.latency_ms} ms
                </Badge>
              </div>
              {testResult.details?.raw_error && (
                <p className="text-[11px] text-red-600 font-mono mt-1 opacity-90 break-all">
                  错误日志: {testResult.details.raw_error}
                </p>
              )}
            </div>
          )}
        </div>

        <DialogFooter className="pt-4 border-t border-slate-200 flex items-center justify-between sm:justify-between">
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={handleRunTest}
            disabled={isTesting}
            className="h-8 gap-1.5 text-xs border-blue-200 text-blue-600 hover:bg-blue-50"
          >
            {isTesting ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Zap className="h-3.5 w-3.5" />}
            {isTesting ? "正在探测端点..." : "测试连通性"}
          </Button>

          <div className="flex items-center gap-2">
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={closeSettings}
              className="h-8 text-xs text-slate-500 hover:text-slate-800"
            >
              取消
            </Button>
            <Button
              type="button"
              variant="studio-accent"
              size="sm"
              onClick={handleSave}
              disabled={isSaving}
              className="h-8 text-xs"
            >
              {isSaving ? <Loader2 className="h-3.5 w-3.5 animate-spin mr-1" /> : null}
              保存并应用
            </Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
