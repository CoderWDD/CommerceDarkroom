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
    1: '进入 9 大矩阵策划',
    2: '前往 3x3 商业出图工坊',
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
    <div className="fixed bottom-0 left-0 right-0 z-30 h-16 border-t border-slate-200/80 bg-white/90 backdrop-blur-xl px-4 sm:px-8 flex items-center justify-between shadow-card">
      {/* Left: Autosave Status & Session ID */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-1.5 text-xs text-slate-500">
          <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" />
          <span className="hidden sm:inline">本地已实时存盘</span>
        </div>

        {currentSession?.session_id && (
          <button
            type="button"
            onClick={handleCopySessionId}
            className="hidden md:flex items-center gap-1 px-2 py-0.5 rounded bg-slate-100 border border-slate-200 text-[11px] font-mono text-slate-600 hover:text-slate-900 transition-colors"
            title="点击复制会话 ID"
          >
            <span>{currentSession.session_id.substring(0, 16)}...</span>
            {copied ? (
              <Check className="h-3 w-3 text-emerald-600" />
            ) : (
              <Copy className="h-3 w-3 text-slate-400" />
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
            className="gap-1.5 text-xs text-slate-700 hover:text-slate-900"
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
