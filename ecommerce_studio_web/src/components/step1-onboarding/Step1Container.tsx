"use client";

import React, { useState } from 'react';
import { ArrowRight, Zap, Wand2 } from 'lucide-react';
import { useStudioStore } from '@/stores/useStudioStore';
import { CommercialDossierForm } from './CommercialDossierForm';
import { AssetUploadDropzone } from './AssetUploadDropzone';
import { StylePresetSelector } from './StylePresetSelector';
import { Button } from '@/components/ui/button';
import { studioApi } from '@/lib/api-client';

export const Step1Container: React.FC = () => {
  const { currentSession, selectedStylePreset, setSession, setCurrentStep } = useStudioStore();
  const [isPlanning, setIsPlanning] = useState(false);

  const handleStartPlanning = async (directToStep3: boolean = false) => {
    if (!currentSession) return;

    const styleToUse = selectedStylePreset || currentSession.style_preset || 'minimalist_muji';
    currentSession.style_preset = styleToUse;

    if (!directToStep3) {
      // 快速进入 Step 2，在 Step 2 显式触发基于资产特征的 AI 9 视角提示词生成
      setCurrentStep(2);
      return;
    }

    setIsPlanning(true);
    try {
      const planRes = await studioApi.planMatrix({
        session_id: currentSession.session_id,
        product_info: currentSession.product_info,
        style_preset: styleToUse,
      });

      if (planRes) {
        setSession(planRes);
      }
      setCurrentStep(3);
    } catch (e) {
      console.error('Plan matrix generation error:', e);
      setCurrentStep(3);
    } finally {
      setIsPlanning(false);
    }
  };

  const hasProductName = Boolean(currentSession?.product_info?.name?.trim());

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6 space-y-6">
      {/* Step Header */}
      <div className="flex flex-col gap-1">
        <h2 className="text-xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
          <span>Step 1: 随手拍商业资产逆向建档与流派选择</span>
        </h2>
        <p className="text-xs text-slate-500">
          通过多模态大脑（Gemini 2.0 / GPT-4o Vision）从随手拍实物照片中逆向提炼商业档案，并锁定顶级商业摄影爆款流派。
        </p>
      </div>

      {/* Style Preset Selector */}
      <StylePresetSelector />

      {/* 60 / 40 Split Grid: Commercial Dossier & Dropzone */}
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

      {/* Bottom Full-Width Express Launch Banner (直通出图工坊极速通道) */}
      <div className="p-5 rounded-2xl bg-gradient-to-r from-blue-50/80 via-white to-amber-50/60 border border-blue-200/80 flex flex-col md:flex-row md:items-center md:justify-between gap-4 shadow-card">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="text-sm font-bold text-slate-900">🚀 极速通关直通车 (Fast-Track Delivery)</span>
            <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-blue-100 text-blue-700 border border-blue-200">
              免手写提示词 · 3秒直达工坊
            </span>
          </div>
          <p className="text-xs text-slate-600 max-w-2xl">
            AI 提示词矩阵编译器将依据所选流派全自动完成 9 大机位焦段、布光比与防漂移语法编译。您完全无需在 Step 2 手动敲键盘改词，可直接直通 Step 3 开始出图！
          </p>
        </div>

        <div className="flex items-center gap-3 shrink-0 flex-wrap">
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleStartPlanning(false)}
            disabled={!hasProductName}
            className="text-xs text-slate-700 hover:text-slate-900 border-slate-200 bg-white gap-1"
          >
            <span>👉 下一步：进入 9 大矩阵策划 (Step 2) →</span>
          </Button>

          <Button
            variant="studio-accent"
            size="sm"
            onClick={() => handleStartPlanning(true)}
            disabled={isPlanning || !hasProductName}
            className="gap-2 text-xs font-bold px-4 h-9 shadow-md shadow-amber-500/20"
          >
            {isPlanning ? (
              <>
                <Wand2 className="h-4 w-4 animate-spin text-white" />
                <span>AI 视觉导演正在全案推演 9 大镜头...</span>
              </>
            ) : (
              <>
                <Zap className="h-4 w-4 fill-current text-white" />
                <span>🚀 一键全案推演并直通 3x3 出图工坊 (极速出图)</span>
                <ArrowRight className="h-3.5 w-3.5 ml-0.5" />
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
};
