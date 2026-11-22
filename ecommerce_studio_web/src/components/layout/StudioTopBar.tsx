"use client";

import React, { useState, useEffect } from 'react';
import {
  Sparkles,
  ChevronDown,
  Plus,
  Edit2,
  Download,
  CheckCircle2,
  HelpCircle,
  Settings,
} from 'lucide-react';
import { useStudioStore } from '@/stores/useStudioStore';
import { useConfigStore } from '@/stores/useConfigStore';
import { ModelSettingsDialog } from '@/components/layout/ModelSettingsDialog';
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
} from '@/components/ui/dropdown-menu';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';

export const StudioTopBar: React.FC = () => {
  const {
    currentSession,
    sessionList,
    loadSession,
    createNewSession,
    renameCurrentSession,
  } = useStudioStore();

  const {
    config,
    fetchConfig,
    openSettings,
  } = useConfigStore();

  const [isRenameOpen, setIsRenameOpen] = useState(false);
  const [renameInput, setRenameInput] = useState('');
  const [isTourOpen, setIsTourOpen] = useState(false);

  useEffect(() => {
    fetchConfig();
  }, [fetchConfig]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === ',') {
        e.preventDefault();
        openSettings();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [openSettings]);

  const activeProvider = config?.active_provider || 'gemini';
  const providerTitleMap: Record<string, string> = {
    gemini: 'Gemini',
    openai: 'OpenAI',
    custom_openai: 'Custom Proxy',
    ollama: 'Ollama',
  };
  const providerTitle = providerTitleMap[activeProvider] || 'AI Model';
  const activeModel =
    config?.[activeProvider]?.model ||
    (activeProvider === 'gemini' ? 'gemini-2.0-flash' : 'gpt-4o');
  const isConfigured = config?.[activeProvider]?.is_configured !== false;

  const handleOpenRename = () => {
    setRenameInput(currentSession?.name || '');
    setIsRenameOpen(true);
  };

  const handleSaveRename = async () => {
    if (renameInput.trim()) {
      await renameCurrentSession(renameInput.trim());
      setIsRenameOpen(false);
    }
  };

  const handleCreateNew = async () => {
    await createNewSession();
  };

  const handleExportJson = () => {
    if (!currentSession) return;
    const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(currentSession, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute('href', dataStr);
    downloadAnchor.setAttribute('download', `${currentSession.name || 'studio_session'}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  return (
    <>
      <header className="sticky top-0 z-40 h-14 w-full border-b border-slate-200/80 bg-white/90 backdrop-blur-md px-4 sm:px-6 flex items-center justify-between shadow-xs">
        {/* Left: Brand & Session Switcher */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br from-blue-600 to-indigo-600 shadow-sm shadow-blue-500/25">
              <Sparkles className="h-4 w-4 text-white" />
            </div>
            <span className="font-semibold text-sm tracking-tight text-slate-900 hidden sm:inline">
              Ecommerce Studio
            </span>
            <Badge variant="outline" className="text-[10px] py-0 px-1.5 h-4 font-mono text-slate-500 border-slate-200 bg-slate-50">
              v2.1 Pro
            </Badge>
          </div>

          <div className="h-4 w-px bg-slate-200 mx-1 hidden sm:block" />

          {/* Project Switcher Dropdown */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                size="sm"
                className="h-8 gap-2 px-2.5 text-xs text-slate-700 hover:text-slate-900 border border-slate-200 hover:border-slate-300 bg-slate-50/80 hover:bg-slate-100 rounded-lg max-w-[220px]"
              >
                <span className="truncate font-medium">
                  {currentSession?.name || '未命名商业专案'}
                </span>
                <ChevronDown className="h-3.5 w-3.5 text-slate-400 shrink-0" />
              </Button>
            </DropdownMenuTrigger>

            <DropdownMenuContent align="start" className="w-72">
              <div className="px-2.5 py-2">
                <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                  切换商业专案
                </p>
              </div>

              {sessionList.length > 0 ? (
                sessionList.map((s) => (
                  <DropdownMenuItem
                    key={s.session_id}
                    onClick={() => loadSession(s.session_id)}
                    className="flex items-center justify-between py-2 text-xs"
                  >
                    <div className="flex flex-col truncate pr-2">
                      <span className="font-medium truncate text-slate-800">
                        {s.name}
                      </span>
                      <span className="text-[10px] text-slate-500">
                        {new Date(s.updated_at * 1000).toLocaleDateString()} · {s.images_count || 0} 张成图
                      </span>
                    </div>
                    {currentSession?.session_id === s.session_id && (
                      <CheckCircle2 className="h-3.5 w-3.5 text-blue-600 shrink-0" />
                    )}
                  </DropdownMenuItem>
                ))
              ) : (
                <div className="px-2.5 py-3 text-center text-xs text-slate-400">
                  暂无其他历史专案
                </div>
              )}

              <DropdownMenuSeparator />

              <DropdownMenuItem onClick={handleCreateNew} className="text-xs gap-2 text-blue-600 focus:text-blue-700">
                <Plus className="h-3.5 w-3.5" />
                新建空白商业专案
              </DropdownMenuItem>

              <DropdownMenuItem onClick={handleOpenRename} className="text-xs gap-2 text-slate-700">
                <Edit2 className="h-3.5 w-3.5" />
                重命名当前专案
              </DropdownMenuItem>

              <DropdownMenuItem onClick={handleExportJson} className="text-xs gap-2 text-slate-700">
                <Download className="h-3.5 w-3.5" />
                导出专案配置 JSON
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>

        {/* Right: API Connectivity & Guide */}
        <div className="flex items-center gap-2 sm:gap-2.5">
          <button
            type="button"
            onClick={openSettings}
            title="点击配置 AI 模型与密钥 (快捷键: ⌘, / Ctrl+,)"
            className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-100 hover:bg-slate-200/80 transition-all border border-slate-200 text-[11px] text-slate-700 hover:text-slate-900 cursor-pointer group shadow-xs"
          >
            <span
              className={`h-1.5 w-1.5 rounded-full ${
                isConfigured
                  ? 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.4)] animate-pulse'
                  : 'bg-amber-500'
              }`}
            />
            <span className="max-w-[150px] truncate font-medium">
              {providerTitle} · {activeModel}
            </span>
            <ChevronDown className="h-3 w-3 text-slate-400 group-hover:text-slate-600 transition-colors shrink-0" />
          </button>

          <Button
            variant="ghost"
            size="sm"
            onClick={openSettings}
            className="h-8 w-8 p-0 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg"
            title="模型与提供商设置 (⌘,)"
          >
            <Settings className="h-4 w-4" />
          </Button>

          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsTourOpen(true)}
            className="h-8 gap-1.5 text-xs text-slate-500 hover:text-slate-800 hover:bg-slate-100"
          >
            <HelpCircle className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">工作流指南</span>
          </Button>
        </div>
      </header>

      {/* Rename Dialog */}
      <Dialog open={isRenameOpen} onOpenChange={setIsRenameOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>重命名商业专案</DialogTitle>
            <DialogDescription>
              为当前的电商视觉全案命名，便于后续归档与团队协同。
            </DialogDescription>
          </DialogHeader>
          <div className="py-2">
            <Input
              value={renameInput}
              onChange={(e) => setRenameInput(e.target.value)}
              placeholder="请输入专案名称（如：钛空舱保温杯春季大促）"
              onKeyDown={(e) => e.key === 'Enter' && handleSaveRename()}
            />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="ghost" size="sm" onClick={() => setIsRenameOpen(false)}>
              取消
            </Button>
            <Button variant="studio-accent" size="sm" onClick={handleSaveRename}>
              保存更改
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Quick Tour Modal */}
      <Dialog open={isTourOpen} onOpenChange={setIsTourOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-blue-600" />
              Ecommerce Studio 极速操作指南
            </DialogTitle>
            <DialogDescription>
              从商品资产到商业级全案交付，只需遵循 4 步工业级动线：
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-3 py-2 text-xs leading-relaxed text-slate-600">
            <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 space-y-1">
              <p className="font-semibold text-slate-900">Step 1: 资产录入与特征锁定</p>
              <p className="text-slate-600">输入商品材质定位与解决的客群痛点，上传多张实物图锁定外形与光影反射基准。</p>
            </div>
            <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 space-y-1">
              <p className="font-semibold text-slate-900">Step 2: 9大商业矩阵策划</p>
              <p className="text-slate-600">基于电商黄金转化动线自动策划 9 组镜头语言，支持就地二次润色与灵感补全。</p>
            </div>
            <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 space-y-1">
              <p className="font-semibold text-slate-900">Step 3: 商业出图工坊与非破坏性版本链</p>
              <p className="text-slate-600">一键并发渲染 9 大机位。单图支持任意微调出图（v1/v2/v3...），并可毫秒级一键回滚历史快照！</p>
            </div>
            <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 space-y-1">
              <p className="font-semibold text-slate-900">Step 4: 物料大盘与 750px 手机详情页</p>
              <p className="text-slate-600">以 750px 仿真长图流预览买家滑屏动线，一键导出规范命名的 ZIP 资产包与 Markdown 策划全案。</p>
            </div>
          </div>

          <div className="flex justify-end pt-2">
            <Button variant="studio-accent" size="sm" onClick={() => setIsTourOpen(false)}>
              开始探索
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* AI Model Settings Dialog */}
      <ModelSettingsDialog />
    </>
  );
};
