"use client";

import React from 'react';
import { ArrowLeft, ArrowRight } from 'lucide-react';
import { useStudioStore } from '@/stores/useStudioStore';
import { StudioControlBar } from './StudioControlBar';
import { Perspective3x3Grid } from './Perspective3x3Grid';
import { Button } from '@/components/ui/button';

export const Step3Container: React.FC = () => {
  const { setCurrentStep } = useStudioStore();

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6 space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-zinc-100 flex items-center gap-2">
            <span>Step 3: 商业大片出图工坊 (Master Studio Bench)</span>
          </h2>
          <p className="text-xs text-zinc-400 mt-1">
            一键批量并发渲染 9 大机位商业成图。支持单卡片无损版本微调（v1/v2/v3...）与双向后悔药瞬时回滚。
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setCurrentStep(2)}
            className="text-xs"
          >
            <ArrowLeft className="h-3.5 w-3.5 mr-1" />
            返回矩阵策划
          </Button>

          <Button
            variant="studio-accent"
            size="sm"
            onClick={() => setCurrentStep(4)}
            className="text-xs"
          >
            <span>前往全套交付与长图</span>
            <ArrowRight className="h-3.5 w-3.5 ml-1" />
          </Button>
        </div>
      </div>

      {/* Top Studio Control Bar */}
      <StudioControlBar />

      {/* 3x3 Canvas Grid */}
      <Perspective3x3Grid />
    </div>
  );
};
