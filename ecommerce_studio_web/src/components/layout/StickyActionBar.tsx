"use client";

import React, { useState } from 'react';
import {
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  Copy,
  Check,
  Sparkles,
} from 'lucide-react';
import { useStudioStore } from '@/stores/useStudioStore';
import { Button } from '@/components/ui/button';

export const StickyActionBar: React.FC = () => {
  const { currentStep, setCurrentStep, currentSession } = useStudioStore();
  const [copied, setCopied] = useState(false);

  const handleCopySessionId = () => {
    if (!currentSession?.session_id) return;
    navigator.clipboard.writeText(currentSession.session_id);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const nextStepTitles: Record<number, string> = {
    1: '推演 9 大视觉方案',
    2: '进入 3x3 出图工坊',
    3: '前往物料交付与长图工坊',
    4: '完成定稿导出物料',
  };

  const handleNext = () => {
    if (currentStep < 4) {
      setCurrentStep((currentStep + 1) as 1 | 2 | 3 | 4);
    }
  };

  const handlePrev = () => {
    if (currentStep > 1) {
      setCurrentStep((currentStep - 1) as 1 | 2 | 3 | 4);
    }
  };

  return (
    <div className="fixed bottom-0 left-0 right-0 z-30 h-16 border-t border-white/[0.08] bg-zinc-950/85 backdrop-blur-xl px-4 sm:px-8 flex items-center justify-between">
      {/* Left: Autosave Status & Session ID */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-1.5 text-xs text-zinc-400">
          <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
          <span className="hidden sm:inline">本地已实时存盘</span>
        </div>

        {currentSession?.session_id && (
          <button
            type="button"
            onClick={handleCopySessionId}
            className="hidden md:flex items-center gap-1 px-2 py-0.5 rounded bg-zinc-900 border border-white/10 text-[11px] font-mono text-zinc-400 hover:text-zinc-200 transition-colors"
            title="点击复制会话 ID"
          >
            <span>{currentSession.session_id.substring(0, 16)}...</span>
            {copied ? (
              <Check className="h-3 w-3 text-emerald-400" />
            ) : (
              <Copy className="h-3 w-3 text-zinc-500" />
            )}
          </button>
        )}
      </div>

      {/* Right: Navigation Actions */}
      <div className="flex items-center gap-3">
        {currentStep > 1 && (
          <Button
            variant="outline"
            size="sm"
            onClick={handlePrev}
            className="gap-1.5 text-xs text-zinc-300 hover:text-white"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            上一步
          </Button>
        )}

        {currentStep < 4 ? (
          <Button
            variant="studio-accent"
            size="sm"
            onClick={handleNext}
            className="gap-1.5 text-xs"
          >
            <span>下一步：{nextStepTitles[currentStep]}</span>
            <ArrowRight className="h-3.5 w-3.5" />
          </Button>
        ) : (
          <Button
            variant="studio-accent"
            size="sm"
            onClick={() => {
              // Scroll to export hub or trigger action
              const exportEl = document.getElementById('export-actions-hub');
              if (exportEl) {
                exportEl.scrollIntoView({ behavior: 'smooth' });
              }
            }}
            className="gap-1.5 text-xs"
          >
            <Sparkles className="h-3.5 w-3.5" />
            <span>定稿全套交付 📦</span>
          </Button>
        )}
      </div>
    </div>
  );
};
