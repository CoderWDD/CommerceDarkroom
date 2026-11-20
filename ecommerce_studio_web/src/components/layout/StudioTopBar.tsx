"use client";

import React, { useState } from 'react';
import {
  Sparkles,
  ChevronDown,
  Plus,
  Edit2,
  Download,
  CheckCircle2,
  HelpCircle,
} from 'lucide-react';
import { useStudioStore } from '@/stores/useStudioStore';
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

  const [isRenameOpen, setIsRenameOpen] = useState(false);
  const [renameInput, setRenameInput] = useState('');
  const [isTourOpen, setIsTourOpen] = useState(false);

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
      <header className="sticky top-0 z-40 h-14 w-full border-b border-white/[0.08] bg-zinc-950/80 backdrop-blur-xl px-4 sm:px-6 flex items-center justify-between">
        {/* Left: Brand & Session Switcher */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br from-sky-500 to-indigo-600 shadow-sm shadow-sky-500/30">
              <Sparkles className="h-4 w-4 text-white" />
            </div>
            <span className="font-semibold text-sm tracking-tight text-zinc-100 hidden sm:inline">
              Ecommerce Studio
            </span>
            <Badge variant="outline" className="text-[10px] py-0 px-1.5 h-4 font-mono text-zinc-400">
              v2.1 Pro
            </Badge>
          </div>

          <div className="h-4 w-px bg-white/10 mx-1 hidden sm:block" />

          {/* Project Switcher Dropdown */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                size="sm"
                className="h-8 gap-2 px-2.5 text-xs text-zinc-300 hover:text-white border border-white/5 hover:border-white/15 bg-zinc-900/40 rounded-lg max-w-[220px]"
              >
                <span className="truncate font-medium">
                  {currentSession?.name || '未命名商业专案'}
                </span>
                <ChevronDown className="h-3.5 w-3.5 text-zinc-500 shrink-0" />
              </Button>
            </DropdownMenuTrigger>

            <DropdownMenuContent align="start" className="w-72">
              <div className="px-2.5 py-2">
                <p className="text-[11px] font-semibold text-zinc-400 uppercase tracking-wider">
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
                      <span className="font-medium truncate text-zinc-200">
                        {s.name}
                      </span>
                      <span className="text-[10px] text-zinc-500">
                        {new Date(s.updated_at * 1000).toLocaleDateString()} · {s.images_count || 0} 张成图
                      </span>
                    </div>
                    {currentSession?.session_id === s.session_id && (
                      <CheckCircle2 className="h-3.5 w-3.5 text-sky-400 shrink-0" />
                    )}
                  </DropdownMenuItem>
                ))
              ) : (
                <div className="px-2.5 py-3 text-center text-xs text-zinc-500">
                  暂无其他历史专案
                </div>
              )}

              <DropdownMenuSeparator />

              <DropdownMenuItem onClick={handleCreateNew} className="text-xs gap-2 text-sky-400 focus:text-sky-300">
                <Plus className="h-3.5 w-3.5" />
                新建空白商业专案
              </DropdownMenuItem>

              <DropdownMenuItem onClick={handleOpenRename} className="text-xs gap-2 text-zinc-300">
                <Edit2 className="h-3.5 w-3.5" />
                重命名当前专案
              </DropdownMenuItem>

              <DropdownMenuItem onClick={handleExportJson} className="text-xs gap-2 text-zinc-300">
                <Download className="h-3.5 w-3.5" />
                导出专案配置 JSON
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>

        {/* Right: API Connectivity & Guide */}
        <div className="flex items-center gap-2 sm:gap-3">
          <div className="hidden md:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-[11px] text-emerald-400">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
            <span>Gemini Imagen Active</span>
          </div>

          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsTourOpen(true)}
            className="h-8 gap-1.5 text-xs text-zinc-400 hover:text-zinc-200"
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
              <Sparkles className="h-4 w-4 text-sky-400" />
              Ecommerce Studio 极速操作指南
            </DialogTitle>
            <DialogDescription>
              从商品资产到商业级全案交付，只需遵循 4 步工业级动线：
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-3 py-2 text-xs leading-relaxed text-zinc-300">
            <div className="p-3 rounded-lg bg-zinc-900/60 border border-white/5 space-y-1">
              <p className="font-semibold text-zinc-100">Step 1: 资产录入与特征锁定</p>
              <p className="text-zinc-400">输入商品材质定位与解决的客群痛点，上传多张实物图锁定外形与光影反射基准。</p>
            </div>
            <div className="p-3 rounded-lg bg-zinc-900/60 border border-white/5 space-y-1">
              <p className="font-semibold text-zinc-100">Step 2: 9大商业矩阵策划</p>
              <p className="text-zinc-400">基于电商黄金转化动线自动策划 9 组镜头语言，支持就地二次润色与灵感补全。</p>
            </div>
            <div className="p-3 rounded-lg bg-zinc-900/60 border border-white/5 space-y-1">
              <p className="font-semibold text-zinc-100">Step 3: 商业出图工坊与非破坏性版本链</p>
              <p className="text-zinc-400">一键并发渲染 9 大机位。单图支持任意微调出图（v1/v2/v3...），并可毫秒级一键回滚历史快照！</p>
            </div>
            <div className="p-3 rounded-lg bg-zinc-900/60 border border-white/5 space-y-1">
              <p className="font-semibold text-zinc-100">Step 4: 物料大盘与 750px 手机详情页</p>
              <p className="text-zinc-400">以 750px 仿真长图流预览买家滑屏动线，一键导出规范命名的 ZIP 资产包与 Markdown 策划全案。</p>
            </div>
          </div>

          <div className="flex justify-end pt-2">
            <Button variant="studio-accent" size="sm" onClick={() => setIsTourOpen(false)}>
              开始探索
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
};
