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
  Camera,
} from 'lucide-react';
import { useStudioStore } from '@/stores/useStudioStore';
import { useBatchRenderer } from '@/hooks/useBatchRenderer';
import { Button } from '@/components/ui/button';

export const StudioControlBar: React.FC = () => {
  const {
    currentSession,
    aspectRatio,
    setAspectRatio,
  } = useStudioStore();

  const {
    isBatchRendering,
    batchProgress,
    startBatchRender,
    stopBatchRender,
  } = useBatchRenderer();

  const refImages = currentSession?.product_info?.reference_images || [];
  const hasActualRef = refImages.some((img) => (img.asset_type || 'actual') === 'actual');

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-card flex flex-col md:flex-row md:items-center md:justify-between gap-4">
      {/* Left: Aspect Ratio & Concurrency Controls */}
      <div className="flex flex-wrap items-center gap-4 sm:gap-6">
        {/* Aspect Ratio Selector */}
        <div className="flex items-center gap-2">
          <span className="text-xs font-medium text-slate-500">画幅比例:</span>
          <div className="inline-flex rounded-lg bg-slate-100 p-0.5 border border-slate-200/80 text-xs">
            <button
              type="button"
              onClick={() => setAspectRatio('1:1')}
              className={`flex items-center gap-1 px-2.5 py-1 rounded-md transition-all ${
                aspectRatio === '1:1'
                  ? 'bg-white text-blue-700 shadow-xs font-medium'
                  : 'text-slate-600 hover:text-slate-900'
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
                  ? 'bg-white text-blue-700 shadow-xs font-medium'
                  : 'text-slate-600 hover:text-slate-900'
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
                  ? 'bg-white text-blue-700 shadow-xs font-medium'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <RectangleHorizontal className="h-3 w-3" />
              <span>16:9 横版海报</span>
            </button>
          </div>
        </div>

        {/* Reference Image Physical Lock Indicator */}
        {hasActualRef ? (
          <div
            className="flex items-center gap-1.5 px-3 py-1 bg-blue-50 border border-blue-200 rounded-lg text-xs"
            title="已载入产品实拍图作为出图基准，生图时自动注入物理防走样锁模，确保产品外观与实物完全相符"
          >
            <Camera className="h-3.5 w-3.5 text-blue-600 shrink-0" />
            <span className="text-blue-800 font-medium">实拍保真锁模已生效</span>
            <span className="text-[10px] text-blue-600 font-mono">· 杜绝货不对板</span>
          </div>
        ) : (
          <div
            className="flex items-center gap-1.5 px-3 py-1 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-500"
            title="未上传产品实拍图，将基于文字描述渲染"
          >
            <span>纯文生图模式 (无实拍图)</span>
          </div>
        )}

        {/* Concurrency Mode (Locked to 1 for 100% Stability & Zero 429 Errors) */}
        <div
          className="flex items-center gap-1.5 px-3 py-1 bg-emerald-50 border border-emerald-200 rounded-lg text-xs"
          title="限制并发只能为 1，逐张串行布光拍摄，杜绝代理服务商限流与连接中断，保障出图高可用"
        >
          <ShieldCheck className="h-3.5 w-3.5 text-emerald-600 shrink-0" />
          <span className="text-emerald-800 font-medium">串行保活模式 (并发: 1)</span>
          <span className="text-[10px] text-emerald-600 font-mono">· 稳定优先</span>
        </div>
      </div>

      {/* Right: Render All Matrix CTA & Progress */}
      <div className="flex items-center gap-3">
        {isBatchRendering ? (
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 text-xs text-amber-800 bg-amber-50 border border-amber-200 px-3 py-1.5 rounded-lg">
              <span className="h-2 w-2 rounded-full bg-amber-500 animate-ping" />
              <span>
                正在逐张拍摄 ({batchProgress.completed}/{batchProgress.total})...
              </span>
              <span className="text-slate-500 font-mono text-[11px] flex items-center gap-1">
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
            className="gap-2 text-xs font-semibold px-4 h-9 shadow-md shadow-amber-500/20"
          >
            <Zap className="h-4 w-4 fill-current text-white" />
            <span>⚡ 一键渲染全套 9 大图</span>
          </Button>
        )}
      </div>
    </div>
  );
};
