"use client";

import React, { useRef } from 'react';
import { Smartphone, ChevronRight } from 'lucide-react';
import { useStudioStore } from '@/stores/useStudioStore';
import { formatAssetUrl } from '@/lib/constants';

export const MobileDetailPreviewSheet: React.FC = () => {
  const { currentSession, selectedPreviewVersions } = useStudioStore();
  const perspectives = currentSession?.perspectives || [];
  const containerRef = useRef<HTMLDivElement>(null);

  const scrollToSlot = (id: string) => {
    const el = document.getElementById(`preview-slot-${id}`);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  };

  return (
    <div className="flex flex-col xl:flex-row items-center xl:items-start justify-center gap-8 py-2">
      {/* 750px Simulated iPhone Frame (Modern Silver Studio Device) */}
      <div className="relative w-full max-w-[420px] sm:max-w-[480px] md:max-w-[540px] rounded-[44px] p-3.5 bg-gradient-to-b from-slate-200 via-slate-100 to-slate-300 shadow-xl border border-slate-300">
        {/* Dynamic Island Decor */}
        <div className="absolute top-5 left-1/2 -translate-x-1/2 h-5 w-24 rounded-full bg-slate-800 z-30 flex items-center justify-end px-2">
          <div className="h-2 w-2 rounded-full bg-slate-900" />
        </div>

        {/* Scrollable Screen Canvas */}
        <div
          ref={containerRef}
          className="relative w-full h-[680px] rounded-[36px] overflow-y-auto bg-slate-50 scrollbar-none border border-slate-300 pt-8"
        >
          {/* Seamless Vertical Image Stack */}
          {perspectives.map((p, index) => {
            const selectedVersionId =
              selectedPreviewVersions[p.id] ||
              p.active_version_id ||
              (p.versions.length > 0 ? p.versions[p.versions.length - 1].version_id : 'v1');

            const activeVersion =
              p.versions.find((v) => String(v.version_id) === String(selectedVersionId)) ||
              p.versions.find((v) => String(v.version_id) === String(p.active_version_id));

            const imageUrl = formatAssetUrl(activeVersion?.image_url || p.image_url);

            return (
              <div
                key={p.id}
                id={`preview-slot-${p.id}`}
                className="relative w-full border-b border-slate-200 group bg-white"
              >
                {imageUrl ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={imageUrl}
                    alt={p.name}
                    className="w-full h-auto block select-none"
                  />
                ) : (
                  <div className="w-full aspect-square bg-slate-100 flex items-center justify-center text-xs text-slate-400">
                    {p.name} (待拍摄)
                  </div>
                )}

                {/* Floating Micro Badge on Card */}
                <div className="absolute bottom-2 left-2 bg-slate-900/70 backdrop-blur-md px-2 py-0.5 rounded text-[10px] text-white font-mono opacity-85 group-hover:opacity-100 transition-opacity shadow-xs">
                  0{index + 1} · {p.name}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Side Outline Navigator */}
      <div className="w-full xl:w-72 space-y-2 bg-white border border-slate-200 rounded-2xl p-4 shadow-card">
        <div className="flex items-center gap-2 pb-2 border-b border-slate-100">
          <Smartphone className="h-4 w-4 text-blue-600" />
          <span className="text-xs font-semibold text-slate-900">
            电商黄金买家动线导航
          </span>
        </div>

        <div className="space-y-1.5 pt-1">
          {perspectives.map((p, idx) => (
            <button
              key={p.id}
              type="button"
              onClick={() => scrollToSlot(p.id)}
              className="w-full text-left flex items-center justify-between p-2 rounded-lg hover:bg-slate-50 transition-all text-xs group"
            >
              <div className="flex items-center gap-2 truncate pr-2">
                <span className="font-mono text-[10px] text-slate-400 group-hover:text-blue-600 font-semibold">
                  0{idx + 1}
                </span>
                <span className="text-slate-700 group-hover:text-slate-900 truncate font-medium">
                  {p.name}
                </span>
              </div>
              <ChevronRight className="h-3.5 w-3.5 text-slate-400 group-hover:text-slate-600 shrink-0" />
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};
