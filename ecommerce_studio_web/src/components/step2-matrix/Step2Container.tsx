"use client";

import React from 'react';
import { ArrowRight, ArrowLeft } from 'lucide-react';
import { useStudioStore } from '@/stores/useStudioStore';
import { StrategySummaryCard } from './StrategySummaryCard';
import { PerspectiveScriptGrid } from './PerspectiveScriptGrid';
import { Button } from '@/components/ui/button';

export const Step2Container: React.FC = () => {
  const { setCurrentStep } = useStudioStore();

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6 space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-zinc-100 flex items-center gap-2">
            <span>Step 2: 9 大商业视觉矩阵策划与审阅</span>
          </h2>
          <p className="text-xs text-zinc-400 mt-1">
            审阅并微调每一张主图与详情图的机位、打光与布景指导，支持就地自由编辑或 AI 灵感润色。
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setCurrentStep(1)}
            className="text-xs"
          >
            <ArrowLeft className="h-3.5 w-3.5 mr-1" />
            返回修改资产
          </Button>

          <Button
            variant="studio-accent"
            size="sm"
            onClick={() => setCurrentStep(3)}
            className="text-xs"
          >
            <span>进入 3x3 出图工坊</span>
            <ArrowRight className="h-3.5 w-3.5 ml-1" />
          </Button>
        </div>
      </div>

      {/* Top Strategy Summary */}
      <StrategySummaryCard />

      {/* 3x3 Scripting Grid */}
      <PerspectiveScriptGrid />
    </div>
  );
};
