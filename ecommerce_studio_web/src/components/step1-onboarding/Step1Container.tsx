"use client";

import React, { useState } from 'react';
import { useStudioStore } from '@/stores/useStudioStore';
import { CommercialDossierForm } from './CommercialDossierForm';
import { AssetUploadDropzone } from './AssetUploadDropzone';
import { studioApi } from '@/lib/api-client';

export const Step1Container: React.FC = () => {
  const { currentSession, setSession, setCurrentStep } = useStudioStore();
  const [isPlanning, setIsPlanning] = useState(false);

  const handleStartPlanning = async () => {
    if (!currentSession) return;
    setIsPlanning(true);

    try {
      const planRes = await studioApi.planMatrix({
        session_id: currentSession.session_id,
        product_info: currentSession.product_info,
      });

      if (planRes) {
        setSession(planRes);
      }
      setCurrentStep(2);
    } catch (e) {
      console.error('Plan matrix generation error:', e);
      // Fallback local plan if backend is still generating
      const { strategy_summary } = currentSession;
      if (!strategy_summary) {
        currentSession.strategy_summary = {
          tone: '现代极简冷峻精工，商务科技美学',
          usp: '轻触知温，从容开喝；真空气密倒置不渗水',
          color_palette: ['#09090b', '#38bdf8', '#71717a', '#ffffff'],
          overview_text: '依据实物特征解构9大商业镜头语言，按“吸引关注—建立信任—打消疑虑—促成下单”转化动线排布。',
        };
      }
      setCurrentStep(2);
    } finally {
      setIsPlanning(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6 space-y-6">
      <div className="flex flex-col gap-1">
        <h2 className="text-xl font-bold tracking-tight text-zinc-100">
          Step 1: 商品商业资产与特征录入
        </h2>
        <p className="text-xs text-zinc-400">
          锁定核心卖点、客群痛点与实物基准照片，多智能体将据此生成全套工业级摄影指令。
        </p>
      </div>

      {/* 60 / 40 Split Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
        <div className="lg:col-span-7">
          <CommercialDossierForm
            onStartPlanning={handleStartPlanning}
            isPlanning={isPlanning}
          />
        </div>

        <div className="lg:col-span-5">
          <AssetUploadDropzone />
        </div>
      </div>
    </div>
  );
};
