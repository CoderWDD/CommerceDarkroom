"use client";

import React from 'react';
import { useStudioStore } from '@/stores/useStudioStore';
import { ScriptCardItem } from './ScriptCardItem';
import { Layers, Sparkles } from 'lucide-react';

export const PerspectiveScriptGrid: React.FC = () => {
  const { currentSession } = useStudioStore();
  const perspectives = currentSession?.perspectives || [];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <Layers className="h-4 w-4 text-blue-600" />
          <h3 className="text-sm font-semibold text-slate-900">
            9 大黄金商业视觉策略卡片阵列 (Visual Strategy Cards)
          </h3>
          <span className="text-[11px] font-mono px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 border border-slate-200">
            共 {perspectives.length} 张策略卡
          </span>
        </div>
        <div className="flex items-center gap-1.5 text-xs text-slate-500">
          <Sparkles className="h-3.5 w-3.5 text-amber-500" />
          <span>点击胶囊快捷微调 · 底层摄影参数已全自动装配锁定</span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {perspectives.map((perspective, index) => (
          <ScriptCardItem
            key={perspective.id}
            perspective={perspective}
            index={index}
          />
        ))}
      </div>
    </div>
  );
};
