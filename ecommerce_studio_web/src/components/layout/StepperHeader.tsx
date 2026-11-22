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
    <nav className="w-full bg-white/80 backdrop-blur-md border-b border-slate-200/80 py-2 px-4 flex items-center justify-center">
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
                    'h-[2px] w-4 sm:w-8 md:w-12 transition-colors duration-300',
                    item.step <= currentStep ? 'bg-blue-600' : 'bg-slate-200'
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
                      'bg-blue-50 border border-blue-600 text-blue-700 shadow-xs font-semibold',
                    isCompleted &&
                      'bg-emerald-50 border border-emerald-300 text-emerald-800 hover:border-emerald-400 cursor-pointer',
                    isUpcoming && 'opacity-40 text-slate-400 cursor-not-allowed border border-transparent'
                  )}
                >
                  <span
                    className={cn(
                      'flex h-5 w-5 items-center justify-center rounded-full text-[10px] font-mono transition-colors',
                      isActive && 'bg-blue-600 text-white font-bold',
                      isCompleted && 'bg-emerald-600 text-white',
                      isUpcoming && 'border border-slate-300 text-slate-400'
                    )}
                  >
                    {isCompleted ? (
                      <Check className="h-3 w-3 stroke-[2.5]" />
                    ) : isActive ? (
                      <Sparkles className="h-3 w-3" />
                    ) : (
                      item.step
                    )}
                  </span>

                  <span className="truncate whitespace-nowrap font-medium">
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
