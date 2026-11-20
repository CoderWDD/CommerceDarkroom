"use client";

import React from 'react';
import { Check, Sparkles } from 'lucide-react';
import { useStudioStore } from '@/stores/useStudioStore';
import { cn } from '@/lib/utils';

const STEPS = [
  { step: 1, label: '资产与特征录入', tag: 'Onboarding' },
  { step: 2, label: '9大矩阵策划', tag: 'Scripting' },
  { step: 3, label: '商业出图工坊', tag: 'Studio Bench' },
  { step: 4, label: '全套交付与长图', tag: 'Handoff' },
] as const;

export const StepperHeader: React.FC = () => {
  const { currentStep, setCurrentStep } = useStudioStore();

  return (
    <nav className="w-full bg-zinc-950/60 border-b border-white/[0.06] py-2 px-4 flex items-center justify-center">
      <ol className="flex items-center gap-1 sm:gap-4 md:gap-8 overflow-x-auto py-1 scrollbar-none">
        {STEPS.map((item, index) => {
          const isCompleted = item.step < currentStep;
          const isActive = item.step === currentStep;
          const isUpcoming = item.step > currentStep;

          return (
            <React.Fragment key={item.step}>
              {index > 0 && (
                <div
                  className={cn(
                    'h-[1px] w-4 sm:w-8 md:w-12 transition-colors duration-300',
                    item.step <= currentStep ? 'bg-sky-500/50' : 'bg-zinc-800'
                  )}
                />
              )}

              <li className="flex items-center">
                <button
                  type="button"
                  onClick={() => {
                    // Completed steps or current step are directly clickable
                    if (isCompleted || isActive) {
                      setCurrentStep(item.step as 1 | 2 | 3 | 4);
                    }
                  }}
                  disabled={isUpcoming}
                  className={cn(
                    'group flex items-center gap-2 rounded-full px-2.5 py-1 text-xs transition-all select-none',
                    isActive &&
                      'bg-sky-500/15 border border-sky-500/40 text-white shadow-sm shadow-sky-500/20 font-medium',
                    isCompleted &&
                      'bg-zinc-900/80 border border-emerald-500/30 text-zinc-200 hover:border-emerald-500/60 cursor-pointer',
                    isUpcoming && 'opacity-40 text-zinc-500 cursor-not-allowed border border-transparent'
                  )}
                >
                  <span
                    className={cn(
                      'flex h-5 w-5 items-center justify-center rounded-full text-[10px] font-mono transition-colors',
                      isActive && 'bg-sky-500 text-zinc-950 font-bold',
                      isCompleted && 'bg-emerald-500/20 text-emerald-400',
                      isUpcoming && 'border border-zinc-700 text-zinc-600'
                    )}
                  >
                    {isCompleted ? (
                      <Check className="h-3 w-3" />
                    ) : isActive ? (
                      <Sparkles className="h-3 w-3" />
                    ) : (
                      item.step
                    )}
                  </span>

                  <span className="truncate whitespace-nowrap">
                    {item.label}
                  </span>
                </button>
              </li>
            </React.Fragment>
          );
        })}
      </ol>
    </nav>
  );
};
