"use client";

import React, { useState } from 'react';
import {
  Zap,
  Square,
  RectangleVertical,
  RectangleHorizontal,
  Sliders,
  XCircle,
  Clock,
} from 'lucide-react';
import { useStudioStore } from '@/stores/useStudioStore';
import { Button } from '@/components/ui/button';
import { Slider } from '@/components/ui/slider';
import { SSEBatchEvent } from '@/types/api';
import { subscribeSSE } from '@/lib/sse-client';

export const StudioControlBar: React.FC = () => {
  const {
    aspectRatio,
    setAspectRatio,
    concurrency,
    setConcurrency,
    isBatchRendering,
    batchProgress,
    setBatchRenderingState,
    setSingleCardStatus,
    addNewVersionSnapshot,
    currentSession,
  } = useStudioStore();

  const [abortController, setAbortController] = useState<AbortController | null>(null);

  const handleStartBatchRender = async () => {
    if (!currentSession?.session_id || isBatchRendering) return;

    const controller = new AbortController();
    setAbortController(controller);

    setBatchRenderingState(true, {
      total: 9,
      completed: 0,
      etaSeconds: 30,
      currentRunningIds: currentSession.perspectives.map((p) => p.id),
    });

    // Mark all cards as rendering
    currentSession.perspectives.forEach((p) => {
      setSingleCardStatus(p.id, 'rendering', 10);
    });

    try {
      subscribeSSE<SSEBatchEvent>(
        '/api/v1/studio/render-batch',
        {
          session_id: currentSession.session_id,
          aspect_ratio: aspectRatio,
          concurrency: concurrency,
        },
        {
          onMessage: (event, data) => {
            if (event === 'perspective_done' || data?.event === 'perspective_done') {
              const pid = data.perspective_id;
              if (pid && data.version) {
                addNewVersionSnapshot(pid, data.version);
                setSingleCardStatus(pid, 'success', 100);
              }
            } else if (event === 'progress' || data?.event === 'progress') {
              setBatchRenderingState(true, {
                completed: data.completed || 0,
                total: data.total || 9,
                etaSeconds: data.eta_seconds || 15,
              });
            } else if (event === 'batch_complete' || data?.event === 'batch_complete') {
              setBatchRenderingState(false);
            }
          },
          onError: (err) => {
            console.warn('Batch render SSE interrupted, checking progress', err);
            setBatchRenderingState(false);
          },
          onClose: () => {
            setBatchRenderingState(false);
          },
        },
        controller.signal
      );
    } catch (e) {
      console.error('Batch render start error:', e);
      setBatchRenderingState(false);
    }
  };

  const handleStopBatchRender = () => {
    if (abortController) {
      abortController.abort();
      setAbortController(null);
    }
    setBatchRenderingState(false);
  };

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

        {/* Concurrency Slider */}
        <div className="flex items-center gap-2.5 min-w-[140px]">
          <div className="flex items-center gap-1 text-xs text-zinc-400">
            <Sliders className="h-3.5 w-3.5 text-zinc-500" />
            <span>并发:</span>
            <span className="font-mono text-zinc-200 font-bold">{concurrency}</span>
            <span className="text-[10px] text-zinc-500">线程</span>
          </div>
          <div className="w-20">
            <Slider
              value={[concurrency]}
              min={1}
              max={5}
              step={1}
              onValueChange={(val) => setConcurrency(val[0])}
            />
          </div>
        </div>
      </div>

      {/* Right: Render All Matrix CTA & Progress */}
      <div className="flex items-center gap-3">
        {isBatchRendering ? (
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 text-xs text-amber-400 bg-amber-500/10 border border-amber-500/20 px-3 py-1.5 rounded-lg">
              <span className="h-2 w-2 rounded-full bg-amber-400 animate-ping" />
              <span>
                正在并发拍摄 ({batchProgress.completed}/{batchProgress.total})...
              </span>
              <span className="text-zinc-400 font-mono text-[11px] flex items-center gap-1">
                <Clock className="h-3 w-3" /> 约 {batchProgress.etaSeconds}s
              </span>
            </div>

            <Button
              variant="destructive"
              size="sm"
              onClick={handleStopBatchRender}
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
            onClick={handleStartBatchRender}
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
