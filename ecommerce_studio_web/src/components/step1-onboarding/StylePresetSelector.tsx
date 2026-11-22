"use client";

import React from 'react';
import { Sparkles, Check, Flame, SlidersHorizontal, Sun, Palette, Camera } from 'lucide-react';
import { useStudioStore } from '@/stores/useStudioStore';
import { STYLE_PRESETS } from '@/lib/constants';
import { StylePresetId } from '@/types/session';

export const StylePresetSelector: React.FC = () => {
  const { selectedStylePreset, setStylePreset } = useStudioStore();

  return (
    <div className="space-y-3 bg-white border border-slate-200 rounded-2xl p-5 shadow-card">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
        <div className="flex items-center gap-2">
          <div className="h-7 w-7 rounded-lg bg-gradient-to-br from-amber-500 to-amber-600 flex items-center justify-center text-white shadow-sm shadow-amber-500/25">
            <Flame className="h-4 w-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-bold text-slate-900 tracking-wide">
                爆款视觉流派引擎 (Style Preset Engine)
              </h3>
              <span className="text-[10px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full bg-amber-50 text-amber-700 border border-amber-200">
                9视角光学防漂移
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              单选锁定顶级商业摄影参数包（四维光学布光、空间机位与色彩规范），严防画面质感漂移。
            </p>
          </div>
        </div>

        <div className="flex items-center gap-1.5 text-xs text-slate-500">
          <SlidersHorizontal className="h-3.5 w-3.5 text-amber-500" />
          <span>当前激活：</span>
          <span className="font-semibold text-amber-700">
            {STYLE_PRESETS.find((p) => p.id === selectedStylePreset)?.name || '极简原研哉 (日系留白)'}
          </span>
        </div>
      </div>

      {/* 5-Card Responsive Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 pt-1">
        {STYLE_PRESETS.map((preset) => {
          const isSelected = selectedStylePreset === preset.id;
          return (
            <div
              key={preset.id}
              onClick={() => setStylePreset(preset.id as StylePresetId)}
              className={`group relative flex flex-col justify-between rounded-xl p-3.5 cursor-pointer transition-all duration-200 select-none border ${
                isSelected
                  ? 'border-amber-500 bg-amber-50/50 shadow-sm ring-1 ring-amber-500/30'
                  : 'border-slate-200 bg-slate-50/50 hover:border-amber-400/60 hover:bg-white hover:shadow-card-hover'
              }`}
            >
              {/* Active Selection Glow Dot & Checkmark */}
              <div className="flex items-start justify-between gap-1 mb-2">
                <span
                  className={`text-[10px] font-bold px-2 py-0.5 rounded-md tracking-wider uppercase transition-colors ${
                    isSelected
                      ? 'bg-amber-500 text-white shadow-xs font-bold'
                      : 'bg-slate-200/80 text-slate-700 group-hover:text-amber-800'
                  }`}
                >
                  {preset.badge || '官方流派'}
                </span>

                <div
                  className={`h-5 w-5 rounded-full flex items-center justify-center transition-all ${
                    isSelected
                      ? 'bg-amber-500 text-white shadow-xs'
                      : 'border border-slate-300 bg-white text-transparent group-hover:border-amber-400'
                  }`}
                >
                  <Check className={`h-3 w-3 stroke-[3] ${isSelected ? 'opacity-100' : 'opacity-0'}`} />
                </div>
              </div>

              {/* Title & Subtitle */}
              <div className="space-y-1 mb-2.5">
                <h4
                  className={`text-xs font-bold leading-snug transition-colors line-clamp-1 ${
                    isSelected ? 'text-amber-900' : 'text-slate-800 group-hover:text-slate-900'
                  }`}
                >
                  {preset.name}
                </h4>
                <p className="text-[10px] font-medium text-slate-500 line-clamp-1">
                  {preset.en_name}
                </p>
                <p className="text-[11px] text-slate-600 leading-relaxed line-clamp-2 mt-1">
                  {preset.tagline}
                </p>
              </div>

              {/* Optical Parameters Micro Preview */}
              <div className="pt-2 border-t border-slate-200 space-y-1 text-[10px] text-slate-500">
                <div className="flex items-center gap-1.5 truncate">
                  <Sun className="h-3 w-3 text-amber-500 shrink-0" />
                  <span className="truncate text-slate-600">{preset.lighting}</span>
                </div>
                <div className="flex items-center gap-1.5 truncate">
                  <Palette className="h-3 w-3 text-blue-600 shrink-0" />
                  <span className="truncate text-slate-600">{preset.color_tone}</span>
                </div>
                <div className="flex items-center gap-1.5 truncate">
                  <Camera className="h-3 w-3 text-emerald-600 shrink-0" />
                  <span className="truncate text-slate-600">{preset.camera}</span>
                </div>
              </div>

              {/* Anti-drift Quality Lock Indicator */}
              {isSelected && (
                <div className="mt-2.5 pt-2 border-t border-amber-200 flex items-center gap-1 text-[10px] text-amber-800 font-medium">
                  <Sparkles className="h-3 w-3 text-amber-600 shrink-0" />
                  <span className="truncate">已载入防漂移质量锁</span>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
