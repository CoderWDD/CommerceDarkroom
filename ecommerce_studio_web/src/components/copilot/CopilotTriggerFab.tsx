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
        className="group relative flex items-center gap-2 px-3.5 py-2.5 rounded-full bg-white text-slate-800 border border-slate-200 hover:border-indigo-400 shadow-card hover:shadow-card-hover transition-all hover:scale-105 active:scale-95"
      >
        <div className="flex h-5 w-5 items-center justify-center rounded-full bg-gradient-to-br from-indigo-600 to-blue-600 text-white shadow-xs">
          <Sparkles className="h-3 w-3" />
        </div>
        <span className="text-xs font-semibold tracking-tight text-slate-800 group-hover:text-indigo-600 transition-colors">
          首席视觉顾问
        </span>

        {unreadCount > 0 && (
          <span className="flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-[10px] font-bold text-white shadow">
            {unreadCount}
          </span>
        )}
      </button>
    </aside>
  );
};
