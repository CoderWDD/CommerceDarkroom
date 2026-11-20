"use client";

import React, { useState } from 'react';
import { LayoutGrid, Smartphone, ArrowLeft } from 'lucide-react';
import { useStudioStore } from '@/stores/useStudioStore';
import { MasterAssetGrid } from './MasterAssetGrid';
import { MobileDetailPreviewSheet } from './MobileDetailPreviewSheet';
import { ExportActionHub } from './ExportActionHub';
import { Button } from '@/components/ui/button';

export const Step4Container: React.FC = () => {
  const { setCurrentStep } = useStudioStore();
  const [viewMode, setViewMode] = useState<'grid' | 'canvas'>('grid');

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6 space-y-6">
      {/* Header & View Mode Switcher */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-zinc-100 flex items-center gap-2">
            <span>Step 4: 全套物料交付与详情页长图工坊</span>
          </h2>
          <p className="text-xs text-zinc-400 mt-1">
            定稿全套高保真商业大片，在 750px 手机详情页中沉浸式核验视觉节奏与购买转化动线。
          </p>
        </div>

        <div className="flex items-center gap-3">
          {/* Mode Switcher */}
          <div className="inline-flex rounded-lg bg-zinc-900/80 p-0.5 border border-white/10 text-xs">
            <button
              type="button"
              onClick={() => setViewMode('grid')}
              className={`flex items-center gap-1 px-2.5 py-1 rounded-md transition-all ${
                viewMode === 'grid'
                  ? 'bg-zinc-800 text-sky-400 font-medium'
                  : 'text-zinc-400 hover:text-white'
              }`}
            >
              <LayoutGrid className="h-3.5 w-3.5" />
              <span>3x3 矩阵大盘</span>
            </button>
            <button
              type="button"
              onClick={() => setViewMode('canvas')}
              className={`flex items-center gap-1 px-2.5 py-1 rounded-md transition-all ${
                viewMode === 'canvas'
                  ? 'bg-zinc-800 text-sky-400 font-medium'
                  : 'text-zinc-400 hover:text-white'
              }`}
            >
              <Smartphone className="h-3.5 w-3.5" />
              <span>750px 手机详情页长图</span>
            </button>
          </div>

          <Button
            variant="outline"
            size="sm"
            onClick={() => setCurrentStep(3)}
            className="text-xs"
          >
            <ArrowLeft className="h-3.5 w-3.5 mr-1" />
            返回工坊微调
          </Button>
        </div>
      </div>

      {/* Main Preview Area */}
      {viewMode === 'grid' ? <MasterAssetGrid /> : <MobileDetailPreviewSheet />}

      {/* Export Action Hub */}
      <ExportActionHub />
    </div>
  );
};
