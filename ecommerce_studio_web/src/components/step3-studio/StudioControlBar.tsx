"use client";

import React from 'react';
import {
  Zap,
  Square,
  RectangleVertical,
  RectangleHorizontal,
  ShieldCheck,
  XCircle,
  Clock,
} from 'lucide-react';
import { useStudioStore } from '@/stores/useStudioStore';
import { useBatchRenderer } from '@/hooks/useBatchRenderer';
import { Button } from '@/components/ui/button';

export const StudioControlBar: React.FC = () => {
  const {
    aspectRatio,
    setAspectRatio,
  } = useStudioStore();

  const {
    isBatchRendering,
    batchProgress,
    startBatchRender,
    stopBatchRender,
  } = useBatchRenderer();

  return (
    <div className="bg-zinc-900/60 backdrop-blur-md border border-white/[0.08] rounded-xl p-4 shadow-xl flex flex-col md:flex-row md:items-center md:justify-between gap-4">
      {/* Left: Aspect Ratio & Concurrency Controls */}
      <div className="flex flex-wrap items-center gap-4 sm:gap-6">
        {/* Aspect Ratio Selector */}
        <div className="flex items-center gap-2">
          <span className="text-xs font-medium text-zinc-400">画幅比例:</span>
          <div className="inline-flex rounded-lg bg-zinc-950/80 p-0.5 border border-white/10 text-xs">
            <button
              type="button"
              onClick={() => setAspectRatio('1:1')}
              className={`flex items-center gap-1 px-2.5 py-1 rounded-md transition-all ${
                aspectRatio === '1:1'
                  ? 'bg-zinc-800 text-sky-400 shadow font-medium'
                  : 'text-zinc-400 hover:text-white'
              }`}
            >
              <Square className="h-3 w-3" />
              <span>1:1 正方</span>
            </button>
            <button
              type="button"
              onClick={() => setAspectRatio('3:4')}
              className={`flex items-center gap-1 px-2.5 py-1 rounded-md transition-all ${
                aspectRatio === '3:4'
                  ? 'bg-zinc-800 text-sky-400 shadow font-medium'
                  : 'text-zinc-400 hover:text-white'
              }`}
            >
              <RectangleVertical className="h-3 w-3" />
              <span>3:4 手机详情</span>
            </button>
            <button
              type="button"
              onClick={() => setAspectRatio('16:9')}
              className={`flex items-center gap-1 px-2.5 py-1 rounded-md transition-all ${
                aspectRatio === '16:9'
                  ? 'bg-zinc-800 text-sky-400 shadow font-medium'
                  : 'text-zinc-400 hover:text-white'
              }`}
            >
              <RectangleHorizontal className="h-3 w-3" />
              <span>16:9 横版海报</span>
            </button>
          </div>
        </div>

        {/* Concurrency Mode (Locked to 1 for 100% Stability & Zero 429 Errors) */}
        <div
          className="flex items-center gap-1.5 px-3 py-1 bg-emerald-500/10 border border-emerald-500/20 rounded-lg text-xs"
          title="限制并发只能为 1，逐张串行布光拍摄，杜绝代理服务商限流与连接中断，保障出图高可用"
        >
          <ShieldCheck className="h-3.5 w-3.5 text-emerald-400 shrink-0" />
          <span className="text-emerald-300 font-medium">串行保活模式 (并发: 1)</span>
          <span className="text-[10px] text-emerald-400/80 font-mono">· 稳定优先</span>
        </div>
      </div>

      {/* Right: Render All Matrix CTA & Progress */}
      <div className="flex items-center gap-3">
        {isBatchRendering ? (
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 text-xs text-amber-400 bg-amber-500/10 border border-amber-500/20 px-3 py-1.5 rounded-lg">
              <span className="h-2 w-2 rounded-full bg-amber-400 animate-ping" />
              <span>
                正在逐张拍摄 ({batchProgress.completed}/{batchProgress.total})...
              </span>
              <span className="text-zinc-400 font-mono text-[11px] flex items-center gap-1">
                <Clock className="h-3 w-3" /> 约 {batchProgress.etaSeconds}s
              </span>
            </div>

            <Button
              variant="destructive"
              size="sm"
              onClick={stopBatchRender}
              className="text-xs gap-1"
            >
              <XCircle className="h-3.5 w-3.5" />
              终止
            </Button>
          </div>
        ) : (
          <Button
            variant="studio-accent"
            size="sm"
            onClick={startBatchRender}
            className="gap-2 text-xs font-semibold px-4 h-9 shadow-md shadow-sky-500/20"
          >
            <Zap className="h-4 w-4 fill-current text-amber-300" />
            <span>⚡ 一键渲染全套 9 大图</span>
          </Button>
        )}
      </div>
    </div>
  );
};
