"use client";

import React, { useEffect, useState } from 'react';
import { useStudioStore } from '@/stores/useStudioStore';
import { StudioTopBar } from '@/components/layout/StudioTopBar';
import { StepperHeader } from '@/components/layout/StepperHeader';
import { StickyActionBar } from '@/components/layout/StickyActionBar';
import { Step1Container } from '@/components/step1-onboarding/Step1Container';
import { Step2Container } from '@/components/step2-matrix/Step2Container';
import { Step3Container } from '@/components/step3-studio/Step3Container';
import { Step4Container } from '@/components/step4-handoff/Step4Container';
import { CopilotDrawer } from '@/components/copilot/CopilotDrawer';
import { CopilotTriggerFab } from '@/components/copilot/CopilotTriggerFab';

export default function StudioPage() {
  const { currentSession, currentStep, initDefaultSession, fetchSessionList } =
    useStudioStore();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    fetchSessionList();
    if (!currentSession) {
      initDefaultSession();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (!mounted) {
    return (
      <div className="min-h-screen bg-zinc-950 flex items-center justify-center">
        <div className="flex flex-col items-center gap-3 text-zinc-400">
          <div className="h-6 w-6 rounded-full border-2 border-sky-500 border-t-transparent animate-spin" />
          <span className="text-xs font-mono">正在加载商业暗房摄影工作台...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 flex flex-col pb-24 relative overflow-x-hidden">
      {/* Top Bar with Brand & Session Switcher */}
      <StudioTopBar />

      {/* 4-Step Stepper Header */}
      <StepperHeader />

      {/* Main Dynamic Step Workspace */}
      <main className="flex-1">
        {currentStep === 1 && <Step1Container />}
        {currentStep === 2 && <Step2Container />}
        {currentStep === 3 && <Step3Container />}
        {currentStep === 4 && <Step4Container />}
      </main>

      {/* Persistent Sticky Bottom Bar */}
      <StickyActionBar />

      {/* Floating Copilot Trigger & Drawer */}
      <CopilotTriggerFab />
      <CopilotDrawer />
    </div>
  );
}
