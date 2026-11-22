"use client";

import React, { useState } from 'react';
import { ChevronDown, ChevronUp, Palette, Target, Award } from 'lucide-react';
import { useStudioStore } from '@/stores/useStudioStore';

export const StrategySummaryCard: React.FC = () => {
  const { currentSession } = useStudioStore();
  const [isOpen, setIsOpen] = useState(true);

  const strategy = currentSession?.strategy_summary || {
    tone: '商业极简、硬核精工与现代科技生活美学',
    usp: '触控看温度，通勤喝热饮更从容；严密防漏打消携带疑虑',
    color_palette: ['#0F172A', '#2563EB', '#64748B', '#FFFFFF'],
    overview_text: '九张图按“认识产品—看见数显—感受材质—回应顾虑—融入日常”黄金买家决策动线展开，严格依据实物参考图还原杯身轮廓与金属反光。',
  };

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-card text-slate-800">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-blue-50 text-blue-600 border border-blue-200">
            <Award className="h-4 w-4" />
          </div>
          <div>
            <span className="text-xs font-semibold uppercase tracking-wider text-blue-600">
              视觉总监全案策划策略 (Creative Strategy Overview)
            </span>
            <p className="text-xs text-slate-500 mt-0.5 font-medium">
              基调: <span className="text-slate-900 font-semibold">{strategy.tone}</span>
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Palette Preview */}
          <div className="hidden sm:flex items-center gap-1 bg-slate-50 px-2 py-1 rounded-md border border-slate-200">
            <Palette className="h-3 w-3 text-slate-400 mr-1" />
            {strategy.color_palette?.map((color, idx) => (
              <span
                key={idx}
                className="h-3.5 w-3.5 rounded-full border border-slate-300 inline-block shadow-xs"
                style={{ backgroundColor: color }}
                title={color}
              />
            ))}
          </div>

          <button
            type="button"
            onClick={() => setIsOpen(!isOpen)}
            className="p-1 rounded hover:bg-slate-100 text-slate-400 hover:text-slate-700 transition-colors"
          >
            {isOpen ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          </button>
        </div>
      </div>

      {isOpen && (
        <div className="mt-3 pt-3 border-t border-slate-200 grid grid-cols-1 md:grid-cols-2 gap-4 text-xs leading-relaxed">
          <div className="space-y-1">
            <span className="text-slate-600 font-medium flex items-center gap-1.5">
              <Target className="h-3 w-3 text-emerald-600" />
              第一杀手级卖点 (USP):
            </span>
            <p className="text-slate-800 bg-slate-50 p-2.5 rounded-lg border border-slate-200 font-medium">
              {strategy.usp}
            </p>
          </div>

          <div className="space-y-1">
            <span className="text-slate-600 font-medium">视觉故事线与光影逻辑:</span>
            <p className="text-slate-600 bg-slate-50 p-2.5 rounded-lg border border-slate-200 line-clamp-3">
              {strategy.overview_text}
            </p>
          </div>
        </div>
      )}
    </div>
  );
};
