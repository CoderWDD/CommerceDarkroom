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
      {/* 750px Simulated iPhone Frame */}
      <div className="relative w-full max-w-[420px] sm:max-w-[480px] md:max-w-[540px] rounded-[44px] p-3.5 bg-gradient-to-b from-zinc-700 via-zinc-800 to-zinc-900 shadow-2xl shadow-black/80 border border-white/10">
        {/* Dynamic Island Decor */}
        <div className="absolute top-5 left-1/2 -translate-x-1/2 h-5 w-24 rounded-full bg-black z-30 flex items-center justify-end px-2">
          <div className="h-2 w-2 rounded-full bg-zinc-800" />
        </div>

        {/* Scrollable Screen Canvas */}
        <div
          ref={containerRef}
          className="relative w-full h-[680px] rounded-[36px] overflow-y-auto bg-zinc-950 scrollbar-none border border-black/40 pt-8"
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
                className="relative w-full border-b border-black/20 group"
              >
                {imageUrl ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={imageUrl}
                    alt={p.name}
                    className="w-full h-auto block select-none"
                  />
                ) : (
                  <div className="w-full aspect-square bg-zinc-900/80 flex items-center justify-center text-xs text-zinc-500">
                    {p.name} (待拍摄)
                  </div>
                )}

                {/* Floating Micro Badge on Card */}
                <div className="absolute bottom-2 left-2 bg-black/60 backdrop-blur-md px-2 py-0.5 rounded text-[10px] text-zinc-300 font-mono opacity-80 group-hover:opacity-100 transition-opacity">
                  0{index + 1} · {p.name}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Side Outline Navigator */}
      <div className="w-full xl:w-72 space-y-2 bg-zinc-900/60 backdrop-blur-md border border-white/[0.08] rounded-2xl p-4 shadow-xl">
        <div className="flex items-center gap-2 pb-2 border-b border-white/5">
          <Smartphone className="h-4 w-4 text-sky-400" />
          <span className="text-xs font-semibold text-zinc-100">
            电商黄金买家动线导航
          </span>
        </div>

        <div className="space-y-1.5 pt-1">
          {perspectives.map((p, idx) => (
            <button
              key={p.id}
              type="button"
              onClick={() => scrollToSlot(p.id)}
              className="w-full text-left flex items-center justify-between p-2 rounded-lg hover:bg-white/5 transition-all text-xs group"
            >
              <div className="flex items-center gap-2 truncate pr-2">
                <span className="font-mono text-[10px] text-zinc-500 group-hover:text-sky-400">
                  0{idx + 1}
                </span>
                <span className="text-zinc-300 group-hover:text-white truncate font-medium">
                  {p.name}
                </span>
              </div>
              <ChevronRight className="h-3.5 w-3.5 text-zinc-600 group-hover:text-zinc-300 shrink-0" />
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};
