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
    color_palette: ['#09090b', '#38bdf8', '#52525b', '#f4f4f5'],
    overview_text: '九张图按“认识产品—看见数显—感受材质—回应顾虑—融入日常”黄金买家决策动线展开，严格依据实物参考图还原杯身轮廓与金属反光。',
  };

  return (
    <div className="bg-zinc-900/60 backdrop-blur-md border border-white/[0.08] rounded-xl p-4 shadow-xl text-zinc-200">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-sky-500/20 text-sky-400 border border-sky-500/30">
            <Award className="h-4 w-4" />
          </div>
          <div>
            <span className="text-xs font-semibold uppercase tracking-wider text-sky-400">
              视觉总监全案策划策略 (Creative Strategy Overview)
            </span>
            <p className="text-xs text-zinc-400 mt-0.5 font-medium">
              基调: <span className="text-zinc-200">{strategy.tone}</span>
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Palette Preview */}
          <div className="hidden sm:flex items-center gap-1 bg-zinc-950/60 px-2 py-1 rounded-md border border-white/5">
            <Palette className="h-3 w-3 text-zinc-500 mr-1" />
            {strategy.color_palette?.map((color, idx) => (
              <span
                key={idx}
                className="h-3.5 w-3.5 rounded-full border border-white/20 inline-block"
                style={{ backgroundColor: color }}
                title={color}
              />
            ))}
          </div>

          <button
            type="button"
            onClick={() => setIsOpen(!isOpen)}
            className="p-1 rounded hover:bg-white/5 text-zinc-400 hover:text-white"
          >
            {isOpen ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          </button>
        </div>
      </div>

      {isOpen && (
        <div className="mt-3 pt-3 border-t border-white/5 grid grid-cols-1 md:grid-cols-2 gap-4 text-xs leading-relaxed">
          <div className="space-y-1">
            <span className="text-zinc-400 font-medium flex items-center gap-1.5">
              <Target className="h-3 w-3 text-emerald-400" />
              第一杀手级卖点 (USP):
            </span>
            <p className="text-zinc-200 bg-zinc-950/40 p-2 rounded-lg border border-white/5">
              {strategy.usp}
            </p>
          </div>

          <div className="space-y-1">
            <span className="text-zinc-400 font-medium">视觉故事线与光影逻辑:</span>
            <p className="text-zinc-400 bg-zinc-950/40 p-2 rounded-lg border border-white/5 line-clamp-3">
              {strategy.overview_text}
            </p>
          </div>
        </div>
      )}
    </div>
  );
};
