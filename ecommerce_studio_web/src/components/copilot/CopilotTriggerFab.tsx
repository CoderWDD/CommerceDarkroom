"use client";

import React from 'react';
import { Sparkles } from 'lucide-react';
import { useCopilotStore } from '@/stores/useCopilotStore';

export const CopilotTriggerFab: React.FC = () => {
  const { toggleOpen, unreadCount } = useCopilotStore();

  return (
    <aside aria-label="Creative Advisor" className="fixed bottom-20 right-6 z-30">
      <button
        type="button"
        onClick={toggleOpen}
        className="group relative flex items-center gap-2 px-3.5 py-2.5 rounded-full bg-zinc-900/90 text-zinc-100 border border-white/10 hover:border-indigo-500/60 shadow-2xl backdrop-blur-md hover:shadow-indigo-500/20 transition-all hover:scale-105 active:scale-95"
      >
        <div className="flex h-5 w-5 items-center justify-center rounded-full bg-gradient-to-br from-indigo-500 to-sky-400 text-white shadow-sm">
          <Sparkles className="h-3 w-3" />
        </div>
        <span className="text-xs font-semibold tracking-tight text-zinc-200 group-hover:text-white">
          首席视觉顾问
        </span>

        {unreadCount > 0 && (
          <span className="flex h-4 w-4 items-center justify-center rounded-full bg-rose-500 text-[10px] font-bold text-white shadow">
            {unreadCount}
          </span>
        )}
      </button>
    </aside>
  );
};
